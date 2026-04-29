from rest_framework import serializers
from .models import Category, Course, CourseEnrollment

# CATEGORY
class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["category_id", "category_name", "parent_id", "subcategories"]

    def get_subcategories(self, obj):
        return CategorySerializer(obj.subcategories.all(), many=True).data


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["category_name", "parent"]

    def validate_parent(self, parent):
        if parent and parent.parent_id is not None:
            raise serializers.ValidationError("Danh mục con chỉ được thuộc danh mục chính.")
        return parent

    def validate(self, data):
        parent = data.get("parent")
        if self.instance and parent and parent.category_id == self.instance.category_id:
            raise serializers.ValidationError("Danh mục không thể là cha của chính nó.")
        return data
    
# COURSE
class CourseListSerializer(serializers.ModelSerializer):
    """Dùng cho danh sách — trả về ít field hơn để nhẹ hơn."""
    instructor_name = serializers.CharField(source="instructor.user.full_name", read_only=True)
    category_name = serializers.CharField(source="category.category_name", read_only=True)
    total_videos = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    active_students = serializers.SerializerMethodField()
    completed_students = serializers.SerializerMethodField()
    avg_progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields  = [
            "course_id", "course_name", "course_describes", "language",
            "level", "image_course", "intro_video", "status", "instructor_name",
            "category_name", "total_videos", "total_students", "active_students",
            "completed_students", "avg_progress_percent", "created_at",
        ]

    def get_total_videos(self, obj):
        videos = getattr(obj, "videos", None)
        return videos.count() if videos is not None else 0

    def get_total_students(self, obj):
        return obj.enrollments.count()

    def get_active_students(self, obj):
        return obj.enrollments.filter(status="active").count()

    def get_completed_students(self, obj):
        return obj.enrollments.filter(status="completed").count()

    def get_avg_progress_percent(self, obj):
        enrollments = obj.enrollments.all()
        total = enrollments.count()
        if not total:
            return 0
        progress = sum(enrollment.course_progress_percent for enrollment in enrollments)
        return round(progress / total, 1)
    
class CourseDetailSerializer(serializers.ModelSerializer):
    """Dùng cho chi tiết 1 khóa học — trả về đầy đủ."""
    instructor_name = serializers.CharField(source="instructor.user.full_name", read_only=True)
    instructor_avatar = serializers.CharField(source="instructor.user.avatar_url", read_only=True)
    instructor_headline = serializers.CharField(source="instructor.headline", read_only=True)
    category_name = serializers.CharField(source="category.category_name", read_only=True)
    category_sub_name =  serializers.CharField(source="category_sub.category_name", read_only=True)
    total_videos = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "course_id", "course_name", "course_describes", "language",
            "level", "image_course", "intro_video", "status",
            "category", "category_sub",
            "instructor_name", "instructor_avatar", "instructor_headline",
            "category_name", "category_sub_name",
            "total_videos", "total_students",
            "created_at", "updated_at",
        ]

    def get_total_videos(self, obj):
        videos = getattr(obj, "videos", None)
        return videos.count() if videos is not None else 0
    
    def get_total_students(self, obj):
        return obj.enrollments.filter(status='active').count()
    
class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Dùng cho tạo và sửa khóa học."""
    class Meta:
        model = Course
        fields = [
            "course_name", "course_describes", "language",
            "level", "image_course", "intro_video", "status",
            "category", "category_sub",
        ]
    
    def validate(self, data):
        category = data.get("category")
        category_sub = data.get("category_sub")

        # category_sub phải khác category
        if category and category_sub and category == category_sub:
            raise serializers.ValidationError("category và category_sub không được trùng nhau.")
        
        # category_sub phải là con của category
        if category_sub and category and category_sub.parent_id != category.category_id:
            raise serializers.ValidationError("category_sub phải là danh mục phụ của category đã chọn.")
        
        return data
    
# ENROLLMENT
class EnrollmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.course_name", read_only=True)
    image_course = serializers.CharField(source="course.image_course", read_only=True)
    intro_video = serializers.CharField(source="course.intro_video", read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = [
            "id", "course_id", "course_name", "image_course",
            "intro_video", "status", "course_progress_percent",
            "videos_completed", "total_watch_time_seconds",
            "enrolled_at", "last_accessed_at",
        ]
