from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Deprecated. Use `dvc repro train_dropout` or run mlops/pipelines/04_train_dropout.py."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            "Training in Django is deprecated. Run the offline pipeline:"
        ))
        self.stdout.write("  dvc repro train_dropout")
        self.stdout.write("  python mlops/pipelines/04_train_dropout.py")
        self.stdout.write("")
        self.stdout.write(
            "Then refresh the serving cache: python manage.py reload_models"
        )
