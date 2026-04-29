from django.contrib import admin

from .models import Video, VideoNote, VideoProgress


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("video_id", "title", "course", "order", "is_published", "is_preview", "created_at")
    list_filter = ("is_published", "is_preview")
    search_fields = ("title", "course__course_name")
    ordering = ("course", "order")


@admin.register(VideoNote)
class VideoNoteAdmin(admin.ModelAdmin):
    list_display = ("note_id", "video", "student", "timestamp_seconds", "created_at")
    search_fields = ("content", "video__title", "student__user__email", "student__user__full_name")
    ordering = ("video", "timestamp_seconds")


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = (
        "progress_id", "video", "student", "watched_seconds",
        "duration_seconds", "completed", "completed_at", "last_watched_at",
    )
    list_filter = ("completed",)
    search_fields = ("video__title", "student__user__email", "student__user__full_name")
    ordering = ("video", "student")
