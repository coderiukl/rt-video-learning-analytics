"""Train the learning-style clustering model.

Auto-selects k in mlops.yaml::learning_style.k_range using silhouette score
(or Davies-Bouldin as configured). Logs profile + scores to MLflow and aliases
the best version as @production.
"""
from __future__ import annotations

import json
import os
import sys
import yaml
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Bootstrap Django so the feature contract stays single-source-of-truth.
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django  # noqa: E402

django.setup()

CONFIG_PATH = "mlops/config/mlops.yaml"
FEATURES_PATH = "data/processed/dropout_features.parquet"
MODEL_DIR = "models/style"
METRICS_DIR = "metrics"
REPORTS_DIR = "reports"
MODEL_NAME = "learning_style"
PROD_ALIAS = "production"

STYLE_FEATURES = [
    "avg_playback_rate",
    "skip_fwd_ratio",
    "skip_bwd_ratio",
    "note_ratio",
    "avg_session_active_minutes",
    "hidden_tab_ratio",
]


def pick_k(X: np.ndarray, k_min: int, k_max: int, method: str, random_state: int):
    best_k, best_score = k_min, -np.inf
    scores: dict[int, float] = {}
    k_max = min(k_max, max(2, len(X) - 1))
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=random_state).fit(X)
        labels = km.labels_
        if len(set(labels)) < 2:
            continue
        if method == "silhouette":
            score = silhouette_score(X, labels)
        elif method == "davies_bouldin":
            score = -davies_bouldin_score(X, labels)
        else:
            raise ValueError(f"Unknown auto_select method: {method}")
        scores[k] = float(score)
        if score > best_score:
            best_k, best_score = k, score
    return best_k, scores


def alias_latest(client: MlflowClient) -> None:
    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    if not versions:
        return
    latest = max(versions, key=lambda v: int(v.version)).version
    client.set_registered_model_alias(MODEL_NAME, PROD_ALIAS, latest)
    print(f"Aliased {MODEL_NAME} v{latest} -> @{PROD_ALIAS}")


def train() -> None:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    lcfg = cfg["learning_style"]
    random_state = int(cfg.get("dropout", {}).get("random_state", 42))

    mlflow.set_tracking_uri(cfg["mlflow"]["tracking_uri"])
    mlflow.set_experiment(cfg["mlflow"]["experiment_name"])

    df = pd.read_parquet(FEATURES_PATH)
    df = df[df[STYLE_FEATURES].notna().all(axis=1)]
    if len(df) < 4:
        raise RuntimeError(
            f"Need >=4 rows for learning-style clustering, got {len(df)}."
        )

    X_raw = df[STYLE_FEATURES].astype(float)
    scaler = StandardScaler().fit(X_raw)
    X = scaler.transform(X_raw)

    k_min, k_max = lcfg["k_range"]
    method = lcfg["auto_select"]

    with mlflow.start_run(run_name="learning_style"):
        best_k, scores = pick_k(X, k_min, k_max, method, random_state)
        model = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("kmeans", KMeans(n_clusters=best_k, n_init=20, random_state=random_state)),
            ]
        )
        model.fit(X_raw)
        labels = model.named_steps["kmeans"].labels_

        sil = float(silhouette_score(X, labels)) if len(set(labels)) > 1 else 0.0
        dbi = (
            float(davies_bouldin_score(X, labels))
            if len(set(labels)) > 1
            else float("nan")
        )

        profile_df = df[STYLE_FEATURES].copy()
        profile_df["cluster"] = labels
        profile = (
            profile_df.groupby("cluster")[STYLE_FEATURES]
            .mean()
            .round(4)
            .to_dict(orient="index")
        )
        cluster_sizes = {int(k): int(v) for k, v in pd.Series(labels).value_counts().items()}

        mlflow.log_params({"k": best_k, "auto_select": method, "features": ",".join(STYLE_FEATURES)})
        mlflow.log_metrics({"silhouette": sil, "davies_bouldin": dbi})
        mlflow.log_dict({str(k): v for k, v in scores.items()}, "k_search.json")
        mlflow.log_dict({str(k): v for k, v in profile.items()}, "cluster_profile.json")
        mlflow.log_dict(cluster_sizes, "cluster_sizes.json")

        os.makedirs(MODEL_DIR, exist_ok=True)
        os.makedirs(METRICS_DIR, exist_ok=True)
        os.makedirs(REPORTS_DIR, exist_ok=True)
        joblib.dump(model, f"{MODEL_DIR}/kmeans.pkl")
        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            registered_model_name=MODEL_NAME,
            input_example=X_raw.iloc[:1],
        )

        with open(f"{METRICS_DIR}/style_metrics.json", "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "k": best_k,
                    "silhouette": sil,
                    "davies_bouldin": dbi,
                    "n_samples": int(len(df)),
                    "cluster_sizes": cluster_sizes,
                },
                fh,
                indent=2,
            )
        with open(f"{REPORTS_DIR}/style_profile.json", "w", encoding="utf-8") as fh:
            json.dump({"profile": profile, "k_search": scores}, fh, indent=2)

    alias_latest(MlflowClient(tracking_uri=cfg["mlflow"]["tracking_uri"]))
    print(f"Learning style model trained: k={best_k}, silhouette={sil:.3f}")


if __name__ == "__main__":
    train()
