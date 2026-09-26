from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "finsight_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes default hard timeout
    task_soft_time_limit=240,
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
)

# Celery Beat recurring schedules (§38)
celery_app.conf.beat_schedule = {
    "refresh-holding-prices-hourly": {
        "task": "app.workers.tasks.refresh_holding_prices",
        "schedule": crontab(minute=0),  # every hour on the hour
    },
    "scheduled-watchlist-scan-daily": {
        "task": "app.workers.tasks.scheduled_watchlist_scan",
        "schedule": crontab(hour=6, minute=0),  # every day at 06:00 UTC
    },
}
