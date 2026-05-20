from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

RAW_ROOT = "data/raw"
REPORTS_DIR = "reports"

REQUIRED_TABLES = {
    "enrollments": [
        "student_id",
        "course_id",
        "status",
        "enrolled_at",
        "course_progress_percent",
    ],
    "learning_events": [
        "event_id",
        "student_id",
        "course_id",
        "event_type",
        "created_at",
    ],
}

OPTIONAL_TABLES = {
    "learning_sessions": ["session_id", "student_id", "course_id"],
    "video_progress": ["progress_id", "student_id", "video_id"],
    "courses": ["course_id", "status"],
}


def latest_snapshot_dir() -> str:
    snapshots = sorted(
        path
        for path in os.listdir(RAW_ROOT)
        if os.path.isdir(os.path.join(RAW_ROOT, path))
    )
    if not snapshots:
        raise RuntimeError("No raw snapshots found.")
    return os.path.join(RAW_ROOT, snapshots[-1])


def check_table(
    issues: list[str],
    table: str,
    path: str,
    required_cols: list[str],
    optional: bool = False,
) -> pd.DataFrame | None:
    if not os.path.exists(path):
        if optional:
            return None
        issues.append(f"[missing] {table}: {path}")
        return None
    df = pd.read_parquet(path)
    if df.empty and not optional:
        issues.append(f"[empty] {table}: 0 rows")
    missing = [c for c in required_cols if c not in df.columns]
    if missing and not (optional and df.empty):
        issues.append(f"[schema] {table} missing columns: {missing}")
    return df


def validate() -> dict:
    snap = latest_snapshot_dir()
    issues: list[str] = []
    summary: dict = {"snapshot_dir": snap, "tables": {}}

    tables: dict[str, pd.DataFrame] = {}
    for tname, cols in REQUIRED_TABLES.items():
        df = check_table(issues, tname, f"{snap}/{tname}.parquet", cols)
        if df is not None:
            tables[tname] = df
            summary["tables"][tname] = {"rows": len(df), "cols": list(df.columns)}

    for tname, cols in OPTIONAL_TABLES.items():
        df = check_table(issues, tname, f"{snap}/{tname}.parquet", cols, optional=True)
        if df is not None:
            tables[tname] = df
            summary["tables"][tname] = {"rows": len(df), "cols": list(df.columns)}

    enrol = tables.get("enrollments")
    events = tables.get("learning_events")

    if enrol is not None and not enrol.empty:
        dup = enrol.duplicated(subset=["student_id", "course_id"]).sum()
        if dup:
            issues.append(f"[dup] enrollments has {dup} duplicate (student,course) pairs")
        if "course_progress_percent" in enrol.columns:
            bad = enrol["course_progress_percent"].dropna()
            bad = bad[(bad < 0) | (bad > 100)]
            if len(bad):
                issues.append(
                    f"[range] enrollments.course_progress_percent out of [0,100]: {len(bad)} rows"
                )

    if events is not None and not events.empty:
        if "event_id" in events.columns:
            dup = events["event_id"].duplicated().sum()
            if dup:
                issues.append(f"[dup] learning_events has {dup} duplicate event_id")
        if enrol is not None and "student_id" in enrol.columns:
            enrolled = set(enrol["student_id"].astype(str))
            orphan = (~events["student_id"].astype(str).isin(enrolled)).sum()
            if orphan:
                issues.append(
                    f"[fk] learning_events has {orphan} rows whose student_id is not in enrollments"
                )

    summary["issues"] = issues
    summary["passed"] = len(issues) == 0
    summary["validated_at"] = datetime.now(timezone.utc).isoformat()

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(f"{REPORTS_DIR}/data_validation.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    if issues:
        print("DATA VALIDATION FAILED:")
        for line in issues:
            print(f"  - {line}")
        sys.exit(1)

    print(f"DATA VALIDATION PASSED. {len(tables)} tables checked.")
    return summary


if __name__ == "__main__":
    validate()
