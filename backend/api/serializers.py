from rest_framework import serializers

from courses.models import Course, CourseEnrollment
from courses.serializers import CourseListSerializer, EnrollmentSerializer
from users.models import InstructorProfile, StudentProfile, User
from users.serializers import UserSerializer
from videos.models import VideoNote
from videos.serializers import VideoNoteSerializer
from .models import (
    AuditLog, Certificate, CourseReview, Discussion, LearningGoal,
    Notification, Report, SystemSetting, Wishlist,
)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "type", "title", "message", "data", "is_read", "created_at"]
        read_only_fields = ["id", "created_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.full_name", read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "actor", "actor_name", "action", "target_type", "target_id", "metadata", "created_at"]
        read_only_fields = fields


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ["id", "key", "value", "description", "updated_at"]
        read_only_fields = ["id", "updated_at"]


class AdminUserSerializer(serializers.ModelSerializer):
    instructor_status = serializers.SerializerMethodField()
    instructor_profile = serializers.SerializerMethodField()
    enrollments_count = serializers.IntegerField(read_only=True)
    courses_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "user_id", "email", "full_name", "avatar_url", "role", "is_active",
            "is_staff", "is_superuser", "is_email_verified", "instructor_status",
            "instructor_profile",
            "enrollments_count", "courses_count", "last_login_at", "created_at", "updated_at",
        ]
        read_only_fields = ["user_id", "email", "created_at", "updated_at"]

    def get_instructor_status(self, user):
        profile = getattr(user, "instructor_profile", None)
        if not profile:
            return "none"
        return "approved" if profile.is_verified and profile.is_active else "pending"

    def get_instructor_profile(self, user):
        profile = getattr(user, "instructor_profile", None)
        if not profile:
            return None
        return {
            "headline": profile.headline,
            "bio": profile.bio,
            "profile_url": profile.profile_url,
            "expertise": profile.expertise,
            "is_verified": profile.is_verified,
            "is_active": profile.is_active,
            "joined_as_instructor_at": profile.joined_as_instructor_at,
        }


class CourseModerationSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source="instructor.user.full_name", read_only=True)
    category_name = serializers.CharField(source="category.category_name", read_only=True)

    class Meta:
        model = Course
        fields = [
            "course_id", "course_name", "course_describes", "language", "level", "image_course",
            "intro_video", "status", "instructor_name", "category_name", "created_at", "updated_at",
        ]
        read_only_fields = ["course_id", "created_at", "updated_at"]


class WishlistSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(source="course", queryset=Course.objects.all(), write_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "course", "course_id", "created_at"]
        read_only_fields = ["id", "created_at"]


class CourseReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)

    class Meta:
        model = CourseReview
        fields = ["id", "course", "student_name", "rating", "comment", "is_hidden", "created_at", "updated_at"]
        read_only_fields = ["id", "course", "student_name", "is_hidden", "created_at", "updated_at"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating phải từ 1 đến 5.")
        return value


class CertificateSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.course_name", read_only=True)
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)

    class Meta:
        model = Certificate
        fields = ["id", "certificate_code", "student_name", "course", "course_name", "issued_at"]
        read_only_fields = fields


class LearningGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningGoal
        fields = ["id", "title", "target_date", "is_completed", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DiscussionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)
    replies_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Discussion
        fields = [
            "id", "course", "video", "user", "user_name", "user_role", "parent",
            "content", "is_hidden", "replies_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "user", "user_name", "user_role", "is_hidden", "replies_count", "created_at", "updated_at"]


class ReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source="reporter.full_name", read_only=True)

    class Meta:
        model = Report
        fields = ["id", "reporter_name", "target_type", "target_id", "reason", "status", "admin_note", "created_at", "updated_at"]
        read_only_fields = ["id", "reporter_name", "status", "admin_note", "created_at", "updated_at"]


class InstructorStudentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    student_email = serializers.EmailField(source="student.user.email", read_only=True)
    course_name = serializers.CharField(source="course.course_name", read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = [
            "id", "student", "student_name", "student_email", "course", "course_name", "status",
            "course_progress_percent", "total_watch_time_seconds", "videos_completed",
            "login_streak", "enrolled_at", "completed_at", "last_accessed_at", "updated_at",
        ]

