from __future__ import annotations

import json
import os
import sys
import yaml
from datetime import datetime, timezone

import numpy as np
import pandas as pd

CONFIG_PATH = "mlops/config/mlops.yaml"
CURRENT_PATH = "data/processed/dropout_features.parquet"
REFERENCE_PATH = "data/processed/dropout_features_reference.parquet"
REPORT_PATH = "reports/drift_report.json"

EXCLUDE = {"student_id", "course_id", "status", "label"}


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index. <0.1 stable, 0.1-0.25 minor, >0.25 major drift."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    if len(expected) == 0 or len(actual) == 0:
        return 0.0
    if np.allclose(expected.std(), 0) and np.allclose(actual.std(), 0):
        return 0.0
    breaks = np.unique(np.percentile(expected, np.linspace(0, 100, bins + 1)))
    if len(breaks) < 2:
        return 0.0
    breaks = breaks.astype(float)
    breaks[0], breaks[-1] = -np.inf, np.inf
    e_hist, _ = np.histogram(expected, breaks)
    a_hist, _ = np.histogram(actual, breaks)
    eps = 1e-6
    e_pct = np.where(e_hist == 0, eps, e_hist) / len(expected)
    a_pct = np.where(a_hist == 0, eps, a_hist) / len(actual)
    return float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))


def run() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    threshold = float(cfg["monitoring"]["drift_threshold"])
    retrain_on_drift = bool(cfg["monitoring"].get("retrain_on_drift", False))

    if not os.path.exists(CURRENT_PATH):
        raise FileNotFoundError(f"Missing current features: {CURRENT_PATH}")

    current = pd.read_parquet(CURRENT_PATH)
    os.makedirs("reports", exist_ok=True)

    if not os.path.exists(REFERENCE_PATH):
        report = {
            "status": "no_reference",
            "message": (
                f"No reference at {REFERENCE_PATH}. Bootstrap with: "
                f"`copy {CURRENT_PATH} {REFERENCE_PATH}` after a trusted training run."
            ),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(REPORT_PATH, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(report["message"])
        return report

    reference = pd.read_parquet(REFERENCE_PATH)
    numeric_cols = [
        c
        for c in reference.columns
        if c not in EXCLUDE and pd.api.types.is_numeric_dtype(reference[c])
    ]

    scores: dict[str, float] = {}
    for col in numeric_cols:
        if col not in current.columns:
            continue
        scores[col] = round(psi(reference[col].values, current[col].values), 4)

    drifted = {k: v for k, v in scores.items() if v > threshold}
    report = {
        "status": "drift_detected" if drifted else "stable",
        "threshold": threshold,
        "psi": scores,
        "drifted_features": drifted,
        "n_current": int(len(current)),
        "n_reference": int(len(reference)),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    if drifted:
        print(f"DRIFT DETECTED in {len(drifted)} features: {list(drifted)}")
        if retrain_on_drift:
            sys.exit(2)
    else:
        print(f"No drift across {len(scores)} features (threshold={threshold}).")
    return report


if __name__ == "__main__":
    run()
