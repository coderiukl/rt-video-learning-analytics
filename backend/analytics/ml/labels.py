"""Dropout labelling rules — shared between training and any rule-based fallback."""
from courses.models import CourseEnrollment
from .schemas import DropoutFeatures


def label_dropout(status: str, f: DropoutFeatures) -> int:
    if status == CourseEnrollment.Status.DROPPED:
        return 1
    if f.days_inactive >= 14:
        return 1
    if f.progress_percent < 20 and f.days_inactive >= 7:
        return 1
    if f.skip_fwd_ratio >= 0.3:
        return 1
    if f.hidden_tab_ratio >= 0.5 and f.progress_percent < 50:
        return 1
    return 0


def label_dropout_row(row: dict) -> int:
    """Pandas-friendly version: takes a dict-like row with FEATURE_NAMES + 'status'."""
    f = DropoutFeatures.from_dict(row)
    return label_dropout(row.get("status", ""), f)
