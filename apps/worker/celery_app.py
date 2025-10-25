"""Celery application configuration."""

import logging
from celery import Celery

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create Celery application
celery_app = Celery(
    "benchhub_plus",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["apps.worker.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
)

# Task routing
celery_app.conf.task_routes = {
    "apps.worker.tasks.run_evaluation": {"queue": "evaluation"},
    "apps.worker.tasks.cleanup_task": {"queue": "maintenance"},
}

# Configure logging
celery_app.conf.worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
celery_app.conf.worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"

logger.info("Celery application configured")

if __name__ == "__main__":
    celery_app.start()