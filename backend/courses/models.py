from django.db import models
from users.models import User, InstructorProfile, StudentProfile
# Create your models here.

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="subcategories"
    )

    class Meta:
        db_table="categories"
        verbose_name_plural="categories"

    def __str__(self):
        return self.category_name
    
class Course(models.Model):
    class Level(models.TextChoices):
        BEGINER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    course_id = models.AutoField(primary_key=True)
    instructor = models.ForeignKey(
        InstructorProfile, on_delete=models.RESTRICT, 
        related_name="courses"
    )

    category = models.ForeignKey(
        Category, on_delete=models.RESTRICT,
        related_name="courses"
    )

    category_sub = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="sub_courses"
    )

    course_name = models.CharField(max_length=255)
    course_describes =  models.TextField(blank=True)
    language = models.CharField(max_length=50, default='vi')
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINER)
    image_course = models.URLField(blank=True, null=True)
    intro_video = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses"
        constraints = [
            models.CheckConstraint(
                check=~models.Q(category_id=models.F("category_sub_id")),
                name="category_and_sub_must_differ"
            )
        ]

    def __str__(self):
        return self.course_name
    
class CourseEnrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        DROPPED = "dropped", "Dropped"

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="enrollments"
    )

    course = models.ForeignKey(
        Course, on_delete=models.RESTRICT, related_name="enrollments"
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    course_progress_percent  = models.FloatField(default=0.0)
    total_watch_time_seconds  = models.IntegerField(default=0)
    videos_completed = models.IntegerField(default=0)
    login_streak = models.IntegerField(default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "course_enrollments"
        unique_together =  [["student", "course"]] # 1 student chỉ đăng ký 1 khóa 1 lần
    
    def __str__(self):
        return f"{self.student_id} -> {self.course.course_name}"
