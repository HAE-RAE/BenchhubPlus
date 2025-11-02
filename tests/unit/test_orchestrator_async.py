import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from apps.backend.services.orchestrator import EvaluationOrchestrator
from apps.core.schemas import LeaderboardQuery, ModelInfo, PlanConfig


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


def test_suggest_filters_uses_planner_recommendation(planner_plan):
    orchestrator, _, planner_agent = _build_orchestrator(planner_plan)
    plan_config = PlanConfig(
        problem_type="MCQA",
        target_type="General",
        subject_type=["Science", "Science/Math"],
        task_type="Reasoning",
        external_tool_usage=False,
        language="Korean",
        sample_size=50,
    )
    planner_agent.parse_query.return_value = plan_config

    suggestion = orchestrator.suggest_leaderboard_filters("한국어 과학 추론 문제를 보고 싶어요")

    assert suggestion.used_planner is True
    assert suggestion.language == "Korean"
    assert suggestion.subject_type == "Science/Math"
    assert suggestion.task_type == "Reasoning"
    assert suggestion.subject_type_options == ["Science", "Science/Math"]
    assert "plan_config" in suggestion.metadata
    assert "Korean" in suggestion.plan_summary


def test_suggest_filters_empty_query_returns_full_leaderboard(planner_plan):
    orchestrator, _, planner_agent = _build_orchestrator(planner_plan)
    suggestion = orchestrator.suggest_leaderboard_filters("   ")

    assert suggestion.used_planner is False
    assert suggestion.language is None
    assert suggestion.subject_type is None
    assert suggestion.task_type is None
    assert suggestion.plan_summary == "필터 없이 전체 리더보드를 보여드릴게요."


def test_suggest_filters_falls_back_when_planner_errors(planner_plan):
    orchestrator, _, planner_agent = _build_orchestrator(planner_plan)
    planner_agent.parse_query.side_effect = RuntimeError("planner offline")

    suggestion = orchestrator.suggest_leaderboard_filters("Show me coding evaluations")

    assert suggestion.used_planner is False
    assert suggestion.language == "English"
    assert suggestion.subject_type == "Science"
    assert suggestion.task_type == "Knowledge"
    assert suggestion.subject_type_options == ["Science"]
    assert suggestion.metadata.get("planner_error") == "planner offline"
