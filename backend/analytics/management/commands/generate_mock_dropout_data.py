"""Generate realistic mock data for dropout prediction.

Khớp schema DB: Course/Video/CourseEnrollment/LearningSession/LearningEvent/
VideoProgress — sinh đầy đủ field để feature pipeline (`build_dropout_features`)
và labelling (`label_dropout`) chạy đúng.

5 persona (per course):
  - diligent  : ACTIVE, progress 70-100%, vừa truy cập, có notes
  - completed : COMPLETED, progress 100%
  - at_risk   : ACTIVE, progress thấp, inactive 7-13 ngày, skip nhiều, tab ẩn
  - dropped   : DROPPED, progress thấp, inactive >=15 ngày
  - learning  : ACTIVE, progress 30-60%, truy cập gần đây
"""
from __future__ import annotations

import random
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from analytics.models import LearningEvent, LearningSession
from courses.models import Category, Course, CourseEnrollment
from users.models import InstructorProfile, StudentProfile
from videos.models import Video, VideoProgress

User = get_user_model()

PERSONAS = ["diligent", "completed", "at_risk", "dropped", "learning"]
PERSONA_MIX = {
    "diligent": 0.25,
    "completed": 0.15,
    "at_risk": 0.20,
    "dropped": 0.25,
    "learning": 0.15,
}

DEVICES = ["desktop", "mobile", "tablet"]
BROWSERS = ["Chrome 124", "Firefox 125", "Safari 17", "Edge 124"]


def pick_persona() -> str:
    r = random.random()
    cum = 0.0
    for name, w in PERSONA_MIX.items():
        cum += w
        if r <= cum:
            return name
    return "learning"


class Command(BaseCommand):
    help = "Sinh mock data khớp schema DB cho pipeline dropout."

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=120)
        parser.add_argument("--courses", type=int, default=3)
        parser.add_argument("--videos-per-course", type=int, default=5)
        parser.add_argument("--purge", action="store_true",
                            help="Xoá mock cũ (user/course/event mock_*) trước khi sinh.")

    @transaction.atomic
    def handle(self, *args, **opts):
        n_students = opts["students"]
        n_courses = opts["courses"]
        n_videos = opts["videos_per_course"]
        purge = opts["purge"]

        now = timezone.now()
        self.stdout.write(f"[i] Generating {n_students} students × {n_courses} courses × {n_videos} videos…")

        if purge:
            self._purge()

        cat, _ = Category.objects.get_or_create(category_name="Mock Category")
        instructor = self._ensure_instructor()
        courses = self._ensure_courses(instructor, cat, n_courses, n_videos)

        # Sinh student × persona
        counts = {p: 0 for p in PERSONAS}
        for i in range(n_students):
            persona = pick_persona()
            counts[persona] += 1
            student = self._create_student(i)
            # Mỗi student enroll vào 1-2 course để tăng đa dạng
            for course in random.sample(courses, k=random.randint(1, min(2, n_courses))):
                self._enroll(student, course, persona, now)

        self.stdout.write(self.style.SUCCESS("[OK] Mock data ready."))
        for p, c in counts.items():
            self.stdout.write(f"   - {p:9s}: {c} students")
        self.stdout.write(
            "\n[next] python mlops/pipelines/01_extract.py "
            "&& dvc repro"
        )

    # ---------- builders ----------

    def _purge(self):
        mock_users = User.objects.filter(email__startswith="mock_student_")
        self.stdout.write(f"[purge] removing {mock_users.count()} mock students…")
        mock_users.delete()
        Course.objects.filter(course_name__startswith="[MOCK]").delete()

    def _ensure_instructor(self) -> InstructorProfile:
        user, created = User.objects.get_or_create(
            email="mock_inst@test.com",
            defaults={"full_name": "Mock Instructor", "role": User.Role.INSTRUCTOR},
        )
        if created:
            user.set_password("password")
            user.save()
        inst, _ = InstructorProfile.objects.get_or_create(
            user=user, defaults={"profile_url": f"mock-inst-{uuid.uuid4().hex[:8]}"}
        )
        return inst

    def _ensure_courses(self, instructor, category, n_courses, n_videos):
        courses = []
        levels = [Course.Level.BEGINER, Course.Level.INTERMEDIATE, Course.Level.ADVANCED]
        for idx in range(n_courses):
            course, _ = Course.objects.get_or_create(
                course_name=f"[MOCK] Course {idx + 1}",
                defaults={
                    "instructor": instructor,
                    "category": category,
                    "status": Course.Status.PUBLISHED,
                    "level": levels[idx % len(levels)],
                    "language": "vi",
                },
            )
            # video orders 1..n
            for o in range(1, n_videos + 1):
                Video.objects.get_or_create(
                    course=course,
                    order=o,
                    defaults={
                        "title": f"Bài {o}",
                        "duration_seconds": random.randint(300, 1200),
                        "is_published": True,
                    },
                )
            courses.append(course)
        return courses

    def _create_student(self, i: int) -> StudentProfile:
        user = User.objects.create(
            email=f"mock_student_{i}@test.com",
            full_name=f"Mock Student {i}",
            role=User.Role.STUDENT,
        )
        user.set_password("password")
        user.save()
        return StudentProfile.objects.create(user=user)

    def _enroll(self, student, course, persona, now):
        cfg = self._persona_config(persona, now)
        videos = list(course.videos.all().order_by("order"))
        total_dur = sum(v.duration_seconds for v in videos) or 1
        watched_seconds = int(total_dur * cfg["progress"] / 100.0)

        enrollment = CourseEnrollment.objects.create(
            student=student,
            course=course,
            status=cfg["status"],
            course_progress_percent=cfg["progress"],
            total_watch_time_seconds=watched_seconds,
            videos_completed=int(len(videos) * cfg["progress"] / 100.0),
            login_streak=cfg["login_streak"],
        )
        # Override auto_now_add
        CourseEnrollment.objects.filter(id=enrollment.id).update(
            enrolled_at=now - timedelta(days=cfg["enrolled_days"]),
            last_accessed_at=cfg["last_accessed"],
            completed_at=cfg["last_accessed"] if persona == "completed" else None,
        )

        self._make_video_progress(student, videos, cfg, now)
        self._make_sessions_and_events(student, course, videos, cfg, now)

    def _persona_config(self, persona: str, now) -> dict:
        if persona == "diligent":
            return {
                "status": CourseEnrollment.Status.ACTIVE,
                "progress": random.uniform(70, 99),
                "enrolled_days": random.randint(20, 40),
                "last_accessed": now - timedelta(days=random.randint(0, 2)),
                "login_streak": random.randint(7, 20),
                "n_sessions": random.randint(15, 30),
                "events_per_session": (8, 25),
                "skip_fwd_prob": 0.05,
                "skip_bwd_prob": 0.15,
                "note_prob": 0.20,
                "rate_change_prob": 0.05,
                "hidden_prob": 0.05,
                "muted_prob": 0.05,
                "rate_choices": [1.0, 1.25],
            }
        if persona == "completed":
            return {
                "status": CourseEnrollment.Status.COMPLETED,
                "progress": 100.0,
                "enrolled_days": random.randint(30, 60),
                "last_accessed": now - timedelta(days=random.randint(0, 5)),
                "login_streak": random.randint(10, 25),
                "n_sessions": random.randint(20, 40),
                "events_per_session": (10, 30),
                "skip_fwd_prob": 0.05,
                "skip_bwd_prob": 0.15,
                "note_prob": 0.18,
                "rate_change_prob": 0.10,
                "hidden_prob": 0.05,
                "muted_prob": 0.05,
                "rate_choices": [1.0, 1.25, 1.5],
            }
        if persona == "at_risk":
            return {
                "status": CourseEnrollment.Status.ACTIVE,
                "progress": random.uniform(5, 25),
                "enrolled_days": random.randint(15, 30),
                "last_accessed": now - timedelta(days=random.randint(7, 13)),
                "login_streak": random.randint(0, 2),
                "n_sessions": random.randint(3, 8),
                "events_per_session": (3, 10),
                "skip_fwd_prob": 0.40,
                "skip_bwd_prob": 0.05,
                "note_prob": 0.01,
                "rate_change_prob": 0.20,
                "hidden_prob": 0.45,
                "muted_prob": 0.35,
                "rate_choices": [1.5, 2.0],
            }
        if persona == "dropped":
            return {
                "status": CourseEnrollment.Status.DROPPED,
                "progress": random.uniform(0, 25),
                "enrolled_days": random.randint(25, 45),
                "last_accessed": now - timedelta(days=random.randint(15, 30)),
                "login_streak": 0,
                "n_sessions": random.randint(2, 6),
                "events_per_session": (3, 8),
                "skip_fwd_prob": 0.35,
                "skip_bwd_prob": 0.05,
                "note_prob": 0.02,
                "rate_change_prob": 0.15,
                "hidden_prob": 0.40,
                "muted_prob": 0.30,
                "rate_choices": [1.5, 2.0],
            }
        # learning
        return {
            "status": CourseEnrollment.Status.ACTIVE,
            "progress": random.uniform(30, 60),
            "enrolled_days": random.randint(10, 25),
            "last_accessed": now - timedelta(days=random.randint(0, 4)),
            "login_streak": random.randint(3, 8),
            "n_sessions": random.randint(8, 15),
            "events_per_session": (5, 15),
            "skip_fwd_prob": 0.15,
            "skip_bwd_prob": 0.10,
            "note_prob": 0.10,
            "rate_change_prob": 0.08,
            "hidden_prob": 0.15,
            "muted_prob": 0.10,
            "rate_choices": [1.0, 1.25, 1.5],
        }

    def _make_video_progress(self, student, videos, cfg, now):
        progress = cfg["progress"] / 100.0
        rows = []
        for v in videos:
            r = max(0.0, min(1.0, random.gauss(progress, 0.15)))
            watched = int(v.duration_seconds * r)
            completed = r >= 0.95
            rows.append(VideoProgress(
                student=student,
                video=v,
                watched_seconds=watched,
                duration_seconds=v.duration_seconds,
                completed=completed,
                completed_at=cfg["last_accessed"] if completed else None,
                last_watched_at=cfg["last_accessed"],
            ))
        created = VideoProgress.objects.bulk_create(rows)
        # last_watched_at là auto-set bằng bulk; nhưng created_at là auto_now_add → bỏ qua
        # (extract pipeline không phụ thuộc created_at của VideoProgress)
        return created

    def _make_sessions_and_events(self, student, course, videos, cfg, now):
        ev_types = LearningEvent.EventType
        n_sessions = cfg["n_sessions"]
        spread_days = max((now - (cfg["last_accessed"] - timedelta(days=cfg["enrolled_days"]))).days, 1)

        for s_idx in range(n_sessions):
            # session bắt đầu trong cửa sổ [enrolled_at, last_accessed]
            offset_days = random.uniform(0, cfg["enrolled_days"])
            started_at = now - timedelta(days=offset_days, hours=random.randint(0, 23))
            if started_at > cfg["last_accessed"]:
                started_at = cfg["last_accessed"] - timedelta(hours=random.randint(1, 48))

            active_sec = random.randint(180, 2400)
            idle_sec = random.randint(0, 600)
            ended_at = started_at + timedelta(seconds=active_sec + idle_sec)

            lo, hi = cfg["events_per_session"]
            n_events = random.randint(lo, hi)

            session = LearningSession.objects.create(
                session_id=uuid.uuid4().hex,
                student=student,
                course=course,
                started_at=started_at,
                ended_at=ended_at,
                active_seconds=active_sec,
                idle_seconds=idle_sec,
                event_count=n_events,
                device_type=random.choice(DEVICES),
                browser=random.choice(BROWSERS),
                user_agent="MockUA/1.0",
            )

            events = []
            video = random.choice(videos)
            position = 0
            for _ in range(n_events):
                etype = self._pick_event_type(cfg, ev_types)
                playback_rate = None
                from_s = to_s = None
                delta = 0

                if etype == ev_types.RATE_CHANGE:
                    playback_rate = random.choice(cfg["rate_choices"])
                elif etype == ev_types.SKIP_FORWARD_10:
                    from_s = position
                    position = min(position + 10, video.duration_seconds)
                    to_s = position
                    delta = 10
                elif etype == ev_types.SKIP_BACKWARD_10:
                    from_s = position
                    position = max(position - 10, 0)
                    to_s = position
                    delta = -10
                elif etype == ev_types.SEEK:
                    from_s = position
                    position = random.randint(0, video.duration_seconds)
                    to_s = position
                    delta = to_s - from_s
                else:
                    position = min(position + random.randint(5, 60), video.duration_seconds)

                client_ts = started_at + timedelta(seconds=random.randint(0, max(active_sec, 1)))
                events.append(LearningEvent(
                    student=student,
                    course=course,
                    video=video,
                    event_type=etype,
                    position_seconds=position,
                    from_seconds=from_s,
                    to_seconds=to_s,
                    delta_seconds=delta,
                    playback_rate=playback_rate,
                    session=session,
                    client_timestamp=client_ts,
                    duration_ms=random.randint(50, 4000),
                    is_tab_hidden=random.random() < cfg["hidden_prob"],
                    is_fullscreen=random.random() < 0.10,
                    volume=round(random.uniform(0.3, 1.0), 2),
                    muted=random.random() < cfg["muted_prob"],
                    metadata={},
                ))
            created = LearningEvent.objects.bulk_create(events)
            # ép created_at vào cửa sổ session
            ids = [e.event_id for e in created]
            for eid in ids:
                LearningEvent.objects.filter(event_id=eid).update(
                    created_at=started_at + timedelta(seconds=random.randint(0, active_sec))
                )

    def _pick_event_type(self, cfg, ev_types):
        r = random.random()
        if r < cfg["skip_fwd_prob"]:
            return ev_types.SKIP_FORWARD_10
        r -= cfg["skip_fwd_prob"]
        if r < cfg["skip_bwd_prob"]:
            return ev_types.SKIP_BACKWARD_10
        r -= cfg["skip_bwd_prob"]
        if r < cfg["note_prob"]:
            return ev_types.NOTE_CREATED
        r -= cfg["note_prob"]
        if r < cfg["rate_change_prob"]:
            return ev_types.RATE_CHANGE
        # còn lại: PLAY/PAUSE/SEEK/PROGRESS_SYNC
        return random.choice([
            ev_types.PLAY, ev_types.PAUSE, ev_types.SEEK, ev_types.PROGRESS_SYNC
        ])
