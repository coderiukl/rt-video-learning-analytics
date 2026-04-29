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
        courses = Course.objects.select_related("instructor__user", "category").annotate(
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
                    "status": course.status,
                    "level": course.level,
                    "language": course.language,
                    "enrollment_count": course.enrollment_count,
                    "created_at": course.created_at,
                }
                for course in courses[:100]
            ],
        })
