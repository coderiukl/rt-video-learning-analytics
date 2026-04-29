from django.db import models

from courses.models import Course
from users.models import StudentProfile
from .storage import LargeVideoCloudinaryStorage


class Video(models.Model):
    video_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="videos")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_file = models.FileField(
        upload_to="LearnFlow/course_videos/%Y/%m/",
        storage=LargeVideoCloudinaryStorage(),
        blank=True,
        null=True,
        max_length=500,
    )
    video_url = models.URLField(blank=True, null=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=1)
    is_preview = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "videos"
        ordering = ["order", "created_at"]
        unique_together = [["course", "order"]]

    def __str__(self):
        return f"{self.course_id} - {self.order}. {self.title}"


class VideoNote(models.Model):
    note_id = models.AutoField(primary_key=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="notes")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="video_notes")
    timestamp_seconds = models.PositiveIntegerField(default=0)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "video_notes"
        ordering = ["timestamp_seconds", "created_at"]

    def __str__(self):
        return f"{self.student_id} @ {self.video_id}:{self.timestamp_seconds}"


class VideoProgress(models.Model):
    progress_id = models.AutoField(primary_key=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="progress_records")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="video_progress")
    watched_seconds = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_watched_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "video_progress"
        unique_together = [["student", "video"]]
        ordering = ["video__order", "created_at"]

    def __str__(self):
        return f"{self.student_id} -> {self.video_id}: {self.watched_seconds}s"
