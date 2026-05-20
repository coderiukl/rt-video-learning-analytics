from dataclasses import dataclass, asdict, fields
from typing import Any
import numpy as np

FEATURE_NAMES = [
    "days_inactive",
    "progress_percent",
    "login_streak",
    "skip_fwd_ratio",
    "skip_bwd_ratio",
    "note_ratio",
    "avg_playback_rate",
    "time_ratio",
    "activity_per_day",
    "avg_session_active_minutes",
    "session_count_30d",
    "hidden_tab_ratio",
    "muted_ratio",
]


@dataclass
class DropoutFeatures:
    days_inactive: float
    progress_percent: float
    login_streak: float
    skip_fwd_ratio: float
    skip_bwd_ratio: float
    note_ratio: float
    avg_playback_rate: float
    time_ratio: float
    activity_per_day: float
    avg_session_active_minutes: float
    session_count_30d: float
    hidden_tab_ratio: float
    muted_ratio: float

    def to_array(self) -> np.ndarray:
        return np.array(
            [getattr(self, name) for name in FEATURE_NAMES], dtype=np.float64
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DropoutFeatures":
        valid = {f.name for f in fields(cls)}
        return cls(**{k: data[k] for k in valid if k in data})
