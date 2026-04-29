import mimetypes
import os
import re

from django.db.models import Prefetch
from django.http import FileResponse, Http404, HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course, CourseEnrollment
from courses.views import get_student_profile, is_approved_instructor
from analytics.models import LearningEvent
from .models import Video, VideoNote, VideoProgress
from .serializers import VideoNoteSerializer, VideoProgressSerializer, VideoSerializer


def get_course_for_user(course_id, user):
    try:
        course = Course.objects.select_related("instructor__user").get(course_id=course_id)
    except Course.DoesNotExist:
        return None, Response({"error": "Khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

    if is_approved_instructor(user) and course.instructor.user_id == user.user_id:
        return course, None

    student = get_student_profile(user)
    if student and CourseEnrollment.objects.filter(student=student, course=course).exists():
        return course, None

    return None, Response({"error": "Bạn không có quyền xem video của khóa học này."}, status=status.HTTP_403_FORBIDDEN)


def get_owned_course(course_id, user):
    course, err = get_course_for_user(course_id, user)
    if err:
        return None, err

    if not (is_approved_instructor(user) and course.instructor.user_id == user.user_id):
        return None, Response({"error": "Chỉ giảng viên sở hữu khóa học mới được quản lý video."}, status=status.HTTP_403_FORBIDDEN)

    return course, None


class CourseVideoListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, course_id):
        course, err = get_course_for_user(course_id, request.user)
        if err:
            return err

        videos = course.videos.all()
        if not (is_approved_instructor(request.user) and course.instructor.user_id == request.user.user_id):
            videos = videos.filter(is_published=True)
            student = get_student_profile(request.user)
            if student:
                videos = videos.prefetch_related(
                    Prefetch(
                        "progress_records",
                        queryset=VideoProgress.objects.filter(student=student),
                        to_attr="_student_progress",
                    )
                )

        return Response(VideoSerializer(videos, many=True, context={"request": request}).data)

    def post(self, request, course_id):
        course, err = get_owned_course(course_id, request.user)
        if err:
            return err

        serializer = VideoSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        video = serializer.save(course=course)
        return Response(VideoSerializer(video, context={"request": request}).data, status=status.HTTP_201_CREATED)


class VideoManageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_video(self, video_id, user):
        try:
            video = Video.objects.select_related("course__instructor__user").get(video_id=video_id)
        except Video.DoesNotExist:
            return None, Response({"error": "Video không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        if not (is_approved_instructor(user) and video.course.instructor.user_id == user.user_id):
            return None, Response({"error": "Bạn không có quyền quản lý video này."}, status=status.HTTP_403_FORBIDDEN)

        return video, None

    def put(self, request, video_id):
        video, err = self.get_video(video_id, request.user)
        if err:
            return err

        serializer = VideoSerializer(video, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        video = serializer.save()
        return Response(VideoSerializer(video, context={"request": request}).data)

    def delete(self, request, video_id):
        video, err = self.get_video(video_id, request.user)
        if err:
            return err

        video.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VideoStreamView(APIView):
    # Uploaded media files are already public via /media/ in development.
    # This endpoint adds byte-range support so the browser can seek.
    permission_classes = [AllowAny]

    def get(self, request, video_id):
        try:
            video = Video.objects.get(video_id=video_id)
        except Video.DoesNotExist:
            raise Http404("Video không tồn tại.")

        if not video.video_file:
            raise Http404("Video không có file upload.")

        file_path = video.video_file.path
        file_size = os.path.getsize(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or "video/mp4"
        range_header = request.headers.get("Range", "").strip()

        if not range_header:
            response = FileResponse(open(file_path, "rb"), content_type=content_type)
            response["Accept-Ranges"] = "bytes"
            response["Content-Length"] = str(file_size)
            return response

        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if not match:
            return HttpResponse(status=416)

        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else file_size - 1
        end = min(end, file_size - 1)
        length = end - start + 1

        with open(file_path, "rb") as file:
            file.seek(start)
            data = file.read(length)

        response = HttpResponse(data, status=206, content_type=content_type)
        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response["Accept-Ranges"] = "bytes"
        response["Content-Length"] = str(length)
        return response


def get_video_for_student(video_id, user):
    try:
        video = Video.objects.select_related("course").get(video_id=video_id)
    except Video.DoesNotExist:
        return None, None, Response({"error": "Video không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

    student = get_student_profile(user)
    if not student:
        return None, None, Response({"error": "Không tìm thấy hồ sơ học viên."}, status=status.HTTP_403_FORBIDDEN)

    if not CourseEnrollment.objects.filter(student=student, course=video.course).exists():
        return None, None, Response({"error": "Bạn chưa đăng ký khóa học này."}, status=status.HTTP_403_FORBIDDEN)

    return video, student, None


def refresh_course_enrollment_progress(student, course):
    enrollment = CourseEnrollment.objects.filter(student=student, course=course).first()
    if not enrollment:
        return None

    published_videos = Video.objects.filter(course=course, is_published=True)
    total_videos = published_videos.count()
    completed_videos = VideoProgress.objects.filter(
        student=student,
        video__course=course,
        video__is_published=True,
        completed=True,
    ).count()
    total_watch_time = VideoProgress.objects.filter(
        student=student,
        video__course=course,
        video__is_published=True,
    )

    enrollment.videos_completed = completed_videos
    enrollment.total_watch_time_seconds = sum(progress.watched_seconds for progress in total_watch_time)
    enrollment.course_progress_percent = round((completed_videos / total_videos) * 100, 1) if total_videos else 0
    enrollment.last_accessed_at = timezone.now()

    if total_videos and completed_videos >= total_videos:
        enrollment.status = CourseEnrollment.Status.COMPLETED
        if not enrollment.completed_at:
            enrollment.completed_at = timezone.now()
    elif enrollment.status == CourseEnrollment.Status.COMPLETED:
        enrollment.status = CourseEnrollment.Status.ACTIVE
        enrollment.completed_at = None

    enrollment.save(update_fields=[
        "videos_completed", "total_watch_time_seconds", "course_progress_percent",
        "last_accessed_at", "status", "completed_at", "updated_at",
    ])
    return enrollment


class VideoProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, video_id):
        video, student, err = get_video_for_student(video_id, request.user)
        if err:
            return err

        progress, _ = VideoProgress.objects.get_or_create(video=video, student=student)
        return Response(VideoProgressSerializer(progress).data)

    def post(self, request, video_id):
        video, student, err = get_video_for_student(video_id, request.user)
        if err:
            return err

        progress, _ = VideoProgress.objects.get_or_create(video=video, student=student)
        serializer = VideoProgressSerializer(progress, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        watched_seconds = max(
            progress.watched_seconds,
            serializer.validated_data.get("watched_seconds", progress.watched_seconds),
        )
        duration_seconds = serializer.validated_data.get("duration_seconds", progress.duration_seconds)
        if not duration_seconds:
            duration_seconds = video.duration_seconds or progress.duration_seconds

        requested_completed = bool(serializer.validated_data.get("completed", False))
        reached_threshold = bool(duration_seconds and watched_seconds >= duration_seconds * 0.9)
        completed = progress.completed or requested_completed or reached_threshold

        progress.watched_seconds = watched_seconds
        progress.duration_seconds = duration_seconds
        progress.last_watched_at = timezone.now()
        if completed and not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
        progress.save()

        enrollment = refresh_course_enrollment_progress(student, video.course)
        data = VideoProgressSerializer(progress).data
        if enrollment:
            data["enrollment"] = {
                "course_progress_percent": enrollment.course_progress_percent,
                "videos_completed": enrollment.videos_completed,
                "status": enrollment.status,
                "completed_at": enrollment.completed_at,
            }
        return Response(data)


class VideoNoteListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, video_id):
        video, student, err = get_video_for_student(video_id, request.user)
        if err:
            return err

        notes = VideoNote.objects.filter(video=video, student=student)
        return Response(VideoNoteSerializer(notes, many=True).data)

    def post(self, request, video_id):
        video, student, err = get_video_for_student(video_id, request.user)
        if err:
            return err

        serializer = VideoNoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        note = serializer.save(video=video, student=student)
        LearningEvent.objects.create(
            student=student,
            course=video.course,
            video=video,
            event_type=LearningEvent.EventType.NOTE_CREATED,
            position_seconds=note.timestamp_seconds,
            metadata={"note_id": note.note_id},
        )
        return Response(VideoNoteSerializer(note).data, status=status.HTTP_201_CREATED)


class VideoNoteManageView(APIView):
    permission_classes = [IsAuthenticated]

    def get_note(self, note_id, user):
        try:
            note = VideoNote.objects.select_related("student__user").get(note_id=note_id)
        except VideoNote.DoesNotExist:
            return None, Response({"error": "Ghi chú không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        if note.student.user_id != user.user_id:
            return None, Response({"error": "Bạn không có quyền sửa ghi chú này."}, status=status.HTTP_403_FORBIDDEN)

        return note, None

    def put(self, request, note_id):
        note, err = self.get_note(note_id, request.user)
        if err:
            return err

        serializer = VideoNoteSerializer(note, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        note = serializer.save()
        LearningEvent.objects.create(
            student=note.student,
            course=note.video.course,
            video=note.video,
            event_type=LearningEvent.EventType.NOTE_UPDATED,
            position_seconds=note.timestamp_seconds,
            metadata={"note_id": note.note_id},
        )
        return Response(VideoNoteSerializer(note).data)

    def delete(self, request, note_id):
        note, err = self.get_note(note_id, request.user)
        if err:
            return err

        LearningEvent.objects.create(
            student=note.student,
            course=note.video.course,
            video=note.video,
            event_type=LearningEvent.EventType.NOTE_DELETED,
            position_seconds=note.timestamp_seconds,
            metadata={"note_id": note.note_id},
        )
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
