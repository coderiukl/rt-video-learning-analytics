from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from .models import Video, VideoNote, VideoProgress


class VideoProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoProgress
        fields = [
            "progress_id", "video", "watched_seconds", "duration_seconds",
            "completed", "completed_at", "last_watched_at", "updated_at",
        ]
        read_only_fields = ["progress_id", "video", "completed_at", "last_watched_at", "updated_at"]

    def validate_watched_seconds(self, value):
        return max(0, int(value or 0))

    def validate_duration_seconds(self, value):
        return max(0, int(value or 0))


class VideoSerializer(serializers.ModelSerializer):
    video_src = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "video_id", "course", "title", "description", "video_file", "video_url",
            "video_src", "duration_seconds", "order", "is_preview", "is_published",
            "progress", "is_completed", "created_at", "updated_at",
        ]
        read_only_fields = ["course", "video_src", "progress", "is_completed", "created_at", "updated_at"]

    def get_video_src(self, obj):
        request = self.context.get("request")
        if obj.video_file:
            local_file = Path(settings.MEDIA_ROOT) / obj.video_file.name
            url = f"/api/videos/{obj.video_id}/stream/" if local_file.exists() else obj.video_file.url
            return request.build_absolute_uri(url) if request else url
        return obj.video_url

    def get_progress(self, obj):
        progress = self._get_student_progress(obj)
        if not progress:
            return None
        return VideoProgressSerializer(progress).data

    def get_is_completed(self, obj):
        progress = self._get_student_progress(obj)
        return bool(progress and progress.completed)

    def _get_student_progress(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        student = getattr(user, "student_profile", None)
        if not student:
            return None

        prefetched = getattr(obj, "_student_progress", None)
        if prefetched is not None:
            return prefetched[0] if prefetched else None

        return VideoProgress.objects.filter(video=obj, student=student).first()

    def validate(self, attrs):
        video_file = attrs.get("video_file") or getattr(self.instance, "video_file", None)
        video_url = attrs.get("video_url") or getattr(self.instance, "video_url", None)
        if not video_file and not video_url:
            raise serializers.ValidationError("Vui long upload file video hoac nhap URL video.")
        return attrs


class VideoNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoNote
        fields = ["note_id", "video", "timestamp_seconds", "content", "created_at", "updated_at"]
        read_only_fields = ["video", "created_at", "updated_at"]

    def validate_content(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Noi dung ghi chu khong duoc trong.")
        return value
