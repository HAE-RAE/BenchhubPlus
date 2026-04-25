"""Celery application configuration."""

import logging
from urllib.parse import urlparse

from celery import Celery

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _broker_has_auth(url: str) -> bool:
    """Return True if the broker URL embeds credentials or uses TLS."""
    if not url:
        return False
    parsed = urlparse(url)
    has_password = bool(parsed.password)
    is_tls = parsed.scheme in {"rediss", "amqps"}
    is_local = parsed.hostname in {"localhost", "127.0.0.1", None}
    return has_password or is_tls or is_local


# In production, refuse to boot with an unauthenticated remote broker. An
# unauthenticated Redis reachable from the worker is effectively an RCE
# primitive (anyone who can enqueue a message runs code on the worker).
if settings.is_production and not _broker_has_auth(settings.celery_broker_url):
    raise RuntimeError(
        "CELERY_BROKER_URL must include credentials (or use rediss://) when "
        "running outside debug mode. Set a password on Redis and embed it "
        "in the URL, e.g. redis://:<password>@host:6379/0."
    )

# Create Celery application
celery_app = Celery(
    "benchhub_plus",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["apps.worker.tasks"]
)

# JSON-only serialization closes the pickle-RCE foot-gun.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_protocol=2,
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,
    # Acknowledge messages only after they finish so a crashed worker does
    # not silently drop in-flight evaluations.
    task_acks_late=True,
    task_reject_on_worker_lost=True,
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