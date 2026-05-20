"""Promote the latest dropout-predictor version to Production if gates pass.

Uses MLflow registered-model aliases (the post-2.9 successor to stages).
After this script runs, serving loads the model via "models:/dropout_predictor@production".
"""
from __future__ import annotations

import json
import sys
import yaml

from mlflow.tracking import MlflowClient

CONFIG_PATH = "mlops/config/mlops.yaml"
METRICS_PATH = "metrics/dropout_metrics.json"
MODEL_NAME = "dropout_predictor"
PROD_ALIAS = "production"
ARCHIVE_ALIAS = "archived"


def _latest_version(client: MlflowClient) -> str | None:
    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    if not versions:
        return None
    return max(versions, key=lambda v: int(v.version)).version


def promote() -> None:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    with open(METRICS_PATH, "r", encoding="utf-8") as fh:
        metrics = json.load(fh)

    gate = cfg["dropout"]["promotion"]
    f1 = metrics.get("f1") or 0.0
    auc = metrics.get("roc_auc") or 0.0

    if f1 < gate["min_f1"] or auc < gate["min_roc_auc"]:
        print(
            f"GATE FAILED: f1={f1:.3f} (min={gate['min_f1']}), "
            f"roc_auc={auc:.3f} (min={gate['min_roc_auc']})"
        )
        sys.exit(1)

    client = MlflowClient(tracking_uri=cfg["mlflow"]["tracking_uri"])

    latest = _latest_version(client)
    if latest is None:
        print(f"No registered versions of {MODEL_NAME}; nothing to promote.")
        sys.exit(0)

    # Archive whatever currently holds the production alias.
    try:
        previous = client.get_model_version_by_alias(MODEL_NAME, PROD_ALIAS)
        if previous and previous.version != latest:
            client.set_registered_model_alias(MODEL_NAME, ARCHIVE_ALIAS, previous.version)
    except Exception:
        previous = None

    client.set_registered_model_alias(MODEL_NAME, PROD_ALIAS, latest)
    print(f"Aliased {MODEL_NAME} v{latest} -> @{PROD_ALIAS}")


if __name__ == "__main__":
    promote()
