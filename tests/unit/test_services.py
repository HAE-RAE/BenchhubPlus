"""Unit tests for core services (orchestrator, audit)."""

import json
from datetime import datetime
from unittest.mock import Mock

import pytest

from apps.backend.repositories.leaderboard_repo import LeaderboardRepository
from apps.backend.repositories.tasks_repo import TasksRepository
from apps.backend.services.audit import AuditService
from apps.backend.services.orchestrator import EvaluationOrchestrator
from apps.core.credential_service import StoredCredential
from apps.core.schemas import LeaderboardQuery, ModelInfo


@pytest.fixture
def orchestrator_with_mock_planner(test_db):
    """Provide an orchestrator with a mocked planner and credential service."""
    orchestrator = EvaluationOrchestrator(test_db)

    # Mock planner to avoid external LLM dependency
    plan_metadata = {
        "config": {
            "language": "English",
            "subject_type": ["Science/Math"],
            "task_type": "Reasoning",
            "problem_type": "MCQA",
            "target_type": "General",
            "external_tool_usage": False,
            "sample_size": 10,
        },
        "models": [
            {"name": "test-model", "api_base": "https://api.test.com", "model_type": "openai"},
        ],
    }
    orchestrator.planner_agent = Mock()
    orchestrator.planner_agent.create_evaluation_plan.return_value = plan_metadata

    # Mock credential service to avoid storing secrets in test DB
    stored = [
        StoredCredential(
            id=1,
            credential_hash="hash-1",
            model_name="test-model",
            api_base="https://api.test.com",
            model_type="openai",
        )
    ]
    orchestrator.credential_service = Mock()
    orchestrator.credential_service.register_models.return_value = stored

    return orchestrator


def test_generate_leaderboard_returns_cache_hit(test_db, orchestrator_with_mock_planner):
    """Cache hit should short-circuit task to SUCCESS with cached payload."""
    # Seed cache for the query criteria
    repo = LeaderboardRepository(test_db)
    repo.upsert_entry(
        model_name="test-model",
        language="English",
        subject_type="Science/Math",
        task_type="Reasoning",
        score=0.95,
    )

    query = LeaderboardQuery(
        query="Evaluate math reasoning",
        models=[
            ModelInfo(
                name="test-model",
                api_base="https://api.test.com",
                api_key="sk-test",
                model_type="openai",
            )
        ],
    )

    result = orchestrator_with_mock_planner.generate_leaderboard(query)
    # Cache hit path should mark task as SUCCESS
    assert result.status == "SUCCESS"
    assert "Results retrieved from cache" in result.message or "cache" in result.message.lower()

    # Task record should be persisted with SUCCESS state and cached result
    tasks_repo = TasksRepository(test_db)
    task = tasks_repo.get_task(result.task_id)
    assert task is not None
    assert task.status == "SUCCESS"
    assert task.result is not None
    cached_payload = json.loads(task.result)
    assert cached_payload.get("cache_hit") is True
    assert cached_payload["total_models"] == 1


def test_get_system_stats_includes_cache_count(test_db):
    """System stats should report cache entries and task counts."""
    repo = LeaderboardRepository(test_db)
    repo.upsert_entry(
        model_name="stats-model",
        language="English",
        subject_type="Science/Math",
        task_type="Reasoning",
        score=0.5,
    )

    orchestrator = EvaluationOrchestrator(test_db)
    stats = orchestrator.get_system_stats()

    assert stats["cache_entries"] >= 1
    assert "tasks" in stats
    assert all(key in stats["tasks"] for key in ["PENDING", "SUCCESS", "FAILURE", "TOTAL"])


def test_audit_service_writes_and_lists_entries(test_db):
    """AuditService should persist and return audit entries."""
    service = AuditService(test_db)
    entry = service.log_action(
        action="test.action",
        resource="leaderboard",
        resource_id="123",
        user_id=42,
        metadata={"foo": "bar"},
    )

    logs, total = service.list_logs(limit=10, offset=0)
    assert total == 1
    assert logs[0].id == entry.id
    assert logs[0].action == "test.action"
    assert logs[0].resource == "leaderboard"
    assert logs[0].user_id == 42
