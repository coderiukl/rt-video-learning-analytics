from __future__ import annotations
import logging

from analytics.ml.features import build_dropout_features
from analytics.ml.registry import load as load_model, invalidate as invalidate_model
from analytics.ml.schemas import FEATURE_NAMES, DropoutFeatures
from analytics.ml_engine import compute_risk_score

logger = logging.getLogger(__name__)


def _risk_level(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _reasons(f: DropoutFeatures) -> list[str]:
    out: list[str] = []
    if f.days_inactive >= 7:
        out.append(f"Không vào học {int(f.days_inactive)} ngày")
    elif f.days_inactive >= 3:
        out.append(f"Ít hoạt động ({int(f.days_inactive)} ngày không vào)")
    if f.progress_percent < 20 and f.time_ratio > 0.3:
        out.append(f"Tiến độ rất thấp ({f.progress_percent:.1f}%)")
    if f.login_streak == 0:
        out.append("Không có chuỗi đăng nhập liên tục")
    if f.skip_fwd_ratio > 0.15:
        out.append(f"Tỷ lệ tua nhanh cao ({f.skip_fwd_ratio:.0%})")
    if f.note_ratio == 0 and f.activity_per_day > 0:
        out.append("Không có ghi chú nào")
    if f.avg_playback_rate > 1.75:
        out.append(f"Thường xem ở tốc độ {f.avg_playback_rate:.1f}x")
    if f.hidden_tab_ratio > 0.4:
        out.append(f"Nhiều hoạt động khi tab bị ẩn ({f.hidden_tab_ratio:.0%})")
    if f.muted_ratio > 0.6:
        out.append(f"Thường xem ở trạng thái tắt tiếng ({f.muted_ratio:.0%})")
    return out


def predict(enrollment, events_qs=None) -> dict:
    model, scaler = load_model("dropout_predictor")

    if model is None:
        result = compute_risk_score(enrollment.student, enrollment.course)
        result["model_type"] = "rule-based"
        result["dropout_probability"] = None
        return result

    import pandas as pd
    from analytics.ml.schemas import FEATURE_NAMES

    feats = build_dropout_features(enrollment, events_qs)
    # DataFrame preserves feature names through Pipeline/scaler and silences
    # the "X does not have valid feature names" sklearn warning.
    X = pd.DataFrame([feats.to_dict()], columns=FEATURE_NAMES)

    # MLflow pyfunc wraps a Pipeline that already includes the scaler.
    is_pyfunc = type(model).__module__.startswith("mlflow.pyfunc")
    is_pipeline = hasattr(model, "named_steps") or is_pyfunc
    if scaler is not None and not is_pipeline:
        X = scaler.transform(X)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        dropout_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
    else:
        # pyfunc returns a 1-col DataFrame of class labels, not proba.
        pred = model.predict(X)
        try:
            dropout_prob = float(pred.iloc[0]) if hasattr(pred, "iloc") else float(pred[0])
        except (TypeError, ValueError):
            dropout_prob = 0.0

    score = round(dropout_prob * 100, 1)
    return {
        "risk_score": score,
        "risk_level": _risk_level(score),
        "dropout_probability": round(dropout_prob, 4),
        "reasons": _reasons(feats),
        "model_type": "ml_registry",
    }


def reload() -> None:
    """Drop cached model — next predict() reloads from registry."""
    invalidate_model("dropout_predictor")


def model_status() -> dict:
    model, _ = load_model("dropout_predictor")
    return {
        "exists": model is not None,
        "feature_names": FEATURE_NAMES,
        "n_features": len(FEATURE_NAMES),
        "source": "ml_registry" if model is not None else "none",
    }
