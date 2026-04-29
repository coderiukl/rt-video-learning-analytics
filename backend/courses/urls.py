from django.urls import path
from .views import (
    CategoryListView, CategoryManageView,
    CourseListView, CourseDetailView,
    CourseCreateView, CourseUpdateDeleteView,
    EnrollCourseView,
    MyCoursesView, MyInstructorCoursesView
)
urlpatterns = [
    # Categories
    path("categories/", CategoryListView.as_view(), name='category-list'),
    path("categories/<int:category_id>/", CategoryManageView.as_view(), name='category-manage'),

    # Danh sách & tìm kiếm (public)
    path("", CourseListView.as_view(), name="course-list"),

    # Chi tiết (public)
    path("<int:course_id>/", CourseDetailView.as_view(), name='course-detail'),

    # Tạo khóa học (instructor)
    path("create/", CourseCreateView.as_view(), name='course-create'),

    # Sửa / xóa (instructor)
    path("<int:course_id>/manage/", CourseUpdateDeleteView.as_view(), name='course-manage'),

    # Đăng ký khóa học (student)
    path("<int:course_id>/enroll/", EnrollCourseView.as_view(), name='course-enroll'),

    # Khóa học của tôi
    path("my-course/", MyCoursesView.as_view(), name='my-courses'),

    # Khóa học của instructor
    path('instructor-course/', MyInstructorCoursesView.as_view(), name='instructor-courses'),
]
