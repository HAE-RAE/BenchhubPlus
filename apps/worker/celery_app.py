"""Celery application configuration."""

import logging
from urllib.parse import urlparse

from celery import Celery
from kombu import Queue

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Hostnames that resolve only inside the deployment's private network and
# therefore have the same security posture as localhost. Anyone on these
# networks already has shell on a sibling container, so requiring an extra
# in-URL password adds no real protection.
_PRIVATE_BROKER_SUFFIXES = (
    ".railway.internal",
    ".internal.railway.app",
    ".flycast",
    ".internal",  # Fly.io / generic compose-net suffix
    ".svc.cluster.local",  # Kubernetes
)

_PRIVATE_BROKER_HOSTS = {"localhost", "127.0.0.1", "redis", "rabbitmq"}


def _broker_has_auth(url: str) -> bool:
    """Return True if the broker URL embeds credentials, uses TLS, or
    resolves to a host we treat as trusted-private."""
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.password:
        return True
    if parsed.scheme in {"rediss", "amqps"}:
        return True
    host = (parsed.hostname or "").lower()
    if not host:
        return True  # malformed URL — let Celery surface the real error
    if host in _PRIVATE_BROKER_HOSTS:
        return True
    if any(host.endswith(suffix) for suffix in _PRIVATE_BROKER_SUFFIXES):
        return True
    return False


# In production, refuse to boot with an unauthenticated *public* broker. An
# unauthenticated Redis reachable from the open internet is effectively an
# RCE primitive (anyone who can enqueue a message runs code on the worker).
if settings.is_production and not _broker_has_auth(settings.celery_broker_url):
    parsed = urlparse(settings.celery_broker_url or "")
    raise RuntimeError(
        "CELERY_BROKER_URL must include credentials, use rediss://, or point "
        "at a private deployment hostname (e.g. *.railway.internal, "
        "*.svc.cluster.local) when running outside debug mode. "
        f"Got scheme={parsed.scheme!r} host={parsed.hostname!r} "
        f"has_password={bool(parsed.password)}."
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

# Task routing. The matching queues are also declared in ``task_queues`` so a
# worker started without an explicit ``-Q`` flag still subscribes to every
# routed destination — otherwise messages silently pile up on a queue nobody
# is listening to.
celery_app.conf.task_routes = {
    "apps.worker.tasks.run_evaluation": {"queue": "evaluation"},
    "apps.worker.tasks.cleanup_task": {"queue": "maintenance"},
}
celery_app.conf.task_queues = (
    Queue("celery"),
    Queue("evaluation"),
    Queue("maintenance"),
)
celery_app.conf.task_default_queue = "celery"

# Configure logging
celery_app.conf.worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
celery_app.conf.worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"

logger.info("Celery application configured")

if __name__ == "__main__":
    celery_app.start()