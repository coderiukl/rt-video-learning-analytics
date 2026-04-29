from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Course, CourseEnrollment
from .serializers import (
    CategorySerializer, CategoryCreateUpdateSerializer,
    CourseListSerializer, CourseDetailSerializer, CourseCreateUpdateSerializer,
    EnrollmentSerializer
)

# Create your views here.
def is_instructor(user):
    return user.role == 'instructor'

def is_approved_instructor(user):
    if not is_instructor(user):
        return False
    instructor = get_instructor_profile(user)
    return bool(instructor and instructor.is_verified and instructor.is_active)

def is_student(user):
    return get_student_profile(user) is not None

def can_manage_categories(user):
    return user.is_authenticated and (
        user.is_staff or user.role in ["admin", "instructor"]
    )

def get_instructor_profile(user):
    try:
        return user.instructor_profile
    except Exception:
        return None
    
def get_student_profile(user):
    try:
        return user.student_profile
    except Exception:
        return None

# CATEGORIES
class CategoryListView(APIView):
    """
    GET /api/courses/categories/
    Lấy toàn bộ category chính kèm subcategories.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        categories =  Category.objects.filter(parent__isnull=True).prefetch_related("subcategories")
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        if not can_manage_categories(request.user):
            return Response(
                {"error": "Bạn không có quyền tạo danh mục."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CategoryCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        category = serializer.save()
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)


class CategoryManageView(APIView):
    permission_classes = [AllowAny]

    def get_category(self, category_id):
        try:
            return Category.objects.prefetch_related("subcategories").get(category_id=category_id), None
        except Category.DoesNotExist:
            return None, Response(
                {"error": "Danh mục không tồn tại."},
                status=status.HTTP_404_NOT_FOUND
            )

    def get(self, request, category_id):
        category, err = self.get_category(category_id)
        if err:
            return err
        return Response(CategorySerializer(category).data)

    def put(self, request, category_id):
        if not can_manage_categories(request.user):
            return Response(
                {"error": "Bạn không có quyền chỉnh sửa danh mục."},
                status=status.HTTP_403_FORBIDDEN
            )

        category, err = self.get_category(category_id)
        if err:
            return err

        serializer = CategoryCreateUpdateSerializer(category, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        category = serializer.save()
        return Response(CategorySerializer(category).data)

    def delete(self, request, category_id):
        if not can_manage_categories(request.user):
            return Response(
                {"error": "Bạn không có quyền xóa danh mục."},
                status=status.HTTP_403_FORBIDDEN
            )

        category, err = self.get_category(category_id)
        if err:
            return err

        if category.subcategories.exists() or category.courses.exists() or category.sub_courses.exists():
            return Response(
                {"error": "Không thể xóa danh mục đang có danh mục con hoặc khóa học sử dụng."},
                status=status.HTTP_400_BAD_REQUEST
            )

        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
# COURSES
class CourseListView(APIView):
    """
    GET /api/courses/
    Query params:
        - search: tìm theo tên
        - category: lọc theo category_id
        - level: beginner | intermediate | advanced
        - language: vi | en | ...
    """
    permission_classes = [AllowAny]

    def get(self, request):
        courses = Course.objects.filter(status="published").select_related(
            "instructor__user", "category", "category_sub"
        )

        # Search
        search = request.query_params.get("search")
        if search:
            courses = courses.filter(course_name__icontains=search)

        # Filter Category
        category = request.query_params.get("category")
        if category:
            if str(category).isdigit():
                courses = courses.filter(category_id=category)
            else:
                courses = courses.filter(category__category_name__iexact=category)

        # Filter Level
        level = request.query_params.get('level')
        if level:
            courses = courses.filter(level=level)

        # Filter Language
        language = request.query_params.get('language')
        if language:
            courses = courses.filter(language=language)

        return Response(CourseListSerializer(courses, many=True).data)
    
class CourseDetailView(APIView):
    """
    GET /api/courses/<course_id>/
    """
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        try:
            course = Course.objects.select_related(
                "instructor__user", "category", "category_sub"
            ).get(course_id=course_id, status='published')
        except Course.DoesNotExist:
            return Response({"error": "Khóa học không tồn tại"}, status=status.HTTP_404_NOT_FOUND)
        
        data = CourseDetailSerializer(course).data
        data["is_enrolled"] = False
        data["enrollment_status"] = None

        if request.user.is_authenticated:
            student = get_student_profile(request.user)
            if student:
                enrollment = CourseEnrollment.objects.filter(student=student, course=course).first()
                if enrollment:
                    data["is_enrolled"] = True
                    data["enrollment_status"] = enrollment.status

        return Response(data)
    
class CourseCreateView(APIView):
    """
    POST /api/courses/create/
    Header: Authorization: Bearer <token>
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not is_approved_instructor(request.user):
            return Response(
                {"error": "Chỉ giảng viên đã được admin duyệt mới có thể tạo khóa học."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instructor = get_instructor_profile(request.user)
        if not instructor:
            return Response(
                {"error": "Không tìm thấy instructor profile."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CourseCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        course = serializer.save(instructor=instructor)
        return Response(CourseDetailSerializer(course).data, status=status.HTTP_201_CREATED)
    
class CourseUpdateDeleteView(APIView):
    """
    PUT   /api/courses/<course_id>/manage/  
    DELETE /api/courses/<course_id>/manage/ 
    Header: Authorization: Bearer <token>
    """

    permission_classes = [IsAuthenticated]

    def get_course(self, course_id, user):
        """Lấy course và kiểm tra quyền sở hữu."""
        try:
            course = Course.objects.get(course_id=course_id)
        except Course.DoesNotExist:
            return None, Response(
                {"error": "Khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND
            )
        
        if not is_approved_instructor(user):
            return None, Response(
                {"error": "Chỉ giảng viên đã được admin duyệt mới có quyền này."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if course.instructor.user_id != user.user_id:
            return None, Response(
                {"error": "Bạn không có quyền chỉnh sửa khóa học này."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return course, None

    def get(self, request, course_id):
        course, err = self.get_course(course_id, request.user)
        if err:
            return err

        data = CourseDetailSerializer(course).data
        data["is_enrolled"] = False
        data["enrollment_status"] = None

        if request.user.is_authenticated:
            student = get_student_profile(request.user)
            if student:
                enrollment = CourseEnrollment.objects.filter(student=student, course=course).first()
                if enrollment:
                    data["is_enrolled"] = True
                    data["enrollment_status"] = enrollment.status

        return Response(data)
    
    def put(self, request, course_id):
        course, err = self.get_course(course_id, request.user)
        if err:
            return err
        
        serializer = CourseCreateUpdateSerializer(course, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        course = serializer.save()
        return Response(CourseDetailSerializer(course).data)
    
    def delete(self, request, course_id):
        course, err = self.get_course(course_id, request.user)
        if err:
            return err
        
        # Không xóa hẳn nếu đã có học viên - chuyển sang archived
        if course.enrollments.exists():
            course.status = Course.Status.ARCHIVED
            course.save(update_fields=['status', "updated_at"])
            return Response(
                {"message": "Khóa học đã được chuyển sang trạng thái archived (đã có học viên đăng ký)."}
            )
        course.delete()
        return Response(
            {"message": "Xóa khóa học thành công."}, status=status.HTTP_204_NO_CONTENT
        )
    
# Enroll Course
class EnrollCourseView(APIView):
    """
    POST /api/courses/<course_id>/enroll/
    Header: Authorization: Bearer <token>
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        if not is_student(request.user):
            return Response(
                {"error": "Chỉ student mới có thể đăng ký khóa học."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        student = get_student_profile(request.user)
        if not student:
            return Response(
                {"error": "Không tìm thấy student profile."},
                status=status.HTTP_400_BAD_REQUEST            
            )
        
        try:
            course = Course.objects.get(course_id=course_id, status="published")
        except Course.DoesNotExist:
            return Response(
                {"error": "Khóa học không tồn tại hoặc chưa được published."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Kiểm tra đã đăng ký chưa
        if CourseEnrollment.objects.filter(student=student, course=course).exists():
            return Response(
                {"error": "Bạn đã đăng ký khóa học này rồi."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment = CourseEnrollment.objects.create(student=student, course=course)
        return Response({
            "message": f"Đăng ký khóa học '{course.course_name}' thành công!",
            "enrollment": EnrollmentSerializer(enrollment).data,
        }, status=status.HTTP_201_CREATED)

# Xem danh sách khóa học (student)
class MyCoursesView(APIView):
    """
    GET /api/courses/my-courses/
    Header: Authorization: Bearer <token>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_student(request.user):
            return Response(
                {"error": "Chỉ student mới có danh sách khóa học."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        student = get_student_profile(request.user)
        enrollments = CourseEnrollment.objects.filter(student=student).select_related(
            "course__instructor__user", "course__category"
        )

        return Response(EnrollmentSerializer(enrollments, many=True).data)
    
# Xem danh sách khóa học (instructor)
class MyInstructorCoursesView(APIView):
    """
    GET /api/courses/instructor/my-courses/
    Header: Authorization: Bearer <token>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_approved_instructor(request.user):
            return Response(
                {"error": "Chỉ giảng viên đã được admin duyệt mới có thể xem danh sách này."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instructor = get_instructor_profile(request.user)
        courses = Course.objects.filter(instructor=instructor).select_related("category", "category_sub").prefetch_related("enrollments", "videos")
        return Response(CourseListSerializer(courses, many=True).data)
