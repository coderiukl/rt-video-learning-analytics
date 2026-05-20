from django.conf import settings
from django.db import models

from courses.models import Course, CourseEnrollment
from users.models import StudentProfile
from videos.models import Video


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs")
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80, blank=True)
    target_id = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]


class Notification(models.Model):
    class Type(models.TextChoices):
        SYSTEM = "system", "System"
        COURSE = "course", "Course"
        DROPOUT = "dropout", "Dropout"
        APPROVAL = "approval", "Approval"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=30, choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict, blank=True)
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_settings"


class Wishlist(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="wishlist_items")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wishlists"
        unique_together = [["student", "course"]]
        ordering = ["-created_at"]


class CourseReview(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="course_reviews")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "course_reviews"
        unique_together = [["student", "course"]]
        ordering = ["-created_at"]


class Certificate(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="certificates")
    enrollment = models.OneToOneField(CourseEnrollment, on_delete=models.CASCADE, related_name="certificate")
    certificate_code = models.CharField(max_length=64, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "certificates"
        unique_together = [["student", "course"]]
        ordering = ["-issued_at"]


class LearningGoal(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="goals")
    title = models.CharField(max_length=255)
    target_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_goals"
        ordering = ["is_completed", "target_date", "-created_at"]


class Discussion(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="discussions")
    video = models.ForeignKey(Video, null=True, blank=True, on_delete=models.CASCADE, related_name="discussions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="discussions")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    content = models.TextField()
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "discussions"
        ordering = ["created_at"]


class Report(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    target_type = models.CharField(max_length=50)
    target_id = models.CharField(max_length=80)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reports"
        ordering = ["-created_at"]

