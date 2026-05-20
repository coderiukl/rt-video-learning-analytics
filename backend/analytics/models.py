from django.db import models

from courses.models import Course
from users.models import StudentProfile
from videos.models import Video


class LearningSession(models.Model):
    session_id = models.CharField(max_length=64, primary_key=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="learning_sessions")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="learning_sessions")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    active_seconds = models.PositiveIntegerField(default=0)
    idle_seconds = models.PositiveIntegerField(default=0)
    event_count = models.PositiveIntegerField(default=0)
    device_type = models.CharField(max_length=40, blank=True)
    browser = models.CharField(max_length=80, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_sessions"
        indexes = [
            models.Index(fields=["student", "course"]),
            models.Index(fields=["course", "started_at"]),
        ]
        ordering = ["-started_at"]


class LearningEvent(models.Model):
    class EventType(models.TextChoices):
        PLAY = "play", "Play"
        PAUSE = "pause", "Pause"
        ENDED = "ended", "Ended"
        SEEK = "seek", "Seek"
        SKIP_FORWARD_10 = "skip_forward_10", "Skip forward 10 seconds"
        SKIP_BACKWARD_10 = "skip_backward_10", "Skip backward 10 seconds"
        RATE_CHANGE = "rate_change", "Playback speed changed"
        NOTE_CREATED = "note_created", "Note created"
        NOTE_UPDATED = "note_updated", "Note updated"
        NOTE_DELETED = "note_deleted", "Note deleted"
        PROGRESS_SYNC = "progress_sync", "Progress synced"

    event_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="learning_events")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="learning_events")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="learning_events")
    event_type = models.CharField(max_length=40, choices=EventType.choices)
    position_seconds = models.PositiveIntegerField(default=0)
    from_seconds = models.PositiveIntegerField(null=True, blank=True)
    to_seconds = models.PositiveIntegerField(null=True, blank=True)
    delta_seconds = models.IntegerField(default=0)
    playback_rate = models.FloatField(null=True, blank=True)
    session = models.ForeignKey(LearningSession, null=True, blank=True, on_delete=models.SET_NULL, related_name="events")
    client_timestamp = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    is_tab_hidden = models.BooleanField(default=False)
    is_fullscreen = models.BooleanField(default=False)
    volume = models.FloatField(null=True, blank=True)
    muted = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "learning_events"
        indexes = [
            models.Index(fields=["course", "created_at"]),
            models.Index(fields=["video", "event_type"]),
            models.Index(fields=["student", "course"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student_id} {self.event_type} video={self.video_id}"
