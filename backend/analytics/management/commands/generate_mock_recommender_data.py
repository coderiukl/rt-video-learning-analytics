import random
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import StudentProfile, InstructorProfile
from courses.models import Course, Category, CourseEnrollment
from analytics.recommender import recommend_courses_for_student

User = get_user_model()

class Command(BaseCommand):
    help = 'Tạo dữ liệu giả để kiểm chứng tính năng Course Recommendation (SVD)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Bat dau xoa du lieu mock cu va tao moi cho Course Recommender...")

        # 1. Tạo Category
        cat, _ = Category.objects.get_or_create(category_name="Mock Course Category")

        # 2. Tạo Instructor
        user_inst, _ = User.objects.get_or_create(email="mock_inst_course_rec@test.com", defaults={"full_name": "Mock Course Instructor"})
        if not user_inst.check_password('password'):
            user_inst.set_password('password')
            user_inst.save()
        inst, _ = InstructorProfile.objects.get_or_create(
            user=user_inst,
            defaults={"profile_url": "mock-instructor-profile-url"}
        )

        # 3. Tạo Courses (10 Khóa học)
        courses = []
        for i in range(1, 11):
            c, _ = Course.objects.get_or_create(
                course_name=f"Khóa học Chủ đề {i}",
                defaults={"instructor": inst, "category": cat, "status": Course.Status.PUBLISHED}
            )
            courses.append(c)

        # Xóa mock students cũ
        User.objects.filter(email__startswith="course_rec_student_").delete()
        User.objects.filter(email="test_course_rec@test.com").delete()

        enrollments_to_create = []

        def create_student_and_enrollments(email, name, engaged_course_indices):
            u = User.objects.create(email=email, full_name=name)
            u.set_password('password')
            u.save()
            sp = StudentProfile.objects.create(user=u)
            
            for c_idx in engaged_course_indices:
                enrollments_to_create.append(CourseEnrollment(
                    student=sp,
                    course=courses[c_idx],
                    status=CourseEnrollment.Status.ACTIVE,
                    course_progress_percent=100.0, # Đã hoàn thành
                    login_streak=random.randint(1, 5),
                ))
            return sp

        # Group A: Học các khóa 0, 1, 2
        for i in range(10):
            create_student_and_enrollments(f"course_rec_student_A_{i}@test.com", f"Student A {i}", [0, 1, 2])
            
        # Group B: Học các khóa 3, 4, 5
        for i in range(10):
            create_student_and_enrollments(f"course_rec_student_B_{i}@test.com", f"Student B {i}", [3, 4, 5])
            
        # Group C: Học các khóa 6, 7, 8, 9
        for i in range(10):
            create_student_and_enrollments(f"course_rec_student_C_{i}@test.com", f"Student C {i}", [6, 7, 8, 9])

        CourseEnrollment.objects.bulk_create(enrollments_to_create)

        # Test Student: Đang xem chi tiết khóa học 0, và CŨNG đã học khóa 0.
        test_student = create_student_and_enrollments("test_course_rec@test.com", "Học viên Test Gợi ý Khóa học", [0])
        CourseEnrollment.objects.bulk_create([CourseEnrollment(
            student=test_student,
            course=courses[0],
            status=CourseEnrollment.Status.ACTIVE,
            course_progress_percent=100.0,
            login_streak=2,
        )])

        self.stdout.write(f"[OK] Successfully created mock data for course recommender testing!")
        
        self.stdout.write(f"\n[VERIFICATION] Checking course recommendations for test_course_rec@test.com viewing Course ID {courses[0].course_id}:")
        # Gọi thuật toán gợi ý:
        recs = recommend_courses_for_student(test_student, courses[0].course_id, n=3)
        
        if recs:
            for rec in recs:
                self.stdout.write(f"- Course ID {rec['course_id']} (Score: {rec['similarity_score']:.4f})")
        else:
            self.stdout.write("No recommendations.")
            
        self.stdout.write(f"\n[DONE] Ban co the kiem tra truc tiep tren giao dien bang cach vao xem chi tiet Course ID = {courses[0].course_id}")
