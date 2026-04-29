from django.contrib import admin

from .models import Category, Course, CourseEnrollment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("category_id", "category_name", "parent")
    search_fields = ("category_name",)
    list_filter = ("parent",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("course_id", "course_name", "instructor", "category", "status", "created_at")
    search_fields = ("course_name", "instructor__user__email", "instructor__user__full_name")
    list_filter = ("status", "level", "language", "category")


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "course", "status", "course_progress_percent", "enrolled_at")
    search_fields = ("student__user__email", "student__user__full_name", "course__course_name")
    list_filter = ("status",)
