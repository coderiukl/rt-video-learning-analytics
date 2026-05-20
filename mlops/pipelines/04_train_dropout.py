"""Train the dropout-prediction model.

Reads features prepared by 03_features.py, logs everything to MLflow,
registers the resulting model under name `dropout_predictor`. The 08
script later promotes the version to Production if metric gates pass.
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
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

# Bootstrap Django so we can reuse FEATURE_NAMES from analytics.ml.schemas.
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django  # noqa: E402

django.setup()

from analytics.ml.schemas import FEATURE_NAMES  # noqa: E402  # pyright: ignore[reportMissingImports]

CONFIG_PATH = "mlops/config/mlops.yaml"
FEATURES_PATH = "data/processed/dropout_features.parquet"
MODEL_DIR = "models/dropout"
METRICS_DIR = "metrics"
REPORTS_DIR = "reports"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build_estimator(hp: dict, scale_pos_weight: float, random_state: int) -> xgb.XGBClassifier:
    return xgb.XGBClassifier(
        n_estimators=hp["n_estimators"],
        max_depth=hp["max_depth"],
        learning_rate=hp["learning_rate"],
        subsample=hp["subsample"],
        colsample_bytree=hp["colsample_bytree"],
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        tree_method="hist",
        random_state=random_state,
        n_jobs=-1,
    )


def safe_metric(fn, *args, **kwargs):
    try:
        return float(fn(*args, **kwargs))
    except Exception:
        return None


def maybe_log_shap(base_model, X_test_scaled: np.ndarray) -> dict | None:
    try:
        import shap

        explainer = shap.TreeExplainer(base_model)
        values = explainer.shap_values(X_test_scaled[:200])
        if isinstance(values, list):  # legacy multi-class output
            values = values[1] if len(values) > 1 else values[0]
        return dict(
            zip(FEATURE_NAMES, np.abs(values).mean(axis=0).tolist())
        )
    except Exception as exc:
        print(f"[warn] SHAP skipped: {exc}")
        return None


def train() -> tuple[str, dict]:
    cfg = load_config()
    dcfg = cfg["dropout"]
    random_state = int(dcfg.get("random_state", 42))

    mlflow.set_tracking_uri(cfg["mlflow"]["tracking_uri"])
    mlflow.set_experiment(cfg["mlflow"]["experiment_name"])

    df = pd.read_parquet(FEATURES_PATH)
    if len(df) < 4:
        raise RuntimeError(
            f"Only {len(df)} rows in {FEATURES_PATH}; need >=4 to train. "
            "Seed more enrollments or run the mock-data command."
        )

    X = df[FEATURE_NAMES]
    y = df["label"].astype(int)
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    if n_pos == 0 or n_neg == 0:
        raise RuntimeError(
            f"Need both classes present (got pos={n_pos}, neg={n_neg})."
        )
    scale_pos_weight = n_neg / max(n_pos, 1)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=float(dcfg.get("test_size", 0.2)),
        stratify=y,
        random_state=random_state,
    )

    # CV folds capped by minority class count in the training split.
    min_class = int(min((y_train == 0).sum(), (y_train == 1).sum()))
    cv_folds = max(2, min(int(dcfg.get("cv_folds", 5)), min_class))
    cv = StratifiedKFold(
        n_splits=cv_folds, shuffle=True, random_state=random_state
    )

    with mlflow.start_run(run_name="dropout_xgb") as run:
        base_estimator = build_estimator(
            dcfg["hyperparams"], scale_pos_weight, random_state
        )
        if dcfg.get("calibrate", True):
            clf = CalibratedClassifierCV(base_estimator, method="isotonic", cv=cv)
        else:
            clf = base_estimator

        # Single artefact: scaler + classifier in one Pipeline so serving never
        # has to manage the scaler separately and DataFrame feature names flow
        # through (silences the "X does not have valid feature names" warning).
        model = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("clf", clf),
            ]
        )

        try:
            cv_auc = float(
                cross_val_score(
                    model, X_train, y_train, cv=cv, scoring="roc_auc"
                ).mean()
            )
        except Exception as exc:
            print(f"[warn] CV failed: {exc}")
            cv_auc = None

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        metrics = {
            "cv_roc_auc": cv_auc,
            "accuracy": safe_metric(accuracy_score, y_test, y_pred),
            "precision": safe_metric(precision_score, y_test, y_pred, zero_division=0),
            "recall": safe_metric(recall_score, y_test, y_pred, zero_division=0),
            "f1": safe_metric(f1_score, y_test, y_pred, zero_division=0),
            "roc_auc": safe_metric(roc_auc_score, y_test, y_prob),
            "brier": safe_metric(brier_score_loss, y_test, y_prob),
            "num_train": int(len(X_train)),
            "num_test": int(len(X_test)),
            "num_pos": n_pos,
            "num_neg": n_neg,
        }

        mlflow.log_params(
            {
                **dcfg["hyperparams"],
                "scale_pos_weight": scale_pos_weight,
                "calibrate": bool(dcfg.get("calibrate", True)),
                "cv_folds": cv_folds,
            }
        )
        mlflow.log_metrics(
            {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
        )

        # SHAP needs the raw XGB on scaled inputs; reuse the pipeline's scaler.
        fitted_scaler = model.named_steps["scaler"]
        X_train_s = fitted_scaler.transform(X_train)
        X_test_s = fitted_scaler.transform(X_test)
        base_for_shap = build_estimator(dcfg["hyperparams"], scale_pos_weight, random_state)
        base_for_shap.fit(X_train_s, y_train)
        shap_imp = maybe_log_shap(base_for_shap, X_test_s)
        if shap_imp:
            mlflow.log_dict(shap_imp, "shap_importance.json")

        mlflow.log_dict(
            {"matrix": confusion_matrix(y_test, y_pred).tolist()},
            "confusion_matrix.json",
        )

        os.makedirs(MODEL_DIR, exist_ok=True)
        os.makedirs(METRICS_DIR, exist_ok=True)
        os.makedirs(REPORTS_DIR, exist_ok=True)
        # Pipeline is the single artefact — it bundles the scaler.
        joblib.dump(model, f"{MODEL_DIR}/dropout_model.pkl")
        # Also dump scaler alone for backwards-compat with the legacy serving
        # path that loaded model+scaler separately.
        joblib.dump(fitted_scaler, f"{MODEL_DIR}/dropout_scaler.pkl")
        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            registered_model_name="dropout_predictor",
            input_example=X_train.iloc[:1],
        )

        with open(f"{METRICS_DIR}/dropout_metrics.json", "w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2)
        if shap_imp:
            with open(f"{REPORTS_DIR}/dropout_feature_importance.json", "w", encoding="utf-8") as fh:
                json.dump(shap_imp, fh, indent=2)

        print(json.dumps(metrics, indent=2))
        return run.info.run_id, metrics


if __name__ == "__main__":
    train()
