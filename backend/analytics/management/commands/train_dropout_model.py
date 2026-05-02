"""
Management command để train Dropout Prediction model.
Chạy: python manage.py train_dropout_model
"""

from django.core.management.base import BaseCommand

from analytics.dropout_predictor import train_model


class Command(BaseCommand):
    help = "Train RandomForest model cho Dropout Prediction từ dữ liệu CourseEnrollment hiện có."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🚀 Bắt đầu training Dropout Prediction model..."))
        self.stdout.write("")

        result = train_model()

        if not result.get("success"):
            self.stdout.write(self.style.ERROR(f"❌ Training thất bại: {result.get('message', 'Unknown error')}"))
            self.stdout.write(f"   Số mẫu hiện có: {result.get('num_samples', 0)}")
            return

        self.stdout.write(self.style.SUCCESS("✅ Training hoàn tất!"))
        self.stdout.write(f"   📊 Tổng số mẫu: {result['num_samples']}")
        self.stdout.write(f"   🔴 Dropout:     {result['num_dropout']}")
        self.stdout.write(f"   🟢 Active:      {result['num_active']}")

        if result.get("accuracy") is not None:
            self.stdout.write(f"   🎯 CV Accuracy: {result['accuracy']:.2%}")

        self.stdout.write(f"   💾 Model saved: {result['model_path']}")

        if result.get("feature_importances"):
            self.stdout.write("")
            self.stdout.write(self.style.NOTICE("📈 Feature Importances:"))
            sorted_feats = sorted(
                result["feature_importances"].items(),
                key=lambda x: x[1],
                reverse=True,
            )
            for name, importance in sorted_feats:
                bar = "█" * int(importance * 50)
                self.stdout.write(f"   {name:20s} {importance:.4f} {bar}")
