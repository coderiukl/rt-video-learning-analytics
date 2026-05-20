from __future__ import annotations
from datetime import timedelta
from typing import Optional

from django.utils import timezone

from analytics.models import LearningEvent, LearningSession
from .schemas import DropoutFeatures


def build_dropout_features(enrollment, events_qs=None, sessions_qs=None, lookback_days: int = 30) -> DropoutFeatures:
    now = timezone.now()
    cutoff = now - timedelta(days=lookback_days)

    if events_qs is None:
        events_qs = LearningEvent.objects.filter(
            student=enrollment.student,
            course=enrollment.course,
            created_at__gte=cutoff,
        )
    if sessions_qs is None:
        sessions_qs = LearningSession.objects.filter(
            student=enrollment.student,
            course=enrollment.course,
            started_at__gte=cutoff,
        )

    total = events_qs.count()
    enrolled_days = max((now - enrollment.enrolled_at).days, 1)

    def ratio(qs):
        return qs.count() / total if total else 0.0

    last = enrollment.last_accessed_at or enrollment.enrolled_at
    days_inactive = max((now - last).days, 0)

    rates = list(
        events_qs.exclude(playback_rate__isnull=True).values_list(
            "playback_rate", flat=True
        )
    )
    actives = list(sessions_qs.values_list("active_seconds", flat=True))

    return DropoutFeatures(
        days_inactive=float(days_inactive),
        progress_percent=float(enrollment.course_progress_percent or 0.0),
        login_streak=float(enrollment.login_streak or 0),
        skip_fwd_ratio=ratio(
            events_qs.filter(event_type=LearningEvent.EventType.SKIP_FORWARD_10)
        ),
        skip_bwd_ratio=ratio(
            events_qs.filter(event_type=LearningEvent.EventType.SKIP_BACKWARD_10)
        ),
        note_ratio=ratio(
            events_qs.filter(event_type=LearningEvent.EventType.NOTE_CREATED)
        ),
        avg_playback_rate=float(sum(rates) / len(rates)) if rates else 1.0,
        time_ratio=min(enrolled_days / 30.0, 1.0),
        activity_per_day=total / enrolled_days,
        avg_session_active_minutes=(sum(actives) / len(actives) / 60.0)
        if actives
        else 0.0,
        session_count_30d=float(len(actives)),
        hidden_tab_ratio=ratio(events_qs.filter(is_tab_hidden=True)),
        muted_ratio=ratio(events_qs.filter(muted=True)),
    )


def build_dropout_features_from_frame(enrollment_row, events_df, sessions_df, now) -> DropoutFeatures:
    total = len(events_df)
    enrolled_days = max((now - enrollment_row["enrolled_at"]).days, 1)
    last = enrollment_row["last_accessed_at"]
    if last is None or last is type(None):
        last = enrollment_row["enrolled_at"]
    try:
        days_inactive = max((now - last).days, 0)
    except (TypeError, AttributeError):
        days_inactive = max((now - enrollment_row["enrolled_at"]).days, 0)

    def ratio(mask):
        return float(mask.sum()) / total if total else 0.0

    skip_fwd = events_df["event_type"] == "skip_forward_10"
    skip_bwd = events_df["event_type"] == "skip_backward_10"
    note_made = events_df["event_type"] == "note_created"

    rates = events_df["playback_rate"].dropna() if total else []
    avg_rate = float(rates.mean()) if len(rates) else 1.0

    actives = sessions_df["active_seconds"] if len(sessions_df) else []
    avg_active_min = float(actives.mean()) / 60.0 if len(actives) else 0.0

    return DropoutFeatures(
        days_inactive=float(days_inactive),
        progress_percent=float(enrollment_row.get("course_progress_percent") or 0.0),
        login_streak=float(enrollment_row.get("login_streak") or 0),
        skip_fwd_ratio=ratio(skip_fwd),
        skip_bwd_ratio=ratio(skip_bwd),
        note_ratio=ratio(note_made),
        avg_playback_rate=avg_rate,
        time_ratio=min(enrolled_days / 30.0, 1.0),
        activity_per_day=total / enrolled_days,
        avg_session_active_minutes=avg_active_min,
        session_count_30d=float(len(sessions_df)),
        hidden_tab_ratio=ratio(events_df["is_tab_hidden"] == True) if total else 0.0,
        muted_ratio=ratio(events_df["muted"] == True) if total else 0.0,
    )
