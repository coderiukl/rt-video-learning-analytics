"""Backward-compatible facade for legacy imports.

The real logic now lives in:
  - analytics.ml.features       (feature builder)
  - analytics.ml.registry       (model loader)
  - analytics.services.dropout_service (prediction)

Training happens OFFLINE in mlops/pipelines/ and writes to the registry.
"""
from analytics.ml.schemas import FEATURE_NAMES  # re-export
from analytics.ml.features import build_dropout_features as extract_features  # re-export
from analytics.services.dropout_service import (
    predict as predict_dropout,
    model_status as get_model_status,
    reload as reload_dropout_model,
)

__all__ = [
    "FEATURE_NAMES",
    "extract_features",
    "predict_dropout",
    "get_model_status",
    "reload_dropout_model",
]
