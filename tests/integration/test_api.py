"""Integration tests for API endpoints."""

import pytest
import json
from unittest.mock import patch, Mock

from apps.core.models import LeaderboardCache, EvaluationTask


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test successful health check."""
        with patch('apps.backend.routers.status.get_db') as mock_db, \
             patch('apps.backend.routers.status.redis_client') as mock_redis:
            
            # Mock database connection
            mock_db.return_value.__enter__.return_value.execute.return_value = None
            
            # Mock Redis connection
            mock_redis.ping.return_value = True
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database_status"] == "connected"
            assert data["redis_status"] == "connected"
    
    def test_health_check_database_failure(self, client):
        """Test health check with database failure."""
        with patch('apps.backend.routers.status.get_db') as mock_db, \
             patch('apps.backend.routers.status.redis_client') as mock_redis:
            
            # Mock database failure
            mock_db.return_value.__enter__.return_value.execute.side_effect = Exception("DB Error")
            
            # Mock Redis success
            mock_redis.ping.return_value = True
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database_status"] == "disconnected"
            assert data["redis_status"] == "connected"
    
    def test_health_check_redis_failure(self, client):
        """Test health check with Redis failure."""
        with patch('apps.backend.routers.status.get_db') as mock_db, \
             patch('apps.backend.routers.status.redis_client') as mock_redis:
            
            # Mock database success
            mock_db.return_value.__enter__.return_value.execute.return_value = None
            
            # Mock Redis failure
            mock_redis.ping.side_effect = Exception("Redis Error")
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database_status"] == "connected"
            assert data["redis_status"] == "disconnected"


class TestLeaderboardEndpoints:
    """Test leaderboard endpoints."""
    
    def test_generate_leaderboard_success(self, client, sample_evaluation_request):
        """Test successful leaderboard generation."""
        with patch('apps.backend.services.orchestrator.EvaluationOrchestrator.create_evaluation_task') as mock_create:
            mock_create.return_value = {
                "task_id": "test-task-id",
                "status": "PENDING",
                "message": "Task created successfully"
            }
            
            response = client.post(
                "/api/v1/leaderboard/generate",
                json=sample_evaluation_request
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id"
            assert data["status"] == "PENDING"
            mock_create.assert_called_once()
    
    def test_generate_leaderboard_validation_error(self, client):
        """Test leaderboard generation with validation error."""
        invalid_request = {
            "query": "",  # Empty query
            "models": []  # Empty models
        }
        
        response = client.post(
            "/api/v1/leaderboard/generate",
            json=invalid_request
        )
        
        assert response.status_code == 422
    
    def test_generate_leaderboard_service_error(self, client, sample_evaluation_request):
        """Test leaderboard generation with service error."""
        with patch('apps.backend.services.orchestrator.EvaluationOrchestrator.create_evaluation_task') as mock_create:
            mock_create.side_effect = Exception("Service error")
            
            response = client.post(
                "/api/v1/leaderboard/generate",
                json=sample_evaluation_request
            )
            
            assert response.status_code == 500
    
    def test_browse_leaderboard_success(self, client, test_db, leaderboard_entries):
        """Test successful leaderboard browsing."""
        # Add test data to database
        for entry in leaderboard_entries:
            cache = LeaderboardCache(
                model_name=entry["model_name"],
                score=entry["score"],
                accuracy=entry["accuracy"],
                language=entry["language"],
                subject_type=entry["subject_type"],
                task_type=entry["task_type"],
                sample_count=entry["sample_count"],
                metadata=entry["metadata"]
            )
            test_db.add(cache)
        test_db.commit()
        
        response = client.get("/api/v1/leaderboard/browse")
        
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert len(data["entries"]) == 2
        assert data["total"] == 2
    
    def test_browse_leaderboard_with_filters(self, client, test_db, leaderboard_entries):
        """Test leaderboard browsing with filters."""
        # Add test data
        for entry in leaderboard_entries:
            cache = LeaderboardCache(
                model_name=entry["model_name"],
                score=entry["score"],
                accuracy=entry["accuracy"],
                language=entry["language"],
                subject_type=entry["subject_type"],
                task_type=entry["task_type"],
                sample_count=entry["sample_count"],
                metadata=entry["metadata"]
            )
            test_db.add(cache)
        test_db.commit()
        
        response = client.get(
            "/api/v1/leaderboard/browse?language=English&subject_type=Math&limit=1"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 1
        assert data["entries"][0]["language"] == "English"
        assert data["entries"][0]["subject_type"] == "Math"
    
    def test_browse_leaderboard_empty_result(self, client):
        """Test leaderboard browsing with no results."""
        response = client.get("/api/v1/leaderboard/browse")
        
        assert response.status_code == 200
        data = response.json()
        assert data["entries"] == []
        assert data["total"] == 0


class TestTaskEndpoints:
    """Test task management endpoints."""
    
    def test_get_task_status_success(self, client, test_db):
        """Test successful task status retrieval."""
        # Create test task
        task = EvaluationTask(
            task_id="test-task-id",
            query="Test query",
            status="SUCCESS",
            progress=100,
            result={"model_results": [{"model": "test", "score": 0.85}]}
        )
        test_db.add(task)
        test_db.commit()
        
        response = client.get("/api/v1/tasks/test-task-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "SUCCESS"
        assert data["progress"] == 100
        assert "result" in data
    
    def test_get_task_status_not_found(self, client):
        """Test task status retrieval for non-existent task."""
        response = client.get("/api/v1/tasks/non-existent-task")
        
        assert response.status_code == 404
    
    def test_cancel_task_success(self, client, test_db):
        """Test successful task cancellation."""
        # Create test task
        task = EvaluationTask(
            task_id="test-task-id",
            query="Test query",
            status="PENDING"
        )
        test_db.add(task)
        test_db.commit()
        
        with patch('apps.backend.services.orchestrator.celery_app') as mock_celery:
            response = client.delete("/api/v1/tasks/test-task-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Task cancelled successfully"
        assert data["task_id"] == "test-task-id"
    
    def test_cancel_task_not_found(self, client):
        """Test cancelling non-existent task."""
        response = client.delete("/api/v1/tasks/non-existent-task")
        
        assert response.status_code == 404
    
    def test_cancel_task_already_completed(self, client, test_db):
        """Test cancelling already completed task."""
        # Create completed task
        task = EvaluationTask(
            task_id="test-task-id",
            query="Test query",
            status="SUCCESS"
        )
        test_db.add(task)
        test_db.commit()
        
        response = client.delete("/api/v1/tasks/test-task-id")
        
        assert response.status_code == 409
    
    def test_list_tasks_success(self, client, test_db):
        """Test successful task listing."""
        # Create test tasks
        tasks = [
            EvaluationTask(task_id="task-1", query="Query 1", status="SUCCESS"),
            EvaluationTask(task_id="task-2", query="Query 2", status="PENDING")
        ]
        
        for task in tasks:
            test_db.add(task)
        test_db.commit()
        
        response = client.get("/api/v1/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["total"] == 2
    
    def test_list_tasks_with_filters(self, client, test_db):
        """Test task listing with filters."""
        # Create test tasks
        tasks = [
            EvaluationTask(task_id="task-1", query="Query 1", status="SUCCESS"),
            EvaluationTask(task_id="task-2", query="Query 2", status="PENDING"),
            EvaluationTask(task_id="task-3", query="Query 3", status="SUCCESS")
        ]
        
        for task in tasks:
            test_db.add(task)
        test_db.commit()
        
        response = client.get("/api/v1/tasks?status=SUCCESS&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        for task in data["tasks"]:
            assert task["status"] == "SUCCESS"


class TestStatsEndpoint:
    """Test statistics endpoint."""
    
    def test_get_stats_success(self, client, test_db):
        """Test successful statistics retrieval."""
        # Create test data
        tasks = [
            EvaluationTask(task_id="task-1", query="Query 1", status="SUCCESS"),
            EvaluationTask(task_id="task-2", query="Query 2", status="PENDING"),
            EvaluationTask(task_id="task-3", query="Query 3", status="FAILURE")
        ]
        
        for task in tasks:
            test_db.add(task)
        
        cache_entries = [
            LeaderboardCache(model_name="model-1", score=0.8, language="English", subject_type="Math", task_type="QA"),
            LeaderboardCache(model_name="model-2", score=0.9, language="English", subject_type="Math", task_type="QA")
        ]
        
        for entry in cache_entries:
            test_db.add(entry)
        
        test_db.commit()
        
        with patch('apps.backend.routers.status.redis_client') as mock_redis:
            mock_redis.ping.return_value = True
            
            response = client.get("/api/v1/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert data["tasks"]["SUCCESS"] == 1
        assert data["tasks"]["PENDING"] == 1
        assert data["tasks"]["FAILURE"] == 1
        assert data["cache_entries"] == 2
    
    def test_get_stats_empty_database(self, client):
        """Test statistics with empty database."""
        with patch('apps.backend.routers.status.redis_client') as mock_redis:
            mock_redis.ping.return_value = True
            
            response = client.get("/api/v1/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"]["SUCCESS"] == 0
        assert data["tasks"]["PENDING"] == 0
        assert data["cache_entries"] == 0


class TestPlannerEndpoint:
    """Test planner endpoint."""
    
    def test_generate_plan_success(self, client):
        """Test successful plan generation."""
        request_data = {
            "query": "Compare models on math problems",
            "context": {
                "models": ["gpt-4", "claude-3"],
                "preferred_metrics": ["accuracy"]
            }
        }
        
        with patch('apps.planner.agent.PlannerAgent.generate_plan') as mock_generate:
            mock_generate.return_value = {
                "plan": {
                    "version": "1.0",
                    "metadata": {"name": "Generated Plan"}
                },
                "confidence": 0.9
            }
            
            response = client.post("/api/v1/planner/generate-plan", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert "confidence" in data
        assert data["confidence"] == 0.9
    
    def test_generate_plan_validation_error(self, client):
        """Test plan generation with validation error."""
        invalid_request = {
            "query": ""  # Empty query
        }
        
        response = client.post("/api/v1/planner/generate-plan", json=invalid_request)
        
        assert response.status_code == 422
    
    def test_generate_plan_service_error(self, client):
        """Test plan generation with service error."""
        request_data = {
            "query": "Test query",
            "context": {}
        }
        
        with patch('apps.planner.agent.PlannerAgent.generate_plan') as mock_generate:
            mock_generate.side_effect = Exception("Planner error")
            
            response = client.post("/api/v1/planner/generate-plan", json=request_data)
        
        assert response.status_code == 500