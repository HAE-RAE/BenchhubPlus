"""Unit tests for service layer."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from apps.backend.services.leaderboard_service import LeaderboardService
from apps.backend.services.orchestrator import EvaluationOrchestrator
from apps.core.schemas import EvaluationRequest, ModelConfig
from apps.core.models import LeaderboardCache, EvaluationTask


class TestLeaderboardService:
    """Test LeaderboardService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock leaderboard repository."""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_repository):
        """LeaderboardService instance."""
        return LeaderboardService(mock_repository)
    
    def test_browse_leaderboard_no_filters(self, service, mock_repository, leaderboard_entries):
        """Test browsing leaderboard without filters."""
        mock_repository.get_entries.return_value = (leaderboard_entries, 2)
        
        result = service.browse_leaderboard({})
        
        assert result["entries"] == leaderboard_entries
        assert result["total"] == 2
        assert result["page"] == 1
        assert result["pages"] == 1
        mock_repository.get_entries.assert_called_once_with({})
    
    def test_browse_leaderboard_with_filters(self, service, mock_repository, leaderboard_entries):
        """Test browsing leaderboard with filters."""
        filters = {
            "language": "English",
            "subject_type": "Math",
            "limit": 10,
            "offset": 0
        }
        
        mock_repository.get_entries.return_value = (leaderboard_entries, 2)
        
        result = service.browse_leaderboard(filters)
        
        assert result["entries"] == leaderboard_entries
        assert result["total"] == 2
        mock_repository.get_entries.assert_called_once_with(filters)
    
    def test_browse_leaderboard_pagination(self, service, mock_repository, leaderboard_entries):
        """Test leaderboard pagination."""
        filters = {"limit": 1, "offset": 0}
        mock_repository.get_entries.return_value = (leaderboard_entries[:1], 2)
        
        result = service.browse_leaderboard(filters)
        
        assert len(result["entries"]) == 1
        assert result["total"] == 2
        assert result["page"] == 1
        assert result["pages"] == 2
        assert result["has_next"] is True
        assert result["has_prev"] is False
    
    def test_browse_leaderboard_empty_result(self, service, mock_repository):
        """Test browsing leaderboard with no results."""
        mock_repository.get_entries.return_value = ([], 0)
        
        result = service.browse_leaderboard({})
        
        assert result["entries"] == []
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["pages"] == 0
        assert result["has_next"] is False
        assert result["has_prev"] is False


class TestEvaluationOrchestrator:
    """Test EvaluationOrchestrator."""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Mock task repository."""
        return Mock()
    
    @pytest.fixture
    def mock_planner_agent(self):
        """Mock planner agent."""
        mock_agent = Mock()
        mock_agent.generate_plan.return_value = {
            "plan": {
                "version": "1.0",
                "metadata": {"name": "Test Plan"},
                "evaluation": {"metrics": ["accuracy"]}
            },
            "confidence": 0.9
        }
        return mock_agent
    
    @pytest.fixture
    def orchestrator(self, mock_task_repository, mock_planner_agent):
        """EvaluationOrchestrator instance."""
        return EvaluationOrchestrator(mock_task_repository, mock_planner_agent)
    
    @pytest.mark.asyncio
    async def test_create_evaluation_task(self, orchestrator, mock_task_repository, sample_evaluation_request):
        """Test creating evaluation task."""
        # Mock task creation
        mock_task = Mock()
        mock_task.task_id = "test-task-id"
        mock_task.status = "PENDING"
        mock_task_repository.create_task.return_value = mock_task
        
        # Mock Celery task
        with patch('apps.backend.services.orchestrator.run_evaluation_task') as mock_celery:
            mock_celery.delay.return_value = Mock(id="celery-task-id")
            
            result = await orchestrator.create_evaluation_task(sample_evaluation_request)
        
        assert result["task_id"] == "test-task-id"
        assert result["status"] == "PENDING"
        mock_task_repository.create_task.assert_called_once()
        mock_celery.delay.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_evaluation_task_planner_failure(self, orchestrator, mock_planner_agent, sample_evaluation_request):
        """Test handling planner failure."""
        mock_planner_agent.generate_plan.side_effect = Exception("Planner failed")
        
        with pytest.raises(Exception, match="Planner failed"):
            await orchestrator.create_evaluation_task(sample_evaluation_request)
    
    def test_get_task_status_existing(self, orchestrator, mock_task_repository):
        """Test getting status of existing task."""
        mock_task = Mock()
        mock_task.task_id = "test-task-id"
        mock_task.status = "SUCCESS"
        mock_task.progress = 100
        mock_task.result = {"model_results": []}
        mock_task.created_at = datetime.utcnow()
        mock_task.completed_at = datetime.utcnow()
        mock_task.error_message = None
        
        mock_task_repository.get_task.return_value = mock_task
        
        result = orchestrator.get_task_status("test-task-id")
        
        assert result["task_id"] == "test-task-id"
        assert result["status"] == "SUCCESS"
        assert result["progress"] == 100
        assert "result" in result
        mock_task_repository.get_task.assert_called_once_with("test-task-id")
    
    def test_get_task_status_not_found(self, orchestrator, mock_task_repository):
        """Test getting status of non-existent task."""
        mock_task_repository.get_task.return_value = None
        
        result = orchestrator.get_task_status("non-existent-task")
        
        assert result is None
        mock_task_repository.get_task.assert_called_once_with("non-existent-task")
    
    def test_cancel_task_success(self, orchestrator, mock_task_repository):
        """Test successful task cancellation."""
        mock_task = Mock()
        mock_task.task_id = "test-task-id"
        mock_task.status = "PENDING"
        
        mock_task_repository.get_task.return_value = mock_task
        mock_task_repository.update_task.return_value = mock_task
        
        with patch('apps.backend.services.orchestrator.celery_app') as mock_celery:
            result = orchestrator.cancel_task("test-task-id")
        
        assert result["message"] == "Task cancelled successfully"
        assert result["task_id"] == "test-task-id"
        mock_celery.control.revoke.assert_called_once()
    
    def test_cancel_task_not_found(self, orchestrator, mock_task_repository):
        """Test cancelling non-existent task."""
        mock_task_repository.get_task.return_value = None
        
        result = orchestrator.cancel_task("non-existent-task")
        
        assert result is None
    
    def test_cancel_task_already_completed(self, orchestrator, mock_task_repository):
        """Test cancelling already completed task."""
        mock_task = Mock()
        mock_task.task_id = "test-task-id"
        mock_task.status = "SUCCESS"
        
        mock_task_repository.get_task.return_value = mock_task
        
        with pytest.raises(ValueError, match="cannot be cancelled"):
            orchestrator.cancel_task("test-task-id")
    
    def test_list_tasks(self, orchestrator, mock_task_repository):
        """Test listing tasks."""
        mock_tasks = [
            Mock(task_id="task-1", status="SUCCESS", created_at=datetime.utcnow()),
            Mock(task_id="task-2", status="PENDING", created_at=datetime.utcnow())
        ]
        
        mock_task_repository.list_tasks.return_value = (mock_tasks, 2)
        
        filters = {"status": "SUCCESS", "limit": 10}
        result = orchestrator.list_tasks(filters)
        
        assert len(result["tasks"]) == 2
        assert result["total"] == 2
        mock_task_repository.list_tasks.assert_called_once_with(filters)


class TestPlannerAgent:
    """Test PlannerAgent."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "plan": {
                "version": "1.0",
                "metadata": {
                    "name": "Generated Plan",
                    "language": "English",
                    "subject_type": "Math"
                }
            },
            "confidence": 0.9
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.mark.asyncio
    async def test_generate_plan_success(self, mock_openai_client):
        """Test successful plan generation."""
        from apps.planner.agent import PlannerAgent
        
        agent = PlannerAgent()
        agent.client = mock_openai_client
        
        query = "Compare models on math problems"
        result = await agent.generate_plan(query)
        
        assert "plan" in result
        assert "confidence" in result
        assert result["plan"]["version"] == "1.0"
        mock_openai_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_plan_api_failure(self, mock_openai_client):
        """Test plan generation with API failure."""
        from apps.planner.agent import PlannerAgent
        
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        agent = PlannerAgent()
        agent.client = mock_openai_client
        
        with pytest.raises(Exception, match="API Error"):
            await agent.generate_plan("Test query")
    
    @pytest.mark.asyncio
    async def test_generate_plan_invalid_response(self, mock_openai_client):
        """Test plan generation with invalid response."""
        from apps.planner.agent import PlannerAgent
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        agent = PlannerAgent()
        agent.client = mock_openai_client
        
        with pytest.raises(Exception):
            await agent.generate_plan("Test query")


class TestEvaluationEngine:
    """Test EvaluationEngine."""
    
    @pytest.fixture
    def evaluation_engine(self):
        """EvaluationEngine instance."""
        from apps.worker.evaluation_engine import EvaluationEngine
        return EvaluationEngine()
    
    def test_calculate_accuracy(self, evaluation_engine):
        """Test accuracy calculation."""
        results = [
            {"expected": "A", "actual": "A"},
            {"expected": "B", "actual": "B"},
            {"expected": "C", "actual": "D"},
            {"expected": "D", "actual": "D"}
        ]
        
        accuracy = evaluation_engine.calculate_accuracy(results)
        assert accuracy == 0.75  # 3/4 correct
    
    def test_calculate_accuracy_empty(self, evaluation_engine):
        """Test accuracy calculation with empty results."""
        accuracy = evaluation_engine.calculate_accuracy([])
        assert accuracy == 0.0
    
    def test_calculate_f1_score(self, evaluation_engine):
        """Test F1 score calculation."""
        # Mock binary classification results
        results = [
            {"expected": 1, "actual": 1},  # TP
            {"expected": 1, "actual": 0},  # FN
            {"expected": 0, "actual": 1},  # FP
            {"expected": 0, "actual": 0}   # TN
        ]
        
        f1 = evaluation_engine.calculate_f1_score(results)
        # F1 = 2 * (precision * recall) / (precision + recall)
        # Precision = TP / (TP + FP) = 1 / (1 + 1) = 0.5
        # Recall = TP / (TP + FN) = 1 / (1 + 1) = 0.5
        # F1 = 2 * (0.5 * 0.5) / (0.5 + 0.5) = 0.5
        assert f1 == 0.5
    
    def test_aggregate_model_results(self, evaluation_engine):
        """Test model results aggregation."""
        model_results = {
            "model1": [
                {"score": 0.8, "accuracy": 0.9},
                {"score": 0.9, "accuracy": 0.8}
            ],
            "model2": [
                {"score": 0.7, "accuracy": 0.7},
                {"score": 0.8, "accuracy": 0.8}
            ]
        }
        
        aggregated = evaluation_engine.aggregate_model_results(model_results)
        
        assert "model1" in aggregated
        assert "model2" in aggregated
        assert aggregated["model1"]["average_score"] == 0.85
        assert aggregated["model1"]["average_accuracy"] == 0.85
        assert aggregated["model2"]["average_score"] == 0.75
        assert aggregated["model2"]["average_accuracy"] == 0.75
    
    def test_calculate_statistical_significance(self, evaluation_engine):
        """Test statistical significance calculation."""
        scores1 = [0.8, 0.9, 0.7, 0.85, 0.95]
        scores2 = [0.6, 0.7, 0.5, 0.65, 0.75]
        
        p_value = evaluation_engine.calculate_statistical_significance(scores1, scores2)
        
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1
        # With these clearly different scores, p-value should be small
        assert p_value < 0.05