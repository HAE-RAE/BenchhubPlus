"""Tests for maintenance cleanup API and status."""

from unittest.mock import Mock

import pytest

from apps.backend.main import app
from apps.backend.routes import status as status_routes
from apps.backend.dependencies import require_admin


@pytest.fixture
def admin_override():
    """Override admin dependency with a dummy admin user."""
    admin = Mock()
    admin.id = 1
    admin.is_admin = True
    admin.role = "admin"
    app.dependency_overrides[require_admin] = lambda: admin
    yield
    app.dependency_overrides.pop(require_admin, None)


def test_schedule_cleanup_defaults(client, admin_override, monkeypatch):
    """POST should return 202 with pending status and progress metadata."""

    class DummyResult:
        id = "cleanup-task-1"

    monkeypatch.setattr(status_routes.cleanup_task, "delay", lambda **kwargs: DummyResult())

    resp = client.post("/api/v1/maintenance/cleanup", json={"dry_run": True})
    assert resp.status_code == 202
    payload = resp.json()
    assert payload["task_id"] == "cleanup-task-1"
    assert payload["status"] == "PENDING"
    assert payload["progress"]["total"] == 3  # tasks, samples, cache
    assert payload["summary"]["dry_run"] is True


def test_schedule_cleanup_validation_error(client, admin_override):
    """Invalid resources should trigger validation error."""
    resp = client.post(
        "/api/v1/maintenance/cleanup",
        json={"resources": ["invalid"], "days_old": 7},
    )
    assert resp.status_code == 422


def test_get_cleanup_status_running(client, admin_override, monkeypatch):
    """Status endpoint should surface progress and running state."""

    class DummyAsyncResult:
        state = "PROGRESS"
        result = None

        @property
        def info(self):
            return {
                "progress": {"current": 1, "total": 3, "stage": "tasks", "eta_seconds": 10},
                "resources": {"tasks": {"deleted": 5, "errors": [], "skipped": 0}},
                "summary": {"dry_run": True},
            }

    monkeypatch.setattr(status_routes.celery_app, "AsyncResult", lambda task_id: DummyAsyncResult())

    resp = client.get("/api/v1/maintenance/cleanup/cleanup-task-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "RUNNING"
    assert data["progress"]["stage"] == "tasks"
    assert data["resources"]["tasks"]["deleted"] == 5
    assert data["dry_run"] is True


def test_get_cleanup_status_failure_with_non_dict_info(client, admin_override, monkeypatch):
    """Non-dict info should still return last_error."""

    class DummyAsyncResult:
        state = "FAILURE"
        result = RuntimeError("boom")
        info = "boom-info"

    monkeypatch.setattr(status_routes.celery_app, "AsyncResult", lambda task_id: DummyAsyncResult())

    resp = client.get("/api/v1/maintenance/cleanup/cleanup-task-err")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "FAILED"
    assert data["last_error"] == "boom-info"
