import os
import sys
import json
import uuid
import pandas as pd
from pathlib import Path
from django.utils import timezone

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "backend"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from courses.models import CourseEnrollment, Course
from videos.models import VideoProgress
from analytics.models import LearningEvent, LearningSession

RAW_DIR = "data/raw"


def normalize_for_parquet(rows):
    return [
        {
            key: str(value) if isinstance(value, uuid.UUID) else value
            for key, value in row.items()
        }
        for row in rows
    ]


def write_parquet(rows, path):
    pd.DataFrame(normalize_for_parquet(rows)).to_parquet(path)


def export():
    snapshot_date = timezone.now().strftime("%Y-%m-%d")
    out_dir = os.path.join(RAW_DIR, snapshot_date)
    os.makedirs(out_dir, exist_ok=True)

    enrollments = list(
        CourseEnrollment.objects.select_related("student", "course").values(
            "id",
            "student_id",
            "course_id",
            "status",
            "course_progress_percent",
            "total_watch_time_seconds",
            "videos_completed",
            "login_streak",
            "enrolled_at",
            "completed_at",
            "last_accessed_at",
            "updated_at",
        )
    )

    events = list(
        LearningEvent.objects.values(
            "event_id",
            "student_id",
            "course_id",
            "video_id",
            "event_type",
            "position_seconds",
            "from_seconds",
            "to_seconds",
            "delta_seconds",
            "playback_rate",
            "session_id",
            "client_timestamp",
            "duration_ms",
            "is_tab_hidden",
            "is_fullscreen",
            "volume",
            "muted",
            "created_at",
        )
    )

    sessions = list(
        LearningSession.objects.values(
            "session_id",
            "student_id",
            "course_id",
            "started_at",
            "ended_at",
            "active_seconds",
            "idle_seconds",
            "event_count",
            "device_type",
            "browser",
            "created_at",
        )
    )

    progress = list(
        VideoProgress.objects.values(
            "progress_id",
            "student_id",
            "video_id",
            "watched_seconds",
            "duration_seconds",
            "completed",
            "completed_at",
            "last_watched_at",
        )
    )

    courses = list(
        Course.objects.values(
            "course_id",
            "category_id",
            "category_sub_id",
            "language",
            "level",
            "status",
            "created_at",
        )
    )

    write_parquet(enrollments, f"{out_dir}/enrollments.parquet")
    write_parquet(events, f"{out_dir}/learning_events.parquet")
    write_parquet(sessions, f"{out_dir}/learning_sessions.parquet")
    write_parquet(progress, f"{out_dir}/video_progress.parquet")
    write_parquet(courses, f"{out_dir}/courses.parquet")

    manifest = {
        "snapshot_date": snapshot_date,
        "exported_at": timezone.now().isoformat(),
        "tables": {
            "enrollments": len(enrollments),
            "learning_events": len(events),
            "learning_sessions": len(sessions),
            "video_progress": len(progress),
            "courses": len(courses),
        },
    }

    with open(f"{out_dir}/manifest.json", 'w', encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(out_dir)

if __name__ == "__main__":
    export()
