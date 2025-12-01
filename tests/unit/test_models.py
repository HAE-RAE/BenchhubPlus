"""Unit tests for database models aligned with current schema."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from apps.core.models import EvaluationTask, ExperimentSample, LeaderboardCache


class TestLeaderboardCache:
    """Test LeaderboardCache model."""

    def test_create_leaderboard_cache(self, test_db):
        """Creating an entry populates key fields."""
        cache = LeaderboardCache(
            model_name="test-model",
            score=0.85,
            language="English",
            subject_type="Science/Math",
            task_type="Reasoning",
        )

        test_db.add(cache)
        test_db.commit()
        test_db.refresh(cache)

        assert cache.id is not None
        assert cache.model_name == "test-model"
        assert cache.score == 0.85
        assert cache.language == "English"
        assert cache.subject_type == "Science/Math"
        assert cache.task_type == "Reasoning"
        assert cache.last_updated is not None

    def test_leaderboard_cache_required_fields(self, test_db):
        """Required fields enforced by DB."""
        with pytest.raises(IntegrityError):
            cache = LeaderboardCache(
                score=0.85,
                language="English",
                subject_type="Science/Math",
                task_type="Reasoning",
            )
            test_db.add(cache)
            test_db.commit()

    def test_leaderboard_cache_defaults(self, test_db):
        """Defaults set for quarantine and timestamps."""
        cache = LeaderboardCache(
            model_name="test-model",
            score=0.85,
            language="English",
            subject_type="Science/Math",
            task_type="Reasoning",
        )

        test_db.add(cache)
        test_db.commit()
        test_db.refresh(cache)

        assert cache.quarantined is False
        assert cache.deleted_at is None
        assert cache.created_at is not None
        assert isinstance(cache.last_updated, datetime)


class TestEvaluationTask:
    """Test EvaluationTask model."""

    def test_create_evaluation_task(self, test_db):
        """Creating a task sets metadata fields."""
        task = EvaluationTask(
            task_id="test-task-id",
            status="PENDING",
            plan_details="{}",
            request_payload='{"query": "Test"}',
            model_count=2,
            policy_tags='["policy_a"]',
        )

        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        assert task.task_id == "test-task-id"
        assert task.status == "PENDING"
        assert task.plan_details == "{}"
        assert task.request_payload == '{"query": "Test"}'
        assert task.model_count == 2
        assert task.policy_tags == '["policy_a"]'
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_evaluation_task_status_update(self, test_db):
        """Status transitions persist."""
        task = EvaluationTask(
            task_id="test-task-id",
            status="PENDING",
        )

        test_db.add(task)
        test_db.commit()

        task.status = "STARTED"
        test_db.commit()
        test_db.refresh(task)

        assert task.status == "STARTED"
        assert task.completed_at is None

    def test_evaluation_task_completion(self, test_db):
        """Completion sets timestamps and result."""
        task = EvaluationTask(
            task_id="test-task-id",
            status="STARTED",
        )

        test_db.add(task)
        test_db.commit()

        task.status = "SUCCESS"
        task.completed_at = datetime.now(timezone.utc)
        task.result = '{"result": "ok"}'

        test_db.commit()
        test_db.refresh(task)

        assert task.status == "SUCCESS"
        assert task.completed_at is not None
        assert task.result is not None

    def test_evaluation_task_failure(self, test_db):
        """Failure sets error message."""
        task = EvaluationTask(
            task_id="test-task-id",
            status="STARTED",
        )

        test_db.add(task)
        test_db.commit()

        task.status = "FAILURE"
        task.completed_at = datetime.now(timezone.utc)
        task.error_message = "Test error"

        test_db.commit()
        test_db.refresh(task)

        assert task.status == "FAILURE"
        assert task.completed_at is not None
        assert task.error_message == "Test error"


class TestExperimentSample:
    """Test ExperimentSample model."""

    def test_create_experiment_sample(self, test_db):
        """Creating an experiment sample."""
        sample = ExperimentSample(
            prompt="What is 2+2?",
            answer="4",
            skill_label="math",
            target_label="arithmetic",
            subject_label="Science/Math",
            format_label="QA",
            dataset_name="testset",
            correctness=1.0,
            meta_data='{"category": "math"}',
        )

        test_db.add(sample)
        test_db.commit()
        test_db.refresh(sample)

        assert sample.id is not None
        assert sample.prompt == "What is 2+2?"
        assert sample.correctness == 1.0
        assert sample.dataset_name == "testset"
        assert isinstance(sample.timestamp, datetime)

    def test_experiment_sample_metadata_nullable(self, test_db):
        """Metadata can be omitted."""
        sample = ExperimentSample(
            prompt="Q",
            answer="A",
            skill_label="skill",
            target_label="target",
            subject_label="Science/Math",
            format_label="QA",
            dataset_name="ds",
            correctness=0.5,
        )
        test_db.add(sample)
        test_db.commit()
        test_db.refresh(sample)

        assert sample.meta_data is None
        assert sample.correctness == 0.5
