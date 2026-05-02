"""
Dropout Prediction bằng Random Forest.

- extract_features(): trích xuất feature vector 9 chiều từ enrollment + events
- train_model(): train RandomForestClassifier, lưu pkl
- predict_dropout(): load model, predict, fallback rule-based nếu chưa có model
"""

import os
import logging
import numpy as np
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import LearningEvent
from courses.models import CourseEnrollment

logger = logging.getLogger(__name__)

# Thư mục lưu model
MODEL_DIR = os.path.join(settings.BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "dropout_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "dropout_scaler.pkl")

FEATURE_NAMES = [
    "days_inactive",       # f1
    "progress_percent",    # f2
    "login_streak",        # f3
    "skip_fwd_ratio",      # f4
    "skip_bwd_ratio",      # f5
    "note_ratio",          # f6
    "avg_playback_rate",   # f7
    "time_ratio",          # f8
    "activity_per_day",    # f9
]


def extract_features(enrollment, events_qs=None):
    """
    Trích xuất feature vector 9 chiều cho một cặp (student, course).
    
    Args:
        enrollment: CourseEnrollment instance
        events_qs: QuerySet LearningEvent đã filter sẵn (30 ngày gần nhất).
                   Nếu None sẽ tự query.
    
    Returns:
        numpy array shape (9,)
    """
    now = timezone.now()
    enrolled_days = (now - enrollment.enrolled_at).days

    # Nếu chưa truyền events_qs, tự query 30 ngày gần nhất
    if events_qs is None:
        recent_cutoff = now - timedelta(days=30)
        events_qs = LearningEvent.objects.filter(
            student=enrollment.student,
            course=enrollment.course,
            created_at__gte=recent_cutoff,
        )

    # f1: days_inactive
    if enrollment.last_accessed_at:
        days_inactive = (now - enrollment.last_accessed_at).days
    else:
        days_inactive = max(enrolled_days, 0)  # Lấy số ngày từ lúc đăng ký

    # f2: progress_percent (giữ nguyên 0-100)
    progress_percent = enrollment.course_progress_percent or 0.0

    # f3: login_streak
    login_streak = enrollment.login_streak or 0

    # Đếm các loại event
    total_events = events_qs.count()
    skip_fwd_count = events_qs.filter(
        event_type=LearningEvent.EventType.SKIP_FORWARD_10
    ).count()
    skip_bwd_count = events_qs.filter(
        event_type=LearningEvent.EventType.SKIP_BACKWARD_10
    ).count()
    note_count = events_qs.filter(
        event_type=LearningEvent.EventType.NOTE_CREATED
    ).count()

    # f4: skip_fwd_ratio
    skip_fwd_ratio = skip_fwd_count / total_events if total_events > 0 else 0.0

    # f5: skip_bwd_ratio
    skip_bwd_ratio = skip_bwd_count / total_events if total_events > 0 else 0.0

    # f6: note_ratio
    note_ratio = note_count / total_events if total_events > 0 else 0.0

    # f7: avg_playback_rate
    rate_events = list(
        events_qs.exclude(playback_rate__isnull=True)
        .values_list("playback_rate", flat=True)
    )
    avg_playback_rate = (
        sum(rate_events) / len(rate_events) if rate_events else 1.0
    )

    # f8: time_ratio — enrolled_days / 30, clamp [0, 1]
    enrolled_days = (now - enrollment.enrolled_at).days
    time_ratio = min(enrolled_days / 30.0, 1.0) if enrolled_days >= 0 else 0.0

    # f9: activity_per_day
    activity_per_day = total_events / max(enrolled_days, 1)

    return np.array([
        days_inactive,
        progress_percent,
        login_streak,
        skip_fwd_ratio,
        skip_bwd_ratio,
        note_ratio,
        avg_playback_rate,
        time_ratio,
        activity_per_day,
    ], dtype=np.float64)


def _get_label(enrollment, features):
    """
    Ground truth: dropout = 1 hay 0.
    Dùng để dạy model nhận biết các pattern xấu.
    """
    if enrollment.status == CourseEnrollment.Status.DROPPED:
        return 1

    days_inactive = features[0]
    progress = features[1]
    skip_fwd_ratio = features[3]

    # Các điều kiện gán nhãn là Dropout (1) để model học
    if days_inactive >= 14:
        return 1
    if progress < 20.0 and days_inactive >= 7:
        return 1
    
    # Nếu có hành vi cực kỳ xấu (tua nhanh > 30%) -> Rủi ro bỏ học rất cao!
    if skip_fwd_ratio >= 0.3:
        return 1

    return 0


def train_model():
    """
    Train RandomForestClassifier từ toàn bộ CourseEnrollment.
    Lưu model + scaler vào thư mục backend/models/.
    
    Returns:
        dict với thông tin training: num_samples, num_dropout, num_active, accuracy, model_path
    """
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score

    now = timezone.now()
    recent_cutoff = now - timedelta(days=30)

    enrollments = CourseEnrollment.objects.select_related(
        "student", "course"
    ).all()

    X_list = []
    y_list = []

    for enrollment in enrollments:
        events_qs = LearningEvent.objects.filter(
            student=enrollment.student,
            course=enrollment.course,
            created_at__gte=recent_cutoff,
        )
        features = extract_features(enrollment, events_qs)
        label = _get_label(enrollment, features)
        X_list.append(features)
        y_list.append(label)

    if len(X_list) < 2:
        return {
            "success": False,
            "message": "Không đủ dữ liệu để train (cần ít nhất 2 enrollment).",
            "num_samples": len(X_list),
        }

    X = np.array(X_list)
    y = np.array(y_list)

    # StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # RandomForestClassifier
    clf = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=42,
        max_depth=10,
        min_samples_split=2,
    )
    clf.fit(X_scaled, y)

    # Cross-validation nếu đủ mẫu
    accuracy = None
    if len(X_list) >= 5:
        n_splits = min(5, len(X_list))
        try:
            scores = cross_val_score(clf, X_scaled, y, cv=n_splits, scoring="accuracy")
            accuracy = round(float(scores.mean()), 4)
        except Exception as e:
            logger.warning(f"Cross-validation failed: {e}")
            accuracy = None

    # Lưu model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    # Feature importances
    importances = dict(zip(FEATURE_NAMES, [round(float(v), 4) for v in clf.feature_importances_]))

    result = {
        "success": True,
        "num_samples": len(X_list),
        "num_dropout": int(y.sum()),
        "num_active": int((y == 0).sum()),
        "accuracy": accuracy,
        "feature_importances": importances,
        "model_path": MODEL_PATH,
        "trained_at": now.isoformat(),
    }

    logger.info(f"Dropout model trained: {result}")
    return result


# Cache model trong memory để không load lại mỗi request
_cached_model = None
_cached_scaler = None
_cache_mtime = None


def _load_model():
    """Load model + scaler từ file pkl, cache trong memory."""
    global _cached_model, _cached_scaler, _cache_mtime

    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        return None, None

    current_mtime = os.path.getmtime(MODEL_PATH)

    # Chỉ reload nếu file thay đổi
    if _cached_model is not None and _cache_mtime == current_mtime:
        return _cached_model, _cached_scaler

    import joblib
    _cached_model = joblib.load(MODEL_PATH)
    _cached_scaler = joblib.load(SCALER_PATH)
    _cache_mtime = current_mtime

    logger.info("Dropout model loaded from disk.")
    return _cached_model, _cached_scaler


def predict_dropout(enrollment, events_qs=None):
    """
    Dự đoán xác suất dropout cho một enrollment.
    
    - Nếu có model pkl → dùng RandomForest
    - Nếu chưa có → fallback về compute_risk_score() rule-based
    
    Returns:
        dict: {risk_score, risk_level, dropout_probability, reasons, model_type}
    """
    model, scaler = _load_model()

    if model is None:
        # Fallback về rule-based
        from .ml_engine import compute_risk_score
        result = compute_risk_score(enrollment.student, enrollment.course)
        result["model_type"] = "rule-based"
        result["dropout_probability"] = None
        return result

    # Trích xuất features
    features = extract_features(enrollment, events_qs)
    features_scaled = scaler.transform(features.reshape(1, -1))

    # Predict
    proba = model.predict_proba(features_scaled)[0]
    # proba[0] = P(active), proba[1] = P(dropout)
    dropout_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
    risk_score = round(dropout_prob * 100, 1)

    # Risk level
    if risk_score >= 70:
        risk_level = "high"
    elif risk_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Tạo reasons dựa trên feature values
    reasons = _generate_reasons(features)

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "dropout_probability": round(dropout_prob, 4),
        "reasons": reasons,
        "model_type": "random_forest",
    }


def _generate_reasons(features):
    """Tạo danh sách lý do cảnh báo dựa trên feature values."""
    reasons = []

    days_inactive = features[0]
    progress = features[1]
    login_streak = features[2]
    skip_fwd_ratio = features[3]
    note_ratio = features[5]
    avg_rate = features[6]

    if days_inactive >= 7:
        reasons.append(f"Không vào học {int(days_inactive)} ngày")
    elif days_inactive >= 3:
        reasons.append(f"Ít hoạt động ({int(days_inactive)} ngày không vào)")

    if progress < 20 and features[7] > 0.3:  # time_ratio > 0.3 (đã enroll > 9 ngày)
        reasons.append(f"Tiến độ rất thấp ({progress:.1f}%)")

    if login_streak == 0:
        reasons.append("Không có chuỗi đăng nhập liên tục")

    if skip_fwd_ratio > 0.15:
        reasons.append(f"Tỷ lệ tua nhanh cao ({skip_fwd_ratio:.0%})")

    if note_ratio == 0 and features[8] > 0:  # có activity nhưng không ghi chú
        reasons.append("Không có ghi chú nào")

    if avg_rate > 1.75:
        reasons.append(f"Thường xem ở tốc độ {avg_rate:.1f}x")

    return reasons


def get_model_status():
    """Trả về thông tin về model hiện tại."""
    if not os.path.exists(MODEL_PATH):
        return {
            "exists": False,
            "model_path": MODEL_PATH,
            "message": "Chưa có model. Hãy train model trước.",
        }

    import joblib
    from datetime import datetime

    mtime = os.path.getmtime(MODEL_PATH)
    trained_at = datetime.fromtimestamp(mtime).isoformat()

    model = joblib.load(MODEL_PATH)

    return {
        "exists": True,
        "model_path": MODEL_PATH,
        "trained_at": trained_at,
        "n_estimators": model.n_estimators,
        "n_features": model.n_features_in_,
        "feature_names": FEATURE_NAMES,
    }
