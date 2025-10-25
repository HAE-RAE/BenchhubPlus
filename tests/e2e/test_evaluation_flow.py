"""End-to-end tests for evaluation flow."""

import pytest
import time
import json
from unittest.mock import patch, Mock

from apps.core.models import EvaluationTask, LeaderboardCache


class TestEvaluationFlow:
    """Test complete evaluation flow."""
    
    @pytest.mark.asyncio
    async def test_complete_evaluation_flow(self, client, test_db, sample_evaluation_request):
        """Test complete evaluation flow from request to results."""
        
        # Mock external dependencies
        with patch('apps.planner.agent.PlannerAgent.generate_plan') as mock_planner, \
             patch('apps.worker.tasks.evaluation_tasks.run_evaluation_task.delay') as mock_celery, \
             patch('apps.worker.hret_runner.HRETRunner.run_evaluation') as mock_hret:
            
            # Setup mocks
            mock_planner.return_value = {
                "plan": {
                    "version": "1.0",
                    "metadata": {
                        "name": "Test Evaluation",
                        "language": "English",
                        "subject_type": "Math",
                        "task_type": "QA",
                        "sample_size": 10
                    },
                    "evaluation": {
                        "metrics": ["accuracy"],
                        "timeout": 30
                    }
                },
                "confidence": 0.9
            }
            
            mock_task = Mock()
            mock_task.id = "celery-task-id"
            mock_celery.return_value = mock_task
            
            mock_hret.return_value = {
                "model_results": [
                    {
                        "model_name": "test-model",
                        "average_score": 0.85,
                        "accuracy": 0.80,
                        "total_samples": 10,
                        "execution_time": 30.5
                    }
                ],
                "evaluation_metadata": {
                    "total_duration": 35.0,
                    "samples_processed": 10
                }
            }
            
            # Step 1: Submit evaluation request
            response = client.post(
                "/api/v1/leaderboard/generate",
                json=sample_evaluation_request
            )
            
            assert response.status_code == 200
            data = response.json()
            task_id = data["task_id"]
            assert data["status"] == "PENDING"
            
            # Verify task was created in database
            task = test_db.query(EvaluationTask).filter(
                EvaluationTask.task_id == task_id
            ).first()
            assert task is not None
            assert task.status == "PENDING"
            
            # Step 2: Simulate task processing
            # Update task status to STARTED
            task.status = "STARTED"
            task.progress = 50
            test_db.commit()
            
            # Check task status
            response = client.get(f"/api/v1/tasks/{task_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "STARTED"
            assert data["progress"] == 50
            
            # Step 3: Complete task
            task.status = "SUCCESS"
            task.progress = 100
            task.result = {
                "model_results": [
                    {
                        "model_name": "test-model",
                        "average_score": 0.85,
                        "accuracy": 0.80,
                        "total_samples": 10
                    }
                ]
            }
            test_db.commit()
            
            # Check final status
            response = client.get(f"/api/v1/tasks/{task_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "SUCCESS"
            assert data["progress"] == 100
            assert "result" in data
            assert len(data["result"]["model_results"]) == 1
            
            # Step 4: Verify results are cached in leaderboard
            # Simulate cache update
            cache_entry = LeaderboardCache(
                model_name="test-model",
                score=0.85,
                accuracy=0.80,
                language="English",
                subject_type="Math",
                task_type="QA",
                sample_count=10
            )
            test_db.add(cache_entry)
            test_db.commit()
            
            # Browse leaderboard to verify results
            response = client.get("/api/v1/leaderboard/browse")
            assert response.status_code == 200
            data = response.json()
            assert len(data["entries"]) == 1
            assert data["entries"][0]["model_name"] == "test-model"
            assert data["entries"][0]["score"] == 0.85
    
    def test_evaluation_flow_with_multiple_models(self, client, test_db):
        """Test evaluation flow with multiple models."""
        
        multi_model_request = {
            "query": "Compare multiple models on math problems",
            "models": [
                {
                    "name": "model-1",
                    "api_base": "https://api.test1.com/v1",
                    "api_key": "key-1",
                    "model_type": "openai"
                },
                {
                    "name": "model-2",
                    "api_base": "https://api.test2.com/v1",
                    "api_key": "key-2",
                    "model_type": "anthropic"
                }
            ]
        }
        
        with patch('apps.planner.agent.PlannerAgent.generate_plan') as mock_planner, \
             patch('apps.worker.tasks.evaluation_tasks.run_evaluation_task.delay') as mock_celery:
            
            mock_planner.return_value = {
                "plan": {"version": "1.0", "metadata": {"name": "Multi-model Test"}},
                "confidence": 0.9
            }
            
            mock_celery.return_value = Mock(id="celery-task-id")
            
            response = client.post(
                "/api/v1/leaderboard/generate",
                json=multi_model_request
            )
            
            assert response.status_code == 200
            data = response.json()
            task_id = data["task_id"]
            
            # Verify task contains multiple models
            task = test_db.query(EvaluationTask).filter(
                EvaluationTask.task_id == task_id
            ).first()
            
            assert len(task.models_config) == 2
            assert task.models_config[0]["name"] == "model-1"
            assert task.models_config[1]["name"] == "model-2"
    
    def test_evaluation_flow_task_failure(self, client, test_db, sample_evaluation_request):
        """Test evaluation flow with task failure."""
        
        with patch('apps.planner.agent.PlannerAgent.generate_plan') as mock_planner, \
             patch('apps.worker.tasks.evaluation_tasks.run_evaluation_task.delay') as mock_celery:
            
            mock_planner.return_value = {
                "plan": {"version": "1.0", "metadata": {"name": "Test"}},
                "confidence": 0.9
            }
            
            mock_celery.return_value = Mock(id="celery-task-id")
            
            # Submit request
            response = client.post(
                "/api/v1/leaderboard/generate",
                json=sample_evaluation_request
            )
            
            task_id = response.json()["task_id"]
            
            # Simulate task failure
            task = test_db.query(EvaluationTask).filter(
                EvaluationTask.task_id == task_id
            ).first()
            
            task.status = "FAILURE"
            task.error_message = "Model API call failed"
            test_db.commit()
            
            # Check failure status
            response = client.get(f"/api/v1/tasks/{task_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "FAILURE"
            assert data["error_message"] == "Model API call failed"
    
    def test_evaluation_flow_task_cancellation(self, client, test_db, sample_evaluation_request):
        """Test evaluation flow with task cancellation."""
        
        with patch('apps.planner.agent.PlannerAgent.generate_plan') as mock_planner, \
             patch('apps.worker.tasks.evaluation_tasks.run_evaluation_task.delay') as mock_celery, \
             patch('apps.backend.services.orchestrator.celery_app') as mock_celery_app:
            
            mock_planner.return_value = {
                "plan": {"version": "1.0", "metadata": {"name": "Test"}},
                "confidence": 0.9
            }
            
            mock_celery.return_value = Mock(id="celery-task-id")
            
            # Submit request
            response = client.post(
                "/api/v1/leaderboard/generate",
                json=sample_evaluation_request
            )
            
            task_id = response.json()["task_id"]
            
            # Cancel task
            response = client.delete(f"/api/v1/tasks/{task_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["message"] == "Task cancelled successfully"
            assert data["task_id"] == task_id
            
            # Verify task status updated
            task = test_db.query(EvaluationTask).filter(
                EvaluationTask.task_id == task_id
            ).first()
            assert task.status == "CANCELLED"
    
    def test_evaluation_flow_planner_failure(self, client, sample_evaluation_request):
        """Test evaluation flow with planner failure."""
        
        with patch('apps.planner.agent.PlannerAgent.generate_plan') as mock_planner:
            mock_planner.side_effect = Exception("Planner service unavailable")
            
            response = client.post(
                "/api/v1/leaderboard/generate",
                json=sample_evaluation_request
            )
            
            assert response.status_code == 500
    
    def test_evaluation_flow_invalid_request(self, client):
        """Test evaluation flow with invalid request."""
        
        invalid_request = {
            "query": "",  # Empty query
            "models": []  # No models
        }
        
        response = client.post(
            "/api/v1/leaderboard/generate",
            json=invalid_request
        )
        
        assert response.status_code == 422
    
    def test_leaderboard_browsing_after_evaluations(self, client, test_db):
        """Test leaderboard browsing after multiple evaluations."""
        
        # Create multiple cache entries
        cache_entries = [
            LeaderboardCache(
                model_name="gpt-4",
                score=0.95,
                accuracy=0.92,
                language="English",
                subject_type="Math",
                task_type="QA",
                sample_count=100
            ),
            LeaderboardCache(
                model_name="claude-3",
                score=0.88,
                accuracy=0.85,
                language="English",
                subject_type="Math",
                task_type="QA",
                sample_count=100
            ),
            LeaderboardCache(
                model_name="gpt-3.5",
                score=0.82,
                accuracy=0.78,
                language="English",
                subject_type="Science",
                task_type="QA",
                sample_count=50
            )
        ]
        
        for entry in cache_entries:
            test_db.add(entry)
        test_db.commit()
        
        # Test browsing all entries
        response = client.get("/api/v1/leaderboard/browse")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 3
        
        # Test filtering by subject
        response = client.get("/api/v1/leaderboard/browse?subject_type=Math")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 2
        
        # Test sorting (should be by score descending by default)
        assert data["entries"][0]["score"] >= data["entries"][1]["score"]
        
        # Test pagination
        response = client.get("/api/v1/leaderboard/browse?limit=1&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 1
        assert data["total"] == 2  # Only Math entries
        assert data["has_next"] is True
    
    def test_system_stats_after_evaluations(self, client, test_db):
        """Test system statistics after running evaluations."""
        
        # Create test tasks with different statuses
        tasks = [
            EvaluationTask(task_id="task-1", query="Query 1", status="SUCCESS"),
            EvaluationTask(task_id="task-2", query="Query 2", status="SUCCESS"),
            EvaluationTask(task_id="task-3", query="Query 3", status="PENDING"),
            EvaluationTask(task_id="task-4", query="Query 4", status="FAILURE")
        ]
        
        for task in tasks:
            test_db.add(task)
        
        # Create cache entries
        cache_entries = [
            LeaderboardCache(model_name="model-1", score=0.8, language="English", subject_type="Math", task_type="QA"),
            LeaderboardCache(model_name="model-2", score=0.9, language="English", subject_type="Math", task_type="QA"),
            LeaderboardCache(model_name="model-3", score=0.7, language="Korean", subject_type="Science", task_type="QA")
        ]
        
        for entry in cache_entries:
            test_db.add(entry)
        
        test_db.commit()
        
        with patch('apps.backend.routers.status.redis_client') as mock_redis:
            mock_redis.ping.return_value = True
            
            response = client.get("/api/v1/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check task statistics
        assert data["tasks"]["SUCCESS"] == 2
        assert data["tasks"]["PENDING"] == 1
        assert data["tasks"]["FAILURE"] == 1
        
        # Check cache statistics
        assert data["cache_entries"] == 3
        
        # Check system health
        assert data["planner_available"] is True