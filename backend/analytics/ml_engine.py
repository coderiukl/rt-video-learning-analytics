from .models import LearningEvent

WEIGHTS = {
    "skip_forward_10": -8,
    "rate_change_fast": -5,
    "skip_backward_10": +5,
    "note_created": +10,
    "ended": +15,
}


def compute_engagement_score(student, video, last_n_events=20):
    """Tính điểm tập trung [0.0, 100.0] dựa vào N event gần nhất."""
    events = LearningEvent.objects.filter(
        student=student, video=video
    ).order_by("-created_at")[:last_n_events]

    score = 70.0

    for event in events:
        etype = event.event_type
        if etype == LearningEvent.EventType.SKIP_FORWARD_10:
            score += WEIGHTS["skip_forward_10"]
        elif etype == LearningEvent.EventType.SKIP_BACKWARD_10:
            score += WEIGHTS["skip_backward_10"]
        elif etype == LearningEvent.EventType.NOTE_CREATED:
            score += WEIGHTS["note_created"]
        elif etype == LearningEvent.EventType.ENDED:
            score += WEIGHTS["ended"]
        elif etype == LearningEvent.EventType.RATE_CHANGE:
            if event.playback_rate and event.playback_rate > 1.5:
                score += WEIGHTS["rate_change_fast"]

    return round(max(0.0, min(100.0, score)), 1)


def get_engagement_label(score):
    if score >= 75:
        return "high"
    elif score >= 45:
        return "medium"
    return "low"


from django.utils import timezone
from datetime import timedelta
from courses.models import CourseEnrollment


def compute_risk_score(student, course):
    """
    Tính điểm nguy cơ bỏ học [0, 100].
    Returns: {"risk_score": float, "risk_level": str, "reasons": list}
    """
    risk_score = 0.0
    reasons = []

    try:
        enrollment = CourseEnrollment.objects.get(student=student, course=course)
    except CourseEnrollment.DoesNotExist:
        return {"risk_score": 0.0, "risk_level": "low", "reasons": []}

    # 1. Số ngày không vào học
    if enrollment.last_accessed_at:
        days_inactive = (timezone.now() - enrollment.last_accessed_at).days
        risk_score += min(days_inactive * 5, 50)
        if days_inactive >= 3:
            reasons.append(f"Không vào học {days_inactive} ngày")
    else:
        risk_score += 30
        reasons.append("Chưa từng truy cập khóa học")

    # 2. Tiến độ thấp
    enrolled_days = (timezone.now() - enrollment.enrolled_at).days
    if enrolled_days >= 7 and enrollment.course_progress_percent < 20:
        risk_score += 20
        reasons.append(
            f"Tiến độ {enrollment.course_progress_percent:.1f}% sau {enrolled_days} ngày"
        )

    # 3. Login streak
    if enrollment.login_streak == 0:
        risk_score += 15
        reasons.append("Không có chuỗi đăng nhập liên tục")

    # 4. Phân tích hành vi 30 ngày gần nhất
    recent_cutoff = timezone.now() - timedelta(days=30)
    events = LearningEvent.objects.filter(
        student=student, course=course, created_at__gte=recent_cutoff
    )
    total_events = events.count()

    if total_events > 0:
        skip_count = events.filter(
            event_type=LearningEvent.EventType.SKIP_FORWARD_10
        ).count()
        if skip_count / total_events > 0.15:  # Giảm ngưỡng phạt xuống 15% để nhạy cảm hơn
            risk_score += 20
            reasons.append(f"Tỷ lệ tua nhanh bỏ qua nội dung quá cao ({skip_count/total_events:.0%})")

        rate_events = list(events.exclude(playback_rate__isnull=True))
        if rate_events:
            avg_rate = sum(e.playback_rate for e in rate_events) / len(rate_events)
            if avg_rate > 1.75:
                risk_score += 10
                reasons.append(f"Thường xem ở tốc độ {avg_rate:.1f}x")

        note_count = events.filter(
            event_type=LearningEvent.EventType.NOTE_CREATED
        ).count()
        if note_count == 0:
            risk_score += 10
            reasons.append("Không có ghi chú nào")

    risk_score = min(100.0, round(risk_score, 1))
    if risk_score >= 70:
        risk_level = "high"
    elif risk_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {"risk_score": risk_score, "risk_level": risk_level, "reasons": reasons}


from collections import defaultdict


def compute_video_heatmap(video, segment_size=30):
    """
    Tính heatmap độ khó theo segment của video.
    Trả về list segments sắp xếp theo intensity giảm dần.
    """
    DIFFICULTY_EVENTS = [
        LearningEvent.EventType.SKIP_BACKWARD_10,
        LearningEvent.EventType.SEEK,
        LearningEvent.EventType.PAUSE,
    ]
    events = LearningEvent.objects.filter(
        video=video,
        event_type__in=DIFFICULTY_EVENTS
    ).values("event_type", "position_seconds", "from_seconds", "to_seconds")

    segment_counts = defaultdict(int)
    seek_back_bonus = defaultdict(int)

    for e in events:
        position = e["position_seconds"] or 0
        seg_idx = position // segment_size
        segment_counts[seg_idx] += 1

        if e["event_type"] == LearningEvent.EventType.SEEK:
            from_s = e["from_seconds"] or 0
            to_s = e["to_seconds"] or 0
            if to_s < from_s:  # Tua lùi — trọng số cao hơn
                seek_back_bonus[seg_idx] += 2

    all_segs = set(segment_counts.keys()) | set(seek_back_bonus.keys())
    if not all_segs:
        return []

    heatmap = []
    max_count = 1
    for seg_id in sorted(all_segs):
        total = segment_counts[seg_id] + seek_back_bonus[seg_id]
        max_count = max(max_count, total)
        heatmap.append({
            "segment_index": seg_id,
            "start_seconds": seg_id * segment_size,
            "end_seconds": (seg_id + 1) * segment_size,
            "difficulty_count": total,
            "seek_back_count": seek_back_bonus[seg_id],
        })

    for seg in heatmap:
        seg["intensity"] = round(seg["difficulty_count"] / max_count, 2)
        if seg["intensity"] >= 0.7:
            seg["difficulty_label"] = "hard"
        elif seg["intensity"] >= 0.35:
            seg["difficulty_label"] = "medium"
        else:
            seg["difficulty_label"] = "easy"

    return sorted(heatmap, key=lambda x: x["intensity"], reverse=True)

