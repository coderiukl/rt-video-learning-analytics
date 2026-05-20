from django.core.management.base import BaseCommand

from analytics.ml.registry import invalidate


class Command(BaseCommand):
    help = "Clear cached models. Next prediction reloads from MLflow registry or local pkl."

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            default=None,
            help="Model name to invalidate (default: all).",
        )

    def handle(self, *args, **options):
        name = options.get("name")
        invalidate(name)
        target = name or "all models"
        self.stdout.write(self.style.SUCCESS(f"Cache cleared for {target}."))
