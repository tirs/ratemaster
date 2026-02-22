"""Celery application for Redis-backed background jobs."""
from celery import Celery

from app.config import settings

celery_app = Celery(
    "ratemaster",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.engine", "app.tasks.market", "app.tasks.ingestion", "app.tasks.training"],
)

# Beat runs every 5 min; adaptive cadence in refresh_all_market_signals
# uses per-property market_refresh_minutes (or global) to skip recently refreshed
refresh_seconds = 300.0

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    beat_schedule={
        "refresh-market-signals": {
            "task": "app.tasks.market.refresh_all_market_signals",
            "schedule": float(refresh_seconds),
        },
        "run-training-jobs": {
            "task": "app.tasks.training.run_training_jobs_scheduled",
            "schedule": 86400.0,  # daily
        },
    },
)
