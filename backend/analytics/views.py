from django.db.models import Count, Max, Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course, CourseEnrollment
from courses.views import get_instructor_profile, get_student_profile, is_approved_instructor
from videos.models import Video
from .models import LearningEvent


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
            metadata=request.data.get("metadata") or {},
        )
        return Response(serialize_event(event), status=status.HTTP_201_CREATED)


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
