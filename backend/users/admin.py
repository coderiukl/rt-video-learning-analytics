from django.contrib import admin

from .models import InstructorProfile, StudentProfile, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "role", "is_active", "is_staff", "created_at")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "full_name")
    ordering = ("-created_at",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "country", "preferred_language", "updated_at")
    search_fields = ("user__email", "user__full_name")


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "expertise", "is_verified", "is_active", "joined_as_instructor_at")
    list_filter = ("is_verified", "is_active")
    search_fields = ("user__email", "user__full_name", "headline", "expertise")
    actions = ["approve_instructors"]

    @admin.action(description="Duyệt hồ sơ giảng viên")
    def approve_instructors(self, request, queryset):
        updated = 0
        for profile in queryset.select_related("user"):
            profile.is_verified = True
            profile.is_active = True
            profile.save(update_fields=["is_verified", "is_active", "updated_at"])

            profile.user.role = User.Role.INSTRUCTOR
            profile.user.save(update_fields=["role", "updated_at"])
            updated += 1

        self.message_user(request, f"Đã duyệt {updated} hồ sơ giảng viên.")
