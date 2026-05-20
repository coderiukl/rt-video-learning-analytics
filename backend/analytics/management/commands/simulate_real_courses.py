"""Mô phỏng học viên hocvien*@gmail.com học các khóa thật của giangvien1..5.

Logic:
  - Tìm tất cả StudentProfile có user.email khớp ^hocvien\\d+@gmail.com$.
  - Bỏ qua HV đã có CourseEnrollment (đã đăng ký bất kỳ khóa nào).
  - Với HV còn lại: chọn persona theo PERSONA_MIX, enroll vào 1-2 course
    published thực tế (loại [MOCK]) rồi sinh VideoProgress + LearningSession
    + LearningEvent y hệt generate_mock_dropout_data để feed pipeline dropout.
"""
from __future__ import annotations

import random
import re

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from analytics.management.commands.generate_mock_dropout_data import (
    Command as MockDropoutCommand,
    PERSONAS,
    pick_persona,
)
from courses.models import Course, CourseEnrollment
from users.models import StudentProfile

EMAIL_RE = re.compile(r"^hocvien\d+@gmail\.com$")


class Command(BaseCommand):
    help = "Sinh learning data cho hocvien*@gmail.com chưa enroll, dùng course thật."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email-pattern", type=str, default=r"^hocvien\d+@gmail\.com$",
            help="Regex email HV cần xử lý (default: hocvien*@gmail.com).",
        )
        parser.add_argument(
            "--min-courses", type=int, default=1,
            help="Số course tối thiểu mỗi HV enroll.",
        )
        parser.add_argument(
            "--max-courses", type=int, default=2,
            help="Số course tối đa mỗi HV enroll.",
        )
        parser.add_argument(
            "--include-mock-courses", action="store_true",
            help="Bao gồm cả [MOCK] courses trong pool (mặc định: loại).",
        )
        parser.add_argument(
            "--seed", type=int, default=None,
            help="Random seed (debug/reproduce).",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Chỉ in plan, không ghi DB.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["seed"] is not None:
            random.seed(opts["seed"])

        email_re = re.compile(opts["email_pattern"])
        min_c, max_c = opts["min_courses"], opts["max_courses"]

        # Pool course
        course_qs = Course.objects.filter(status=Course.Status.PUBLISHED)
        if not opts["include_mock_courses"]:
            course_qs = course_qs.exclude(course_name__startswith="[MOCK]")
        courses = list(course_qs)
        if not courses:
            self.stdout.write(self.style.ERROR("Không có course PUBLISHED phù hợp."))
            return

        self.stdout.write(f"[i] Pool {len(courses)} course PUBLISHED:")
        for c in courses:
            self.stdout.write(f"   - #{c.course_id} {c.course_name}  ({c.instructor.user.email})")

        # HV thuộc pattern
        students = (
            StudentProfile.objects
            .filter(user__email__regex=opts["email_pattern"])
            .select_related("user")
            .prefetch_related("enrollments")
        )
        students = [s for s in students if email_re.match(s.user.email)]
        self.stdout.write(f"\n[i] Tổng HV khớp pattern: {len(students)}")

        targets = []
        skipped = []
        for sp in students:
            if sp.enrollments.exists():
                skipped.append(sp)
            else:
                targets.append(sp)

        self.stdout.write(f"   - đã enroll → bỏ qua: {len(skipped)}")
        self.stdout.write(f"   - chưa enroll → xử lý: {len(targets)}")

        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("\n[dry-run] dừng tại đây."))
            return

        if not targets:
            self.stdout.write(self.style.SUCCESS("Không còn HV nào cần xử lý."))
            return

        # Tái sử dụng helpers từ MockDropoutCommand
        helper = MockDropoutCommand()
        helper.stdout = self.stdout
        helper.style = self.style

        now = timezone.now()
        counts = {p: 0 for p in PERSONAS}
        enroll_count = 0

        for sp in targets:
            persona = pick_persona()
            counts[persona] += 1
            k = random.randint(min_c, min(max_c, len(courses)))
            for course in random.sample(courses, k=k):
                # phòng race: nếu đã có enrollment (vd. chạy lại) → bỏ qua
                if CourseEnrollment.objects.filter(student=sp, course=course).exists():
                    continue
                helper._enroll(sp, course, persona, now)
                enroll_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n[OK] Xử lý {len(targets)} HV → {enroll_count} enrollment mới."
        ))
        for p, c in counts.items():
            self.stdout.write(f"   - {p:9s}: {c} HV")
        self.stdout.write(
            "\n[next] python mlops/pipelines/01_extract.py && dvc repro"
        )
