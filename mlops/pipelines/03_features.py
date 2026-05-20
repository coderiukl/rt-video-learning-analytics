"""Build dropout training features from the latest raw snapshot.

Imports the SAME feature builder + labelling rules used by the Django
serving layer (analytics.ml.features / analytics.ml.labels) so training
and serving cannot drift.
"""
import os
import sys
import json
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

# Bootstrap Django so we can reuse analytics.ml.* (no DB queries are issued
# here; we just need the Python modules + the CourseEnrollment status enum).
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django  # noqa: E402

django.setup()

from analytics.ml.features import build_dropout_features_from_frame  # noqa: E402  # pyright: ignore[reportMissingImports]
from analytics.ml.labels import label_dropout  # noqa: E402  # pyright: ignore[reportMissingImports]
from analytics.ml.schemas import FEATURE_NAMES  # noqa: E402  # pyright: ignore[reportMissingImports]

RAW_ROOT = "data/raw"
PROCESSED_DIR = "data/processed"
CONFIG_CANDIDATES = ["mlops/config/mlops.yaml", "params.yaml"]


def load_dropout_params() -> dict:
    for path in CONFIG_CANDIDATES:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                cfg = yaml.safe_load(fh) or {}
            return cfg.get("dropout", {}) or {}
    raise RuntimeError(
        f"No config found. Looked for: {', '.join(CONFIG_CANDIDATES)}"
    )


def latest_snapshot_dir() -> str:
    snapshots = sorted(
        path
        for path in os.listdir(RAW_ROOT)
        if os.path.isdir(os.path.join(RAW_ROOT, path))
    )
    if not snapshots:
        raise RuntimeError("No raw snapshots found.")
    return os.path.join(RAW_ROOT, snapshots[-1])


def prepare() -> None:
    params = load_dropout_params()
    lookback_days = int(params.get("lookback_days", 30))

    snapshot_dir = latest_snapshot_dir()
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    enrollments = pd.read_parquet(f"{snapshot_dir}/enrollments.parquet")
    events = pd.read_parquet(f"{snapshot_dir}/learning_events.parquet")
    sessions = pd.read_parquet(f"{snapshot_dir}/learning_sessions.parquet")

    # Guarantee expected columns exist even when a snapshot is empty.
    for col in ("student_id", "course_id", "active_seconds", "started_at"):
        if col not in sessions.columns:
            sessions[col] = pd.Series(dtype="object")

    enrollments["enrolled_at"] = pd.to_datetime(enrollments["enrolled_at"], utc=True)
    enrollments["last_accessed_at"] = pd.to_datetime(
        enrollments["last_accessed_at"], utc=True
    )
    if "created_at" in events.columns:
        events["created_at"] = pd.to_datetime(events["created_at"], utc=True)
    if "started_at" in sessions.columns:
        sessions["started_at"] = pd.to_datetime(sessions["started_at"], utc=True)

    now = pd.Timestamp.utcnow()
    cutoff = now - pd.Timedelta(days=lookback_days)

    if "created_at" in events.columns:
        events = events[events["created_at"] >= cutoff]
    if "started_at" in sessions.columns:
        sessions = sessions[sessions["started_at"] >= cutoff]

    rows = []
    for _, enrollment in enrollments.iterrows():
        sid, cid = enrollment["student_id"], enrollment["course_id"]
        ev = events[(events["student_id"] == sid) & (events["course_id"] == cid)]
        se = sessions[(sessions["student_id"] == sid) & (sessions["course_id"] == cid)]

        feats = build_dropout_features_from_frame(enrollment, ev, se, now)
        row = feats.to_dict()
        row["student_id"] = sid
        row["course_id"] = cid
        row["status"] = enrollment["status"]
        row["label"] = label_dropout(enrollment["status"], feats)
        rows.append(row)

    features = pd.DataFrame(rows)
    features.to_parquet(f"{PROCESSED_DIR}/dropout_features.parquet")

    with open(f"{PROCESSED_DIR}/feature_manifest.json", "w", encoding="utf-8") as fh:
        json.dump(
            {
                "snapshot_dir": snapshot_dir,
                "feature_names": list(FEATURE_NAMES),
                "rows": len(features),
                "label_positive": int(features["label"].sum()),
                "label_negative": int((features["label"] == 0).sum()),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            fh,
            indent=2,
        )

    print(f"Prepared {len(features)} rows -> {PROCESSED_DIR}/dropout_features.parquet")


if __name__ == "__main__":
    prepare()
