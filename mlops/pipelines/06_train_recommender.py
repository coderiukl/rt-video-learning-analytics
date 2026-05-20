"""Hybrid course recommender: ALS on implicit watch signal + content TF-IDF.

Reads the latest raw snapshot for video_progress + courses. Saves a self-
contained bundle (ALS model, index maps, TF-IDF vectorizer, content similarity
matrix) so the serving layer can load it without rebuilding indexes.

The bundle is logged to MLflow as a pyfunc-style artifact and saved locally
to models/recommender/hybrid.pkl. We use joblib for the local artifact because
the implicit ALS object pickles cleanly.
"""
from __future__ import annotations

import json
import os
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp

import mlflow
from mlflow.tracking import MlflowClient

from implicit.als import AlternatingLeastSquares
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Bootstrap Django so we share the same model-name conventions if needed later.
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django  # noqa: E402

django.setup()

CONFIG_PATH = "mlops/config/mlops.yaml"
RAW_ROOT = "data/raw"
MODEL_DIR = "models/recommender"
METRICS_DIR = "metrics"
MODEL_NAME = "recommender"
PROD_ALIAS = "production"
ARTIFACT_NAME = "hybrid.pkl"


def latest_snapshot_dir() -> str:
    snapshots = sorted(
        path
        for path in os.listdir(RAW_ROOT)
        if os.path.isdir(os.path.join(RAW_ROOT, path))
    )
    if not snapshots:
        raise RuntimeError("No raw snapshots in data/raw/.")
    return os.path.join(RAW_ROOT, snapshots[-1])


def alias_latest(client: MlflowClient) -> None:
    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    if not versions:
        return
    latest = max(versions, key=lambda v: int(v.version)).version
    client.set_registered_model_alias(MODEL_NAME, PROD_ALIAS, latest)
    print(f"Aliased {MODEL_NAME} v{latest} -> @{PROD_ALIAS}")


def train() -> None:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        full_cfg = yaml.safe_load(fh)
    cfg = full_cfg["recommender"]

    mlflow.set_tracking_uri(full_cfg["mlflow"]["tracking_uri"])
    mlflow.set_experiment(full_cfg["mlflow"]["experiment_name"])

    snap = latest_snapshot_dir()
    progress = pd.read_parquet(f"{snap}/video_progress.parquet")
    courses = pd.read_parquet(f"{snap}/courses.parquet")

    if "duration_seconds" not in progress.columns or len(progress) == 0:
        raise RuntimeError(
            f"Empty or malformed progress data at {snap}/video_progress.parquet"
        )

    progress = progress.copy()
    progress["duration_seconds"] = progress["duration_seconds"].fillna(0).clip(lower=1)
    progress["score"] = progress["watched_seconds"].fillna(0) / progress["duration_seconds"]
    min_signal = float(cfg.get("min_progress_signal", 0.1))
    progress = progress[progress["score"] >= min_signal]

    if progress.empty:
        raise RuntimeError(
            f"No progress rows pass min_progress_signal={min_signal}; cannot train."
        )

    u_idx = {u: i for i, u in enumerate(progress["student_id"].unique())}
    i_idx = {v: i for i, v in enumerate(progress["video_id"].unique())}

    rows = progress["student_id"].map(u_idx).to_numpy()
    cols = progress["video_id"].map(i_idx).to_numpy()
    confidence = 1.0 + float(cfg["alpha"]) * progress["score"].to_numpy()
    user_items = sp.csr_matrix(
        (confidence, (rows, cols)), shape=(len(u_idx), len(i_idx))
    )

    with mlflow.start_run(run_name="recommender_hybrid"):
        als = AlternatingLeastSquares(
            factors=int(cfg["factors"]),
            regularization=float(cfg["regularization"]),
            iterations=int(cfg["iterations"]),
            random_state=42,
        )
        als.fit(user_items)

        # Content side
        courses = courses.copy()
        for col in ("language", "level"):
            if col not in courses.columns:
                courses[col] = ""
        courses["text"] = (
            courses["language"].fillna("").astype(str)
            + " "
            + courses["level"].fillna("").astype(str)
        )
        non_empty = courses["text"].str.strip().astype(bool).any()
        if non_empty:
            tfidf = TfidfVectorizer().fit(courses["text"])
            content_mat = tfidf.transform(courses["text"])
            content_sim = cosine_similarity(content_mat)
        else:
            tfidf = None
            content_sim = np.zeros((len(courses), len(courses)))

        bundle = {
            "als": als,
            "u_idx": u_idx,
            "i_idx": {str(k): v for k, v in i_idx.items()},
            "tfidf": tfidf,
            "content_sim": content_sim,
            "course_ids": courses["course_id"].astype(str).tolist(),
            "content_weight": float(cfg.get("content_weight", 0.3)),
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }

        os.makedirs(MODEL_DIR, exist_ok=True)
        os.makedirs(METRICS_DIR, exist_ok=True)
        local_path = os.path.join(MODEL_DIR, ARTIFACT_NAME)
        joblib.dump(bundle, local_path)

        mlflow.log_params(
            {
                "factors": cfg["factors"],
                "regularization": cfg["regularization"],
                "iterations": cfg["iterations"],
                "alpha": cfg["alpha"],
                "min_progress_signal": min_signal,
                "content_weight": cfg.get("content_weight", 0.3),
            }
        )
        mlflow.log_metrics(
            {
                "n_users": float(len(u_idx)),
                "n_items": float(len(i_idx)),
                "n_interactions": float(len(progress)),
                "n_courses": float(len(courses)),
                "sparsity": float(
                    1.0 - len(progress) / max(len(u_idx) * len(i_idx), 1)
                ),
            }
        )
        mlflow.log_artifact(local_path, artifact_path="bundle")

        # Register via Model Registry by logging a pyfunc wrapper.
        class _HybridWrapper(mlflow.pyfunc.PythonModel):
            def load_context(self, context):
                self.bundle = joblib.load(context.artifacts["bundle"])

            def predict(self, context, model_input, params=None):
                # Minimal contract: accepts {"user_ids": [...], "n": int}.
                return None

        mlflow.pyfunc.log_model(
            name="model",
            python_model=_HybridWrapper(),
            artifacts={"bundle": local_path},
            registered_model_name=MODEL_NAME,
        )

        with open(f"{METRICS_DIR}/recommender_metrics.json", "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "n_users": len(u_idx),
                    "n_items": len(i_idx),
                    "n_interactions": int(len(progress)),
                    "n_courses": int(len(courses)),
                },
                fh,
                indent=2,
            )

    alias_latest(MlflowClient(tracking_uri=full_cfg["mlflow"]["tracking_uri"]))
    print(
        f"Recommender trained: {len(u_idx)} users, {len(i_idx)} items, "
        f"{len(progress)} interactions."
    )


if __name__ == "__main__":
    train()
