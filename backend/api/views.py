from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course
from users.models import InstructorProfile, StudentProfile, User


def can_access_admin(user):
    return user.is_authenticated and (user.is_staff or user.role == User.Role.ADMIN)


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not can_access_admin(request.user):
            return Response({"error": "Bạn không có quyền truy cập trang quản trị."}, status=403)

        user_search = request.query_params.get("user_search", "").strip()
        user_sort = request.query_params.get("user_sort", "name")
        course_search = request.query_params.get("course_search", "").strip()
        course_sort = request.query_params.get("course_sort", "-created_at")

        student_profiles = StudentProfile.objects.select_related("user").annotate(
            enrollment_count=Count("enrollments", distinct=True)
        )
        instructor_profiles = InstructorProfile.objects.select_related("user").annotate(
            course_count=Count("courses", distinct=True)
        )
        courses = Course.objects.select_related("instructor__user", "category", "category_sub").annotate(
            enrollment_count=Count("enrollments", distinct=True)
        )

        if user_search:
            user_filter = Q(user__full_name__icontains=user_search) | Q(user__email__icontains=user_search)
            student_profiles = student_profiles.filter(user_filter)
            instructor_profiles = instructor_profiles.filter(user_filter)

        if course_search:
            courses = courses.filter(
                Q(course_name__icontains=course_search)
                | Q(instructor__user__full_name__icontains=course_search)
                | Q(category__category_name__icontains=course_search)
                | Q(category_sub__category_name__icontains=course_search)
            )

        user_sort_map = {
            "name": "user__full_name",
            "-name": "-user__full_name",
            "created": "user__created_at",
            "-created": "-user__created_at",
            "courses": "course_count",
            "-courses": "-course_count",
            "enrollments": "enrollment_count",
            "-enrollments": "-enrollment_count",
        }
        student_sort = user_sort_map.get(user_sort, "user__full_name")
        instructor_sort = user_sort_map.get(user_sort, "user__full_name")
        if "course_count" in student_sort:
            student_sort = "user__full_name"
        if "enrollment_count" in instructor_sort:
            instructor_sort = "user__full_name"

        course_sort_map = {
            "name": "course_name",
            "-name": "-course_name",
            "created": "created_at",
            "-created": "-created_at",
            "students": "enrollment_count",
            "-students": "-enrollment_count",
            "status": "status",
            "-status": "-status",
        }
        courses = courses.order_by(course_sort_map.get(course_sort, "-created_at"))

        total_users = User.objects.exclude(role=User.Role.ADMIN).count()
        total_students = User.objects.filter(role=User.Role.STUDENT).count()
        total_instructors = User.objects.filter(role=User.Role.INSTRUCTOR).count()

        return Response({
            "stats": {
                "total_users": total_users,
                "total_students": total_students,
                "total_instructors": total_instructors,
                "pending_instructors": InstructorProfile.objects.filter(is_verified=False).count(),
                "total_courses": Course.objects.count(),
                "published_courses": Course.objects.filter(status=Course.Status.PUBLISHED).count(),
                "draft_courses": Course.objects.filter(status=Course.Status.DRAFT).count(),
                "archived_courses": Course.objects.filter(status=Course.Status.ARCHIVED).count(),
            },
            "students": [
                {
                    "user_id": str(profile.user.user_id),
                    "full_name": profile.user.full_name,
                    "email": profile.user.email,
                    "enrollment_count": profile.enrollment_count,
                    "created_at": profile.user.created_at,
                    "is_active": profile.user.is_active,
                }
                for profile in student_profiles.order_by(student_sort)[:100]
            ],
            "instructors": [
                {
                    "user_id": str(profile.user.user_id),
                    "full_name": profile.user.full_name,
                    "email": profile.user.email,
                    "headline": profile.headline,
                    "expertise": profile.expertise,
                    "course_count": profile.course_count,
                    "is_verified": profile.is_verified,
                    "is_active": profile.is_active,
                    "created_at": profile.user.created_at,
                }
                for profile in instructor_profiles.order_by(instructor_sort)[:100]
            ],
            "courses": [
                {
                    "course_id": course.course_id,
                    "course_name": course.course_name,
                    "instructor_name": course.instructor.user.full_name,
                    "category_name": course.category.category_name,
                    "category_sub_name": course.category_sub.category_name if course.category_sub else None,
                    "status": course.status,
                    "level": course.level,
                    "language": course.language,
                    "enrollment_count": course.enrollment_count,
                    "created_at": course.created_at,
                }
                for course in courses[:100]
            ],
        })


class AdminInstructorApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if not can_access_admin(request.user):
            return Response({"error": "Bạn không có quyền phê duyệt giảng viên."}, status=403)

        try:
            profile = InstructorProfile.objects.select_related("user").get(user__user_id=user_id)
        except InstructorProfile.DoesNotExist:
            return Response({"error": "Không tìm thấy hồ sơ giảng viên."}, status=404)

        profile.is_verified = True
        profile.is_active = True
        profile.save(update_fields=["is_verified", "is_active", "updated_at"])

        user = profile.user
        user.role = User.Role.INSTRUCTOR
        user.is_active = True
        user.save(update_fields=["role", "is_active", "updated_at"])

        return Response({"message": "Đã phê duyệt giảng viên."})

import uuid
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from rest_framework import status

from courses.models import CourseEnrollment
from videos.models import VideoNote, VideoProgress
from videos.serializers import VideoNoteSerializer
from analytics.dropout_predictor import predict_dropout
from .models import AuditLog, Certificate, CourseReview, Discussion, LearningGoal, Notification, Report, SystemSetting, Wishlist
from .serializers import (
    AdminUserSerializer, AuditLogSerializer, CertificateSerializer, CourseModerationSerializer,
    CourseReviewSerializer, DiscussionSerializer, InstructorStudentSerializer, LearningGoalSerializer,
    NotificationSerializer, ReportSerializer, SystemSettingSerializer, WishlistSerializer,
)


def is_instructor(user):
    return user.is_authenticated and user.role == User.Role.INSTRUCTOR


def is_student(user):
    return user.is_authenticated and user.role == User.Role.STUDENT


def get_student(user):
    try:
        return user.student_profile
    except StudentProfile.DoesNotExist:
        return None


def log_action(user, action, target_type="", target_id="", metadata=None):
    AuditLog.objects.create(actor=user if user.is_authenticated else None, action=action, target_type=target_type, target_id=str(target_id or ""), metadata=metadata or {})


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = request.user.notifications.all()
        if request.query_params.get("unread") == "1":
            qs = qs.filter(is_read=False)
        return Response(NotificationSerializer(qs[:100], many=True).data)


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id=None):
        qs = request.user.notifications.all()
        if notification_id:
            qs = qs.filter(id=notification_id)
        qs.update(is_read=True)
        return Response({"message": "Đã đánh dấu đã đọc."})


class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        qs = User.objects.all().annotate(
            enrollments_count=Count("student_profile__enrollments", distinct=True),
            courses_count=Count("instructor_profile__courses", distinct=True),
        )
        search = request.query_params.get("search", "").strip()
        role = request.query_params.get("role", "").strip()
        if search:
            qs = qs.filter(Q(full_name__icontains=search) | Q(email__icontains=search))
        if role:
            qs = qs.filter(role=role)
        return Response(AdminUserSerializer(qs.order_by("-created_at")[:200], many=True).data)


class AdminUserManageView(APIView):
    permission_classes = [IsAuthenticated]

    def get_user(self, user_id):
        try:
            return User.objects.get(user_id=user_id), None
        except User.DoesNotExist:
            return None, Response({"error": "Không tìm thấy user."}, status=404)

    def get(self, request, user_id):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        user, err = self.get_user(user_id)
        if err:
            return err
        return Response(AdminUserSerializer(user).data)

    def patch(self, request, user_id):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        user, err = self.get_user(user_id)
        if err:
            return err
        serializer = AdminUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action(request.user, "admin_user_update", "user", user.user_id, request.data)
        return Response(serializer.data)

    def delete(self, request, user_id):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        user, err = self.get_user(user_id)
        if err:
            return err
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        log_action(request.user, "admin_user_lock", "user", user.user_id)
        return Response({"message": "Đã khóa user."})


class AdminUserResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        password = request.data.get("new_password")
        if not password or len(password) < 8:
            return Response({"error": "Mật khẩu tối thiểu 8 ký tự."}, status=400)
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response({"error": "Không tìm thấy user."}, status=404)
        user.set_password(password)
        user.save(update_fields=["password", "updated_at"])
        log_action(request.user, "admin_user_reset_password", "user", user.user_id)
        return Response({"message": "Đã reset mật khẩu."})


class AdminInstructorRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        try:
            profile = InstructorProfile.objects.select_related("user").get(user__user_id=user_id)
        except InstructorProfile.DoesNotExist:
            return Response({"error": "Không tìm thấy hồ sơ giảng viên."}, status=404)
        profile.is_verified = False
        profile.is_active = False
        profile.save(update_fields=["is_verified", "is_active", "updated_at"])
        Notification.objects.create(user=profile.user, type=Notification.Type.APPROVAL, title="Hồ sơ giảng viên bị từ chối", message=request.data.get("reason", ""))
        log_action(request.user, "instructor_reject", "user", user_id, {"reason": request.data.get("reason", "")})
        return Response({"message": "Đã từ chối giảng viên."})


class AdminCourseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        qs = Course.objects.select_related("instructor__user", "category")
        status_filter = request.query_params.get("status")
        search = request.query_params.get("search", "").strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(Q(course_name__icontains=search) | Q(instructor__user__full_name__icontains=search))
        return Response(CourseModerationSerializer(qs.order_by("-created_at")[:200], many=True).data)


class AdminCourseModerationView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, course_id):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        try:
            course = Course.objects.select_related("instructor__user").get(course_id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Không tìm thấy khóa học."}, status=404)
        new_status = request.data.get("status")
        if new_status not in dict(Course.Status.choices):
            return Response({"error": "Status không hợp lệ."}, status=400)
        course.status = new_status
        course.save(update_fields=["status", "updated_at"])
        Notification.objects.create(user=course.instructor.user, type=Notification.Type.COURSE, title="Trạng thái khóa học thay đổi", message=f"{course.course_name}: {new_status}")
        log_action(request.user, "course_moderate", "course", course_id, {"status": new_status})
        return Response(CourseModerationSerializer(course).data)


class AdminAuditLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        return Response(AuditLogSerializer(AuditLog.objects.select_related("actor")[:200], many=True).data)


class AdminSystemSettingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        return Response(SystemSettingSerializer(SystemSetting.objects.all(), many=True).data)

    def post(self, request):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        setting, _ = SystemSetting.objects.update_or_create(key=request.data.get("key"), defaults={"value": request.data.get("value", {}), "description": request.data.get("description", "")})
        log_action(request.user, "system_setting_update", "setting", setting.key)
        return Response(SystemSettingSerializer(setting).data)


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = get_student(request.user)
        if not student:
            return Response({"error": "Chỉ học viên được dùng wishlist."}, status=403)
        return Response(WishlistSerializer(Wishlist.objects.filter(student=student).select_related("course", "course__instructor__user", "course__category"), many=True).data)

    def post(self, request):
        student = get_student(request.user)
        if not student:
            return Response({"error": "Chỉ học viên được dùng wishlist."}, status=403)
        serializer = WishlistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item, _ = Wishlist.objects.get_or_create(student=student, course=serializer.validated_data["course"])
        return Response(WishlistSerializer(item).data, status=201)

    def delete(self, request):
        student = get_student(request.user)
        course_id = request.data.get("course_id")
        Wishlist.objects.filter(student=student, course_id=course_id).delete()
        return Response(status=204)


class CourseReviewListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        reviews = CourseReview.objects.filter(course_id=course_id, is_hidden=False).select_related("student__user")
        return Response(CourseReviewSerializer(reviews, many=True).data)

    def post(self, request, course_id):
        student = get_student(request.user)
        if not student:
            return Response({"error": "Chỉ học viên được review."}, status=403)
        if not CourseEnrollment.objects.filter(student=student, course_id=course_id).exists():
            return Response({"error": "Bạn cần đăng ký khóa học trước."}, status=403)
        serializer = CourseReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review, _ = CourseReview.objects.update_or_create(student=student, course_id=course_id, defaults=serializer.validated_data)
        return Response(CourseReviewSerializer(review).data, status=201)


class CertificateListIssueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = get_student(request.user)
        if not student:
            return Response({"error": "Chỉ học viên có chứng chỉ."}, status=403)
        return Response(CertificateSerializer(Certificate.objects.filter(student=student).select_related("course", "student__user"), many=True).data)

    def post(self, request, course_id):
        student = get_student(request.user)
        if not student:
            return Response({"error": "Chỉ học viên có chứng chỉ."}, status=403)
        try:
            enrollment = CourseEnrollment.objects.get(student=student, course_id=course_id)
        except CourseEnrollment.DoesNotExist:
            return Response({"error": "Bạn chưa đăng ký khóa học."}, status=404)
        if enrollment.status != CourseEnrollment.Status.COMPLETED and enrollment.course_progress_percent < 100:
            return Response({"error": "Chưa hoàn thành khóa học."}, status=400)
        cert, _ = Certificate.objects.get_or_create(student=student, course_id=course_id, enrollment=enrollment, defaults={"certificate_code": uuid.uuid4().hex[:16].upper()})
        return Response(CertificateSerializer(cert).data, status=201)


class LearningGoalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = get_student(request.user)
        return Response(LearningGoalSerializer(LearningGoal.objects.filter(student=student), many=True).data)

    def post(self, request):
        student = get_student(request.user)
        serializer = LearningGoalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        goal = serializer.save(student=student)
        return Response(LearningGoalSerializer(goal).data, status=201)


class LearningGoalManageView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, goal_id):
        student = get_student(request.user)
        goal = LearningGoal.objects.get(id=goal_id, student=student)
        serializer = LearningGoalSerializer(goal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(LearningGoalSerializer(serializer.save()).data)

    def delete(self, request, goal_id):
        student = get_student(request.user)
        LearningGoal.objects.filter(id=goal_id, student=student).delete()
        return Response(status=204)


class ContinueWatchingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = get_student(request.user)
        qs = VideoProgress.objects.filter(student=student, completed=False).select_related("video", "video__course").order_by("-last_watched_at")[:20]
        return Response([{
            "video_id": p.video_id,
            "title": p.video.title,
            "course_id": p.video.course_id,
            "course_name": p.video.course.course_name,
            "watched_seconds": p.watched_seconds,
            "duration_seconds": p.duration_seconds,
            "last_watched_at": p.last_watched_at
        } for p in qs])


class StudentNotesSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = get_student(request.user)
        q = request.query_params.get("q", "").strip()
        qs = VideoNote.objects.filter(student=student).select_related("video", "video__course")
        if q:
            qs = qs.filter(content__icontains=q)
        return Response(VideoNoteSerializer(qs[:100], many=True).data)


class DiscussionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        qs = Discussion.objects.filter(course_id=course_id, parent__isnull=True, is_hidden=False).select_related("user").annotate(replies_count=Count("replies"))
        return Response(DiscussionSerializer(qs, many=True).data)

    def post(self, request, course_id):
        data = request.data.copy()
        data["course"] = course_id
        serializer = DiscussionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(user=request.user)
        return Response(DiscussionSerializer(obj).data, status=201)


class DiscussionRepliesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, discussion_id):
        qs = Discussion.objects.filter(parent_id=discussion_id, is_hidden=False).select_related("user")
        return Response(DiscussionSerializer(qs, many=True).data)


class ReportListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        return Response(ReportSerializer(Report.objects.select_related("reporter")[:200], many=True).data)

    def post(self, request):
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save(reporter=request.user)
        return Response(ReportSerializer(report).data, status=201)


class ReportManageView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, report_id):
        if not can_access_admin(request.user):
            return Response({"error": "Không có quyền."}, status=403)
        report = Report.objects.get(id=report_id)
        report.status = request.data.get("status", report.status)
        report.admin_note = request.data.get("admin_note", report.admin_note)
        report.save(update_fields=["status", "admin_note", "updated_at"])
        log_action(request.user, "report_update", "report", report.id, {"status": report.status})
        return Response(ReportSerializer(report).data)


class InstructorDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_instructor(request.user):
            return Response({"error": "Chỉ giảng viên."}, status=403)
        courses = Course.objects.filter(instructor__user=request.user)
        enrollments = CourseEnrollment.objects.filter(course__in=courses)
        return Response({
            "total_courses": courses.count(),
            "published_courses": courses.filter(status=Course.Status.PUBLISHED).count(),
            "total_students": enrollments.values("student").distinct().count(),
            "avg_progress": enrollments.aggregate(v=Avg("course_progress_percent"))["v"] or 0,
            "completed_enrollments": enrollments.filter(status=CourseEnrollment.Status.COMPLETED).count(),
            "total_watch_time_seconds": enrollments.aggregate(v=Sum("total_watch_time_seconds"))["v"] or 0,
        })


class InstructorStudentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_instructor(request.user):
            return Response({"error": "Chỉ giảng viên."}, status=403)
        qs = CourseEnrollment.objects.filter(course__instructor__user=request.user).select_related("student__user", "course")
        course_id = request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return Response(InstructorStudentSerializer(qs.order_by("-updated_at")[:300], many=True).data)


class InstructorNotifyAtRiskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, enrollment_id):
        if not is_instructor(request.user):
            return Response({"error": "Chỉ giảng viên."}, status=403)
        try:
            enrollment = CourseEnrollment.objects.select_related("student__user", "course").get(id=enrollment_id, course__instructor__user=request.user)
        except CourseEnrollment.DoesNotExist:
            return Response({"error": "Không tìm thấy enrollment."}, status=404)
        message = request.data.get("message", f"Bạn có nguy cơ bị lỡ tiến độ khóa {enrollment.course.course_name}. Hãy tiếp tục học nhé!")
        Notification.objects.create(user=enrollment.student.user, type=Notification.Type.DROPOUT, title="Nhắc học tập", message=message, data={"course_id": enrollment.course_id})
        log_action(request.user, "instructor_notify_student", "enrollment", enrollment.id)
        return Response({"message": "Đã gửi thông báo."})

