"""Background scheduler.

We keep a daily job to invalidate the in-process model cache so the serving
side picks up new model versions promoted to the registry by the CI/CD pipeline.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.utils import timezone

from .services.dropout_service import reload as reload_dropout_model

logger = logging.getLogger(__name__)


def refresh_model_cache_job():
    logger.info("Refreshing dropout model cache from registry...")
    try:
        reload_dropout_model()
        logger.info("Model cache invalidated; next predict will reload.")
    except Exception as exc:
        logger.error("Failed to invalidate model cache: %s", exc)


def start():
    scheduler = BackgroundScheduler(timezone=timezone.get_current_timezone())
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Job: Refresh cache (02:15 AM)
    scheduler.add_job(
        refresh_model_cache_job,
        trigger="cron",
        hour=2,
        minute=15,
        id="daily_dropout_model_cache_refresh",
        max_instances=1,
        replace_existing=True,
    )

    register_events(scheduler)
    scheduler.start()
    logger.info(
        "Scheduler started. Model cache will be refreshed daily at 02:15."
    )
