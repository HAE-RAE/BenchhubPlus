"""Unit tests for database models."""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from apps.core.models import LeaderboardCache, EvaluationTask, ExperimentSample


class TestLeaderboardCache:
    """Test LeaderboardCache model."""
    
    def test_create_leaderboard_cache(self, test_db):
        """Test creating a leaderboard cache entry."""
        cache = LeaderboardCache(
            model_name="test-model",
            score=0.85,
            accuracy=0.80,
            language="English",
            subject_type="Math",
            task_type="QA",
            sample_count=100,
            metadata={"difficulty": "High School"}
        )
        
        test_db.add(cache)
        test_db.commit()
        test_db.refresh(cache)
        
        assert cache.id is not None
        assert cache.model_name == "test-model"
        assert cache.score == 0.85
        assert cache.accuracy == 0.80
        assert cache.language == "English"
        assert cache.subject_type == "Math"
        assert cache.task_type == "QA"
        assert cache.sample_count == 100
        assert cache.metadata == {"difficulty": "High School"}
        assert cache.last_updated is not None
    
    def test_leaderboard_cache_required_fields(self, test_db):
        """Test that required fields are enforced."""
        # Missing model_name should raise error
        with pytest.raises(IntegrityError):
            cache = LeaderboardCache(
                score=0.85,
                language="English",
                subject_type="Math",
                task_type="QA"
            )
            test_db.add(cache)
            test_db.commit()
    
    def test_leaderboard_cache_defaults(self, test_db):
        """Test default values."""
        cache = LeaderboardCache(
            model_name="test-model",
            score=0.85,
            language="English",
            subject_type="Math",
            task_type="QA"
        )
        
        test_db.add(cache)
        test_db.commit()
        test_db.refresh(cache)
        
        assert cache.accuracy is None
        assert cache.sample_count is None
        assert cache.metadata == {}
        assert isinstance(cache.last_updated, datetime)
    
    def test_leaderboard_cache_string_representation(self, test_db):
        """Test string representation."""
        cache = LeaderboardCache(
            model_name="test-model",
            score=0.85,
            language="English",
            subject_type="Math",
            task_type="QA"
        )
        
        test_db.add(cache)
        test_db.commit()
        
        str_repr = str(cache)
        assert "test-model" in str_repr
        assert "0.85" in str_repr


class TestEvaluationTask:
    """Test EvaluationTask model."""
    
    def test_create_evaluation_task(self, test_db):
        """Test creating an evaluation task."""
        task = EvaluationTask(
            task_id="test-task-id",
            query="Test query",
            status="PENDING",
            models_config=[{"name": "test-model", "api_key": "test-key"}],
            plan_config={"version": "1.0"},
            progress=0
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        assert task.id is not None
        assert task.task_id == "test-task-id"
        assert task.query == "Test query"
        assert task.status == "PENDING"
        assert task.models_config == [{"name": "test-model", "api_key": "test-key"}]
        assert task.plan_config == {"version": "1.0"}
        assert task.progress == 0
        assert task.created_at is not None
    
    def test_evaluation_task_status_update(self, test_db):
        """Test updating task status."""
        task = EvaluationTask(
            task_id="test-task-id",
            query="Test query",
            status="PENDING"
        )
        
        test_db.add(task)
        test_db.commit()
        
        # Update status
        task.status = "STARTED"
        task.started_at = datetime.utcnow()
        task.progress = 50
        
        test_db.commit()
        test_db.refresh(task)
        
        assert task.status == "STARTED"
        assert task.started_at is not None
        assert task.progress == 50
    
    def test_evaluation_task_completion(self, test_db):
        """Test task completion."""
        task = EvaluationTask(
            task_id="test-task-id",
            query="Test query",
            status="STARTED"
        )
        
        test_db.add(task)
        test_db.commit()
        
        # Complete task
        task.status = "SUCCESS"
        task.completed_at = datetime.utcnow()
        task.progress = 100
        task.result = {"model_results": [{"model": "test", "score": 0.85}]}
        
        test_db.commit()
        test_db.refresh(task)
        
        assert task.status == "SUCCESS"
        assert task.completed_at is not None
        assert task.progress == 100
        assert task.result is not None
    
    def test_evaluation_task_failure(self, test_db):
        """Test task failure."""
        task = EvaluationTask(
            task_id="test-task-id",
            query="Test query",
            status="STARTED"
        )
        
        test_db.add(task)
        test_db.commit()
        
        # Fail task
        task.status = "FAILURE"
        task.completed_at = datetime.utcnow()
        task.error_message = "Test error"
        
        test_db.commit()
        test_db.refresh(task)
        
        assert task.status == "FAILURE"
        assert task.completed_at is not None
        assert task.error_message == "Test error"


class TestExperimentSample:
    """Test ExperimentSample model."""
    
    def test_create_experiment_sample(self, test_db):
        """Test creating an experiment sample."""
        # First create a task
        task = EvaluationTask(
            task_id="test-task-id",
            query="Test query",
            status="PENDING"
        )
        test_db.add(task)
        test_db.commit()
        
        # Create sample
        sample = ExperimentSample(
            task_id=task.task_id,
            sample_id="sample-1",
            input_data={"question": "What is 2+2?"},
            expected_output="4",
            model_outputs={"test-model": "4"},
            scores={"test-model": 1.0},
            metadata={"category": "math"}
        )
        
        test_db.add(sample)
        test_db.commit()
        test_db.refresh(sample)
        
        assert sample.id is not None
        assert sample.task_id == task.task_id
        assert sample.sample_id == "sample-1"
        assert sample.input_data == {"question": "What is 2+2?"}
        assert sample.expected_output == "4"
        assert sample.model_outputs == {"test-model": "4"}
        assert sample.scores == {"test-model": 1.0}
        assert sample.metadata == {"category": "math"}
        assert sample.created_at is not None
    
    def test_experiment_sample_relationship(self, test_db):
        """Test relationship with evaluation task."""
        # Create task
        task = EvaluationTask(
            task_id="test-task-id",
            query="Test query",
            status="PENDING"
        )
        test_db.add(task)
        test_db.commit()
        
        # Create samples
        sample1 = ExperimentSample(
            task_id=task.task_id,
            sample_id="sample-1",
            input_data={"question": "Q1"},
            expected_output="A1"
        )
        
        sample2 = ExperimentSample(
            task_id=task.task_id,
            sample_id="sample-2",
            input_data={"question": "Q2"},
            expected_output="A2"
        )
        
        test_db.add_all([sample1, sample2])
        test_db.commit()
        
        # Test relationship
        task_samples = test_db.query(ExperimentSample).filter(
            ExperimentSample.task_id == task.task_id
        ).all()
        
        assert len(task_samples) == 2
        assert task_samples[0].task_id == task.task_id
        assert task_samples[1].task_id == task.task_id
    
    def test_experiment_sample_json_fields(self, test_db):
        """Test JSON field handling."""
        task = EvaluationTask(
            task_id="test-task-id",
            query="Test query",
            status="PENDING"
        )
        test_db.add(task)
        test_db.commit()
        
        # Test complex JSON data
        complex_input = {
            "question": "Complex question",
            "context": ["Context 1", "Context 2"],
            "options": {"A": "Option A", "B": "Option B"}
        }
        
        complex_outputs = {
            "model1": {"answer": "A", "confidence": 0.9},
            "model2": {"answer": "B", "confidence": 0.7}
        }
        
        sample = ExperimentSample(
            task_id=task.task_id,
            sample_id="complex-sample",
            input_data=complex_input,
            model_outputs=complex_outputs
        )
        
        test_db.add(sample)
        test_db.commit()
        test_db.refresh(sample)
        
        assert sample.input_data == complex_input
        assert sample.model_outputs == complex_outputs