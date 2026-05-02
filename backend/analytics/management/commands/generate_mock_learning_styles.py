import random
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import StudentProfile, InstructorProfile
from courses.models import Course, Category, CourseEnrollment
from videos.models import Video
from analytics.models import LearningEvent
from analytics.learning_style import cluster_learning_styles

User = get_user_model()

class Command(BaseCommand):
    help = 'Tạo dữ liệu giả để kiểm chứng tính năng Learning Style Clustering'

    def handle(self, *args, **kwargs):
        self.stdout.write("Bat dau xoa du lieu mock cu va tao moi cho Clustering...")
        now = timezone.now()

        # 1. Tạo Category
        cat, _ = Category.objects.get_or_create(category_name="Mock Category")

        # 2. Tạo Instructor
        user_inst, _ = User.objects.get_or_create(email="mock_inst_styles@test.com", defaults={"full_name": "Mock Styles Instructor"})
        if not user_inst.check_password('password'):
            user_inst.set_password('password')
            user_inst.save()
        inst, _ = InstructorProfile.objects.get_or_create(
            user=user_inst,
            defaults={"profile_url": "mock-instructor-profile-url-styles"}
        )

        # 3. Tạo Course
        course, _ = Course.objects.get_or_create(
            course_name="Khóa học phân loại Learning Styles",
            defaults={"instructor": inst, "category": cat, "status": Course.Status.PUBLISHED}
        )
        
        # 4. Tạo Video
        video, _ = Video.objects.get_or_create(
            course=course, title="Video học tập mẫu 1",
            defaults={"duration_seconds": 600, "order": 1, "is_published": True}
        )

        # Xóa mock students cũ (nếu có)
        mock_users = User.objects.filter(email__startswith="style_student_")
        mock_users.delete()

        # 5. Tạo 40 Học viên chia làm 4 nhóm
        # Nhom 1: Deep Learner (note > 0.05, skip_bwd > 0.05)
        # Nhom 2: Speed Runner (rate > 1.1, progress > 0.5)
        # Nhom 3: Struggling Learner (skip_bwd > 0.1, progress < 0.5)
        # Nhom 4: Passive Viewer (còn lại)
        
        group_configs = [
            {
                "name": "Deep Learner",
                "progress_range": (60, 90),
                "num_events": 50,
                "event_weights": {LearningEvent.EventType.PLAY: 40, LearningEvent.EventType.NOTE_CREATED: 20, LearningEvent.EventType.SKIP_BACKWARD_10: 40},
                "rate": 1.0
            },
            {
                "name": "Speed Runner",
                "progress_range": (80, 100),
                "num_events": 30,
                "event_weights": {LearningEvent.EventType.PLAY: 70, LearningEvent.EventType.SKIP_FORWARD_10: 30},
                "rate": 1.5
            },
            {
                "name": "Struggling Learner",
                "progress_range": (10, 40),
                "num_events": 40,
                "event_weights": {LearningEvent.EventType.PLAY: 30, LearningEvent.EventType.PAUSE: 20, LearningEvent.EventType.SKIP_BACKWARD_10: 50},
                "rate": 1.0
            },
            {
                "name": "Passive Viewer",
                "progress_range": (30, 70),
                "num_events": 15,
                "event_weights": {LearningEvent.EventType.PLAY: 90, LearningEvent.EventType.PAUSE: 10},
                "rate": 1.0
            }
        ]

        student_count = 0
        events_to_create = []

        for group_idx, config in enumerate(group_configs):
            for i in range(10): # 10 hs moi nhom
                student_count += 1
                email = f"style_student_{student_count}@test.com"
                u = User.objects.create(email=email, full_name=f"{config['name']} {i+1}")
                sp = StudentProfile.objects.create(user=u)
                
                enrolled_days = random.randint(15, 30)
                last_accessed = now - timedelta(days=random.randint(0, 5))
                progress = random.uniform(*config['progress_range'])
                
                enrollment = CourseEnrollment.objects.create(
                    student=sp,
                    course=course,
                    status=CourseEnrollment.Status.ACTIVE,
                    course_progress_percent=progress,
                    login_streak=random.randint(2, 10),
                )
                
                CourseEnrollment.objects.filter(id=enrollment.id).update(
                    enrolled_at=now - timedelta(days=enrolled_days),
                    last_accessed_at=last_accessed
                )
                
                # Tao events
                event_types = list(config["event_weights"].keys())
                weights = list(config["event_weights"].values())
                
                for _ in range(config["num_events"]):
                    event_type = random.choices(event_types, weights=weights, k=1)[0]
                    
                    rate = None
                    if config["rate"] > 1.0 and event_type == LearningEvent.EventType.PLAY:
                        rate = config["rate"]
                        
                    events_to_create.append(LearningEvent(
                        student=sp,
                        course=course,
                        video=video,
                        event_type=event_type,
                        playback_rate=rate,
                    ))

        created_events = LearningEvent.objects.bulk_create(events_to_create)
        # Update created_at
        for e in created_events:
            LearningEvent.objects.filter(event_id=e.event_id).update(created_at=now - timedelta(days=random.randint(0, 10)))

        self.stdout.write(f"[OK] Successfully created {student_count} mock students and {len(created_events)} events!")
        
        self.stdout.write("\n[VERIFICATION] Clustering Results:")
        res = cluster_learning_styles(course)
        if "clusters" in res:
            for cluster in res["clusters"]:
                self.stdout.write(f"- {cluster['icon']} {cluster['style_name']} ({cluster['count']} students)")
        else:
            self.stdout.write(f"Error: {res.get('error')}")
            
        self.stdout.write(f"\n[DONE] ID của khóa học kiểm chứng là: {course.course_id}")
