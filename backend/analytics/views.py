from datetime import timedelta

from django.db.models import Count, Max, Q
from django.utils import timezone
from prometheus_client import Counter, Histogram
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course, CourseEnrollment
from courses.views import get_instructor_profile, get_student_profile, is_approved_instructor
from videos.models import Video
from .models import LearningEvent, LearningSession
from .ml_engine import compute_engagement_score, get_engagement_label, compute_risk_score, compute_video_heatmap
from .services.dropout_service import predict as predict_dropout, model_status as get_model_status, reload as reload_dropout_model
from .learning_style import cluster_learning_styles
from .recommender import recommend_courses_for_student, recommend_courses_for_student_global

DROPOUT_PREDICTIONS = Counter(
    "ml_dropout_predictions_total",
    "Dropout prediction count by risk level",
    ["risk_level"],
)
RECOMMENDATION_LATENCY = Histogram(
    "ml_recommendation_duration_seconds",
    "Course recommendation API latency",
)
LEARNING_EVENTS = Counter(
    "learning_events_total",
    "Learning event count by event type",
    ["event_type"],
)


def is_admin(user):
    return user.is_staff or user.role == "admin"


def can_view_course_behavior(user, course):
    if is_admin(user):
        return True
    return is_approved_instructor(user) and course.instructor.user_id == user.user_id


def int_or_zero(value):
    try:
        return max(0, int(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def bool_or_false(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def parse_client_timestamp(value):
    if not value:
        return None
    try:
        from django.utils.dateparse import parse_datetime
        parsed = parse_datetime(value)
        return parsed if parsed and timezone.is_aware(parsed) else timezone.make_aware(parsed) if parsed else None
    except (TypeError, ValueError):
        return None


def serialize_event(event):
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "course_id": event.course_id,
        "course_name": event.course.course_name,
        "video_id": event.video_id,
        "video_title": event.video.title,
        "student_id": str(event.student_id),
        "student_name": event.student.user.full_name,
        "student_email": event.student.user.email,
        "position_seconds": event.position_seconds,
        "from_seconds": event.from_seconds,
        "to_seconds": event.to_seconds,
        "delta_seconds": event.delta_seconds,
        "playback_rate": event.playback_rate,
        "session_id": event.session_id,
        "client_timestamp": event.client_timestamp,
        "duration_ms": event.duration_ms,
        "is_tab_hidden": event.is_tab_hidden,
        "is_fullscreen": event.is_fullscreen,
        "volume": event.volume,
        "muted": event.muted,
        "metadata": event.metadata,
        "created_at": event.created_at,
    }


def build_behavior_payload(events, courses):
    events = events.select_related("student__user", "course", "video")
    event_counts = {
        row["event_type"]: row["total"]
        for row in events.values("event_type").annotate(total=Count("event_id"))
    }
    video_rows = events.values("video_id", "video__title").annotate(
        total_events=Count("event_id"),
        last_event_at=Max("created_at"),
    ).order_by("-total_events")[:50]
    student_rows = events.values(
        "student_id", "student__user__full_name", "student__user__email"
    ).annotate(
        total_events=Count("event_id"),
        last_event_at=Max("created_at"),
        skips_forward=Count("event_id", filter=Q(event_type=LearningEvent.EventType.SKIP_FORWARD_10)),
        skips_backward=Count("event_id", filter=Q(event_type=LearningEvent.EventType.SKIP_BACKWARD_10)),
        notes=Count("event_id", filter=Q(event_type__in=[
            LearningEvent.EventType.NOTE_CREATED,
            LearningEvent.EventType.NOTE_UPDATED,
            LearningEvent.EventType.NOTE_DELETED,
        ])),
    ).order_by("-total_events")[:100]

    recent_events = [serialize_event(event) for event in events.order_by("-created_at")[:100]]

    return {
        "summary": {
            "course_count": courses.count(),
            "event_count": events.count(),
            "student_count": events.values("student_id").distinct().count(),
            "video_count": events.values("video_id").distinct().count(),
            "play_count": event_counts.get(LearningEvent.EventType.PLAY, 0),
            "pause_count": event_counts.get(LearningEvent.EventType.PAUSE, 0),
            "seek_count": event_counts.get(LearningEvent.EventType.SEEK, 0),
            "skip_forward_10_count": event_counts.get(LearningEvent.EventType.SKIP_FORWARD_10, 0),
            "skip_backward_10_count": event_counts.get(LearningEvent.EventType.SKIP_BACKWARD_10, 0),
            "note_event_count": sum(event_counts.get(key, 0) for key in [
                LearningEvent.EventType.NOTE_CREATED,
                LearningEvent.EventType.NOTE_UPDATED,
                LearningEvent.EventType.NOTE_DELETED,
            ]),
            "hidden_tab_event_count": events.filter(is_tab_hidden=True).count(),
            "muted_event_count": events.filter(muted=True).count(),
            "fullscreen_event_count": events.filter(is_fullscreen=True).count(),
        },
        "event_counts": event_counts,
        "videos": [
            {
                "video_id": row["video_id"],
                "video_title": row["video__title"],
                "total_events": row["total_events"],
                "last_event_at": row["last_event_at"],
            }
            for row in video_rows
        ],
        "students": [
            {
                "student_id": str(row["student_id"]),
                "student_name": row["student__user__full_name"],
                "student_email": row["student__user__email"],
                "total_events": row["total_events"],
                "skips_forward": row["skips_forward"],
                "skips_backward": row["skips_backward"],
                "notes": row["notes"],
                "last_event_at": row["last_event_at"],
            }
            for row in student_rows
        ],
        "recent_events": recent_events,
    }


class LearningEventCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student = get_student_profile(request.user)
        if not student:
            return Response({"error": "Chi student moi co the ghi nhan hanh vi hoc tap."}, status=status.HTTP_403_FORBIDDEN)

        video_id = request.data.get("video")
        try:
            video = Video.objects.select_related("course").get(video_id=video_id, is_published=True)
        except Video.DoesNotExist:
            return Response({"error": "Video khong ton tai."}, status=status.HTTP_404_NOT_FOUND)

        if not CourseEnrollment.objects.filter(student=student, course=video.course).exists():
            return Response({"error": "Ban chua dang ky khoa hoc nay."}, status=status.HTTP_403_FORBIDDEN)

        event_type = request.data.get("event_type")
        valid_types = {choice[0] for choice in LearningEvent.EventType.choices}
        if event_type not in valid_types:
            return Response({"error": "event_type khong hop le."}, status=status.HTTP_400_BAD_REQUEST)

        session = None
        session_id = request.data.get("session_id")
        if session_id:
            meta = request.data.get("metadata") or {}
            session, _ = LearningSession.objects.get_or_create(
                session_id=session_id,
                defaults={
                    "student": student,
                    "course": video.course,
                    "started_at": timezone.now(),
                    "device_type": meta.get("device_type", ""),
                    "browser": meta.get("browser", ""),
                    "user_agent": meta.get("user_agent", ""),
                },
            )

        event = LearningEvent.objects.create(
            student=student,
            course=video.course,
            video=video,
            event_type=event_type,
            position_seconds=int_or_zero(request.data.get("position_seconds")),
            from_seconds=int_or_zero(request.data.get("from_seconds")) if request.data.get("from_seconds") is not None else None,
            to_seconds=int_or_zero(request.data.get("to_seconds")) if request.data.get("to_seconds") is not None else None,
            delta_seconds=int(request.data.get("delta_seconds") or 0),
            playback_rate=float_or_none(request.data.get("playback_rate")),
            session=session,
            client_timestamp=parse_client_timestamp(request.data.get("client_timestamp")),
            duration_ms=int_or_zero(request.data.get("duration_ms")),
            is_tab_hidden=bool_or_false(request.data.get("is_tab_hidden")),
            is_fullscreen=bool_or_false(request.data.get("is_fullscreen")),
            volume=float_or_none(request.data.get("volume")),
            muted=bool_or_false(request.data.get("muted")),
            metadata=request.data.get("metadata") or {},
        )
        LEARNING_EVENTS.labels(event_type=event_type).inc()

        if session:
            session.event_count = session.events.count()
            active_seconds = int_or_zero((request.data.get("metadata") or {}).get("active_seconds"))
            idle_seconds = int_or_zero((request.data.get("metadata") or {}).get("idle_seconds"))
            if active_seconds:
                session.active_seconds = max(session.active_seconds, active_seconds)
            if idle_seconds:
                session.idle_seconds = max(session.idle_seconds, idle_seconds)
            if event_type in {LearningEvent.EventType.PAUSE, LearningEvent.EventType.ENDED, LearningEvent.EventType.PROGRESS_SYNC}:
                session.ended_at = timezone.now()
            session.save(update_fields=["event_count", "active_seconds", "idle_seconds", "ended_at", "updated_at"])
        
        # Cập nhật ngay lập tức last_accessed_at để bảng At-Risk không báo lỗi "Chưa từng truy cập"
        CourseEnrollment.objects.filter(student=student, course=video.course).update(last_accessed_at=timezone.now())

        engagement_score = compute_engagement_score(student, video)
        response_data = serialize_event(event)
        response_data["engagement_score"] = engagement_score
        response_data["engagement_label"] = get_engagement_label(engagement_score)
        return Response(response_data, status=status.HTTP_201_CREATED)


class CourseBehaviorAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = Course.objects.select_related("instructor__user").get(course_id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Khoa hoc khong ton tai."}, status=status.HTTP_404_NOT_FOUND)

        if not can_view_course_behavior(request.user, course):
            return Response({"error": "Ban khong co quyen xem analytics cua khoa hoc nay."}, status=status.HTTP_403_FORBIDDEN)

        events = LearningEvent.objects.filter(course=course)
        return Response(build_behavior_payload(events, Course.objects.filter(course_id=course_id)))


class InstructorBehaviorAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_approved_instructor(request.user):
            return Response({"error": "Chi instructor da duoc duyet moi co quyen xem analytics."}, status=status.HTTP_403_FORBIDDEN)

        instructor = get_instructor_profile(request.user)
        courses = Course.objects.filter(instructor=instructor)
        events = LearningEvent.objects.filter(course__in=courses)
        return Response(build_behavior_payload(events, courses))


class AdminBehaviorAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_admin(request.user):
            return Response({"error": "Chi admin moi co quyen xem toan bo analytics."}, status=status.HTTP_403_FORBIDDEN)

        events = LearningEvent.objects.all()
        course_id = request.query_params.get("course")
        if course_id:
            events = events.filter(course_id=course_id)
            courses = Course.objects.filter(course_id=course_id)
        else:
            courses = Course.objects.all()
        return Response(build_behavior_payload(events, courses))


class AtRiskStudentsView(APIView):
    """GET /api/analytics/courses/{course_id}/at-risk/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(course_id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Khóa học không tồn tại."}, status=404)

        if not can_view_course_behavior(request.user, course):
            return Response({"error": "Không có quyền."}, status=403)

        now = timezone.now()
        recent_cutoff = now - timedelta(days=30)

        enrollments = CourseEnrollment.objects.filter(
            course=course, status=CourseEnrollment.Status.ACTIVE
        ).select_related("student__user")

        results = []
        model_type_used = None

        for enrollment in enrollments:
            # Query events 30 ngày cho student này
            events_30d = LearningEvent.objects.filter(
                student=enrollment.student,
                course=course,
                created_at__gte=recent_cutoff,
            )
            # Dùng predict_dropout (RF nếu có model, fallback rule-based)
            risk_data = predict_dropout(enrollment, events_30d)
            model_type_used = risk_data.get("model_type", "rule-based")
            DROPOUT_PREDICTIONS.labels(
                risk_level=risk_data.get("risk_level", "unknown")
            ).inc()

            results.append({
                "student_id": str(enrollment.student_id),
                "student_name": enrollment.student.user.full_name,
                "student_email": enrollment.student.user.email,
                "course_progress_percent": enrollment.course_progress_percent,
                "days_enrolled": (now - enrollment.enrolled_at).days,
                "last_accessed_at": enrollment.last_accessed_at,
                **risk_data,
            })

        results.sort(key=lambda x: x["risk_score"], reverse=True)

        return Response({
            "course_id": course_id,
            "course_name": course.course_name,
            "total_active_students": len(results),
            "high_risk_count": sum(1 for r in results if r["risk_level"] == "high"),
            "model_type": model_type_used or "rule-based",
            "students": results,
        })


class DropoutModelReloadView(APIView):
    """POST /api/analytics/dropout-model/reload/

    Training happens offline (DVC/CI). This endpoint only clears the in-process
    model cache so the next prediction picks up a freshly promoted version
    from the registry.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not (is_admin(request.user) or is_approved_instructor(request.user)):
            return Response(
                {"error": "Chỉ admin hoặc instructor mới có quyền reload model."},
                status=403,
            )

        reload_dropout_model()
        return Response(
            {
                "status": "ok",
                "message": "Model cache đã được xóa. Lần predict kế tiếp sẽ load lại từ registry.",
            },
            status=200,
        )


class DropoutModelStatusView(APIView):
    """GET /api/analytics/dropout-model/status/ — model info"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (is_admin(request.user) or is_approved_instructor(request.user)):
            return Response(
                {"error": "Không có quyền."},
                status=403,
            )

        model_status = get_model_status()
        return Response(model_status, status=200)


from videos.models import Video as VideoModel

class VideoHeatmapView(APIView):
    """GET /api/analytics/videos/{video_id}/heatmap/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, video_id):
        try:
            video = VideoModel.objects.select_related(
                "course__instructor__user"
            ).get(video_id=video_id)
        except VideoModel.DoesNotExist:
            return Response({"error": "Video không tồn tại."}, status=404)

        if not can_view_course_behavior(request.user, video.course):
            return Response({"error": "Không có quyền."}, status=403)

        segment_size = int(request.query_params.get("segment_size", 30))
        heatmap = compute_video_heatmap(video, segment_size=segment_size)
        hard_segments = [s for s in heatmap if s["difficulty_label"] == "hard"]

        return Response({
            "video_id": video_id,
            "video_title": video.title,
            "duration_seconds": video.duration_seconds,
            "segment_size_seconds": segment_size,
            "total_segments_analyzed": len(heatmap),
            "hard_segment_count": len(hard_segments),
            "hardest_segments": heatmap[:5],
            "full_heatmap": heatmap,
        })


class LearningStyleView(APIView):
    """GET /api/analytics/courses/{course_id}/learning-styles/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(course_id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Khóa học không tồn tại."}, status=404)

        if not can_view_course_behavior(request.user, course):
            return Response({"error": "Không có quyền."}, status=403)

        data = cluster_learning_styles(course)
        
        return Response(data, status=200)


class CourseRecommendationView(APIView):
    """GET /api/analytics/courses/{course_id}/recommendations/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(course_id=course_id, status=Course.Status.PUBLISHED)
        except Course.DoesNotExist:
            return Response({"error": "Khóa học không tồn tại hoặc chưa được xuất bản."}, status=404)

        student = get_student_profile(request.user)
        # Bất kỳ ai cũng có thể xem gợi ý, nhưng lọc bỏ course đã enroll thì cần truyền student.
        # Nếu không phải student (chưa có profile), sẽ truyền None.

        with RECOMMENDATION_LATENCY.time():
            recommendations = recommend_courses_for_student(student, course.course_id)

        return Response({
            "course_id": course_id,
            "recommendations": recommendations
        })

class PersonalizedCourseRecommendationView(APIView):
    """GET /api/analytics/courses/personalized-recommendations/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = get_student_profile(request.user)
        if not student:
            return Response({"error": "Chỉ sinh viên mới có thể nhận gợi ý cá nhân hóa."}, status=403)

        with RECOMMENDATION_LATENCY.time():
            recommendations = recommend_courses_for_student_global(student, n=4)

        return Response({
            "recommendations": recommendations
        })
