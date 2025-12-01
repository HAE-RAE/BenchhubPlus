"""Unit tests for manager-facing repositories."""

from apps.backend.repositories.tasks_repo import TasksRepository
from apps.backend.repositories.leaderboard_repo import LeaderboardRepository


def test_filter_tasks_with_status_and_pagination(test_db):
    """TasksRepository.filter_tasks should filter by status and paginate."""
    repo = TasksRepository(test_db)
    repo.create_task("task_pending", plan_details="{}", model_count=2)
    repo.create_task("task_running", plan_details="{}", model_count=3)
    repo.update_task_status("task_running", "STARTED")

    tasks, total = repo.filter_tasks(statuses=["PENDING"], page=1, page_size=10)
    assert total == 1
    assert len(tasks) == 1
    assert tasks[0].task_id == "task_pending"


def test_cancel_task_sets_cancelled_status(test_db):
    """Cancel should soft fail tasks."""
    repo = TasksRepository(test_db)
    repo.create_task("task_cancel", plan_details="{}", model_count=1)
    assert repo.cancel_task("task_cancel") is True
    task = repo.get_task("task_cancel")
    assert task.status == "CANCELLED"
    assert task.error_message == "Task cancelled by user"


def test_leaderboard_soft_delete_and_filter(test_db):
    """Soft deleted leaderboard entries should be quarantined and hidden."""
    repo = LeaderboardRepository(test_db)
    entry = repo.manual_entry(
        model_name="test-model",
        language="English",
        subject_type="Math",
        task_type="QA",
        score=0.9,
    )
    assert entry.quarantined is False
    repo.soft_delete(entry.id, quarantine=True)
    hidden = repo.get_leaderboard(language="English", subject_type="Math", task_type="QA")
    assert hidden == []
    stored = repo.get_by_id(entry.id)
    assert stored.quarantined is True
    assert stored.deleted_at is not None
