import random
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import StudentProfile, InstructorProfile
from courses.models import Course, Category, CourseEnrollment
from videos.models import Video
from analytics.models import LearningEvent
from analytics.dropout_predictor import train_model, predict_dropout

User = get_user_model()

class Command(BaseCommand):
    help = 'Tạo dữ liệu giả để kiểm chứng Random Forest model'

    def handle(self, *args, **kwargs):
        self.stdout.write("Bat dau don dep va tao du lieu gia...")
        now = timezone.now()

        # 1. Tạo Category
        cat, _ = Category.objects.get_or_create(category_name="Mock Category")

        # 2. Tạo Instructor
        user_inst, _ = User.objects.get_or_create(email="mock_inst@test.com", defaults={"full_name": "Mock Instructor"})
        if not user_inst.check_password('password'):
            user_inst.set_password('password')
            user_inst.save()
        inst, _ = InstructorProfile.objects.get_or_create(
            user=user_inst,
            defaults={"profile_url": "mock-instructor-profile-url-123"}
        )

        # 3. Tạo Course
        course, _ = Course.objects.get_or_create(
            course_name="Khóa học kiểm chứng Dropout",
            defaults={"instructor": inst, "category": cat, "status": Course.Status.PUBLISHED}
        )
        
        # 4. Tạo Video
        video, _ = Video.objects.get_or_create(
            course=course, title="Video bài giảng 1",
            defaults={"duration_seconds": 600, "order": 1, "is_published": True}
        )

        # Xóa mock students cũ (nếu có)
        mock_users = User.objects.filter(email__startswith="mock_student_")
        mock_users.delete()

        # 5. Tạo 50 Học viên
        # 25 Chăm chỉ (Active, low risk)
        # 15 Bỏ học hẳn (Dropped, label 1 - để model học ground truth)
        # 10 Đang học nhưng lười (Active, bad behavior - để test model predict ra xác suất dropout cao)
        
        for i in range(50):
            u = User.objects.create(email=f"mock_student_{i}@test.com", full_name=f"Mock Student {i}")
            sp = StudentProfile.objects.create(user=u)
            
            if i < 25:
                # Group 1: Chăm chỉ
                enrolled_days = random.randint(10, 30)
                last_accessed = now - timedelta(days=random.randint(0, 2))
                progress = random.uniform(50, 100)
                status = CourseEnrollment.Status.ACTIVE
                group = "good"
            elif i < 40:
                # Group 2: Đã bỏ học
                enrolled_days = random.randint(20, 30)
                last_accessed = now - timedelta(days=random.randint(15, 25))
                progress = random.uniform(0, 30)
                status = CourseEnrollment.Status.DROPPED
                group = "dropped"
            else:
                # Group 3: Lười (nguy cơ bỏ học cao)
                enrolled_days = random.randint(10, 30)
                last_accessed = now - timedelta(days=random.randint(7, 12))
                progress = random.uniform(5, 20)
                status = CourseEnrollment.Status.ACTIVE
                group = "bad_behavior"

            enrollment = CourseEnrollment.objects.create(
                student=sp,
                course=course,
                status=status,
                course_progress_percent=progress,
                login_streak=random.randint(5, 15) if group == "good" else random.randint(0, 2),
            )
            
            # Override auto_now_add dates
            CourseEnrollment.objects.filter(id=enrollment.id).update(
                enrolled_at=now - timedelta(days=enrolled_days),
                last_accessed_at=last_accessed
            )
            
            # Tạo Learning Events
            num_events = random.randint(20, 50) if group == "good" else random.randint(5, 15)
            
            event_types_good = [LearningEvent.EventType.PLAY, LearningEvent.EventType.PAUSE, LearningEvent.EventType.NOTE_CREATED, LearningEvent.EventType.SKIP_BACKWARD_10]
            event_types_bad = [LearningEvent.EventType.PLAY, LearningEvent.EventType.SKIP_FORWARD_10, LearningEvent.EventType.RATE_CHANGE]
            
            events = []
            for _ in range(num_events):
                event_type = random.choice(event_types_good if group == "good" else event_types_bad)
                playback_rate = 1.0
                if event_type == LearningEvent.EventType.RATE_CHANGE and group != "good":
                    playback_rate = random.choice([1.5, 2.0])
                    
                events.append(LearningEvent(
                    student=sp,
                    course=course,
                    video=video,
                    event_type=event_type,
                    playback_rate=playback_rate if event_type == LearningEvent.EventType.RATE_CHANGE else None,
                ))
            
            created_events = LearningEvent.objects.bulk_create(events)
            for e in created_events:
                LearningEvent.objects.filter(event_id=e.event_id).update(created_at=last_accessed - timedelta(hours=random.randint(0, 48)))

        self.stdout.write("[OK] Successfully created 50 mock students and learning events data!")
        
        self.stdout.write("[INFO] Starting to retrain the model with new data...")
        train_res = train_model()
        self.stdout.write(f"   - Accuracy: {train_res.get('accuracy')}")
        self.stdout.write(f"   - Dropout: {train_res.get('num_dropout')} | Active: {train_res.get('num_active')}")
        
        self.stdout.write("\n[VERIFICATION] PREDICTION RESULTS (For ACTIVE students only):")
        
        # Test dự đoán cho vài học viên chăm chỉ
        good_student = CourseEnrollment.objects.get(student__user__email="mock_student_0@test.com")
        good_pred = predict_dropout(good_student)
        self.stdout.write(
            f"[Good] Diligent Student (Student 0):\n"
            f"   - Progress: {good_student.course_progress_percent:.1f}%\n"
            f"   - Days inactive: {(now - good_student.last_accessed_at).days} days\n"
            f"   => Predicted Dropout Probability: {good_pred['dropout_probability']:.1%} (Risk Level: {good_pred['risk_level']})"
        )
        
        # Test dự đoán cho vài học viên lười (có nguy cơ bỏ học)
        bad_student = CourseEnrollment.objects.get(student__user__email="mock_student_45@test.com")
        bad_pred = predict_dropout(bad_student)
        self.stdout.write(
            f"[Bad] Lazy / Low Interaction Student (Student 45):\n"
            f"   - Progress: {bad_student.course_progress_percent:.1f}%\n"
            f"   - Days inactive: {(now - bad_student.last_accessed_at).days} days\n"
            f"   => Predicted Dropout Probability: {bad_pred['dropout_probability']:.1%} (Risk Level: {bad_pred['risk_level']})\n"
            f"   - Reasons: {', '.join(bad_pred['reasons'])}"
        )
        
        self.stdout.write("\n[DONE] Verification completed!")
