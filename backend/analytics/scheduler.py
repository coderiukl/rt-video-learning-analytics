import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.utils import timezone
from .dropout_predictor import train_model

logger = logging.getLogger(__name__)

def automated_train_model_job():
    logger.info("Bắt đầu tự động huấn luyện lại model Dropout Prediction...")
    try:
        res = train_model()
        if res.get("success"):
            logger.info(f"✅ Auto-train thành công! Accuracy: {res.get('accuracy')}")
        else:
            logger.error(f"❌ Auto-train thất bại: {res.get('message')}")
    except Exception as e:
        logger.error(f"❌ Lỗi khi tự động train model: {e}")

def start():
    """Khởi chạy scheduler ngầm."""
    scheduler = BackgroundScheduler(timezone=timezone.get_current_timezone())
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Chạy mỗi ngày lúc 2:00 AM
    scheduler.add_job(
        automated_train_model_job,
        trigger="cron",
        hour=2,
        minute=0,
        id="daily_dropout_model_training",
        max_instances=1,
        replace_existing=True,
    )

    register_events(scheduler)
    scheduler.start()
    logger.info("Scheduler đã được khởi động. Model sẽ tự động retrain vào 02:00 AM mỗi ngày.")
