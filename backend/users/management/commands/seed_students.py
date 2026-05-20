from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import StudentProfile, User


class Command(BaseCommand):
    help = "Tạo 20 học viên mẫu: hocvien1..20@gmail.com / p12345@@"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=20)
        parser.add_argument("--password", type=str, default="p12345@@")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Xoá học viên cũ có email trùng trước khi tạo lại",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        count = opts["count"]
        password = opts["password"]
        reset = opts["reset"]

        created, skipped = 0, 0
        for i in range(1, count + 1):
            email = f"hocvien{i}@gmail.com"
            full_name = f"Học viên {i}"

            if reset:
                User.objects.filter(email=email).delete()

            if User.objects.filter(email=email).exists():
                skipped += 1
                self.stdout.write(self.style.WARNING(f"= Bỏ qua (đã tồn tại): {email}"))
                continue

            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=User.Role.STUDENT,
                is_email_verified=True,
            )
            StudentProfile.objects.get_or_create(user=user)
            created += 1
            self.stdout.write(self.style.SUCCESS(f"+ {email}  |  {full_name}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nHoàn tất: tạo {created}, bỏ qua {skipped}. Mật khẩu: {password}"
        ))
