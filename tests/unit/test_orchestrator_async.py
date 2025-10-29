import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from apps.backend.services.orchestrator import EvaluationOrchestrator
from apps.core.schemas import LeaderboardQuery, ModelInfo


@pytest.fixture
def sample_query():
    return LeaderboardQuery(
        query="Evaluate models",
        models=[
            ModelInfo(
                name="test-model",
                api_base="https://api.example.com",
                api_key="secret-key",
                model_type="openai",
            )
        ],
    )


@pytest.fixture
def planner_plan():
    return {
        "plan_yaml": "version: 1",
        "models": [
            {
                "name": "test-model",
                "api_base": "https://api.example.com",
                "api_key": "secret-key",
                "model_type": "openai",
            }
        ],
        "config": {
            "language": "English",
            "subject_type": "General",
            "task_type": "QA",
            "sample_size": 10,
        },
    }


def _build_orchestrator(planner_plan):
    mock_db = MagicMock()

    tasks_repo = MagicMock()
    tasks_repo.create_task.return_value = SimpleNamespace(task_id="task-123")

    leaderboard_repo = MagicMock()
    leaderboard_repo.get_cached_entry.return_value = None

    planner_agent = MagicMock()
    planner_agent.create_evaluation_plan.return_value = planner_plan

    patches = [
        patch(
            "apps.backend.services.orchestrator.TasksRepository",
            return_value=tasks_repo,
        ),
        patch(
            "apps.backend.services.orchestrator.LeaderboardRepository",
            return_value=leaderboard_repo,
        ),
        patch(
            "apps.backend.services.orchestrator.create_planner_agent",
            return_value=planner_agent,
        ),
    ]

    for active_patch in patches:
        active_patch.start()

    orchestrator = EvaluationOrchestrator(mock_db)

    for active_patch in reversed(patches):
        active_patch.stop()

    return orchestrator, tasks_repo, planner_agent


def test_generate_leaderboard_dispatches_async(sample_query, planner_plan):
    orchestrator, tasks_repo, planner_agent = _build_orchestrator(planner_plan)

    with patch("apps.worker.tasks.run_evaluation") as mock_run_evaluation:
        async_result = MagicMock()
        async_result.id = "celery-1"
        mock_run_evaluation.delay.return_value = async_result

        response = orchestrator.generate_leaderboard(sample_query)

    assert response.status == "PENDING"
    assert "asynchronous" in response.message.lower()

    assert mock_run_evaluation.delay.call_count == 1
    dispatched_args = mock_run_evaluation.delay.call_args[0]
    assert dispatched_args[0] == response.task_id
    json.loads(dispatched_args[1])

    planner_agent.create_evaluation_plan.assert_called_once_with(
        sample_query.query, sample_query.models
    )
    tasks_repo.update_task_status.assert_not_called()


def test_generate_leaderboard_dispatch_failure_marks_task(sample_query, planner_plan):
    orchestrator, tasks_repo, _ = _build_orchestrator(planner_plan)

    with patch("apps.worker.tasks.run_evaluation") as mock_run_evaluation:
        mock_run_evaluation.delay.side_effect = RuntimeError("queue offline")

        with pytest.raises(RuntimeError, match="Failed to dispatch evaluation task"):
            orchestrator.generate_leaderboard(sample_query)

    tasks_repo.update_task_status.assert_called_once()
    args, kwargs = tasks_repo.update_task_status.call_args
    created_task_id = tasks_repo.create_task.call_args[0][0]
    assert args[0] == created_task_id
    assert args[1] == "FAILURE"
    assert "queue offline" in kwargs.get("error_message", "")
