"""Test configuration and fixtures."""

import os
import pytest
import tempfile
from typing import Generator
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.backend.main import app
from apps.core.db import Base, get_db
from apps.core.config import get_settings


@pytest.fixture(scope="session")
def test_settings():
    """Test settings fixture."""
    settings = get_settings()
    settings.DATABASE_URL = "sqlite:///./test.db"
    settings.TESTING = True
    settings.DEBUG = True
    return settings


@pytest.fixture(scope="session")
def test_engine(test_settings):
    """Test database engine."""
    engine = create_engine(
        test_settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Test client with database override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test response"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_celery_task():
    """Mock Celery task."""
    mock_task = Mock()
    mock_task.id = "test-task-id"
    mock_task.status = "PENDING"
    mock_task.result = None
    return mock_task


@pytest.fixture
def sample_model_config():
    """Sample model configuration."""
    return {
        "name": "test-model",
        "api_base": "https://api.test.com/v1",
        "api_key": "test-api-key",
        "model_type": "openai",
        "temperature": 0.7,
        "max_tokens": 1024,
        "timeout": 30
    }


@pytest.fixture
def sample_evaluation_request(sample_model_config):
    """Sample evaluation request."""
    return {
        "query": "Test evaluation query",
        "models": [sample_model_config],
        "criteria": {
            "language": "English",
            "subject_type": "General",
            "task_type": "QA",
            "sample_size": 10
        }
    }


@pytest.fixture
def sample_plan():
    """Sample evaluation plan."""
    return {
        "version": "1.0",
        "metadata": {
            "name": "Test Evaluation",
            "description": "Test evaluation plan",
            "language": "English",
            "subject_type": "General",
            "task_type": "QA",
            "sample_size": 10
        },
        "models": [
            {
                "name": "test-model",
                "api_base": "https://api.test.com/v1",
                "api_key": "test-key",
                "model_type": "openai"
            }
        ],
        "datasets": [
            {
                "name": "test_dataset",
                "type": "qa",
                "source": "local",
                "path": "test_data.json"
            }
        ],
        "evaluation": {
            "metrics": ["accuracy"],
            "timeout": 30,
            "batch_size": 5
        }
    }


@pytest.fixture
def sample_evaluation_samples():
    """Sample evaluation samples."""
    return [
        {
            "id": 1,
            "question": "What is 2 + 2?",
            "answer": "4",
            "category": "math"
        },
        {
            "id": 2,
            "question": "What is the capital of France?",
            "answer": "Paris",
            "category": "geography"
        },
        {
            "id": 3,
            "question": "Who wrote Romeo and Juliet?",
            "answer": "William Shakespeare",
            "category": "literature"
        }
    ]


@pytest.fixture
def temp_file():
    """Temporary file fixture."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_dir():
    """Temporary directory fixture."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    return mock_redis


# Test data fixtures
@pytest.fixture
def leaderboard_entries():
    """Sample leaderboard entries."""
    return [
        {
            "id": "entry-1",
            "model_name": "gpt-4",
            "score": 0.95,
            "accuracy": 0.92,
            "language": "English",
            "subject_type": "Math",
            "task_type": "QA",
            "sample_count": 100,
            "metadata": {"difficulty": "High School"}
        },
        {
            "id": "entry-2",
            "model_name": "claude-3",
            "score": 0.88,
            "accuracy": 0.85,
            "language": "English",
            "subject_type": "Math",
            "task_type": "QA",
            "sample_count": 100,
            "metadata": {"difficulty": "High School"}
        }
    ]


# Async fixtures for testing async functions
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock external services
@pytest.fixture
def mock_hret_runner():
    """Mock HRET runner."""
    mock_runner = Mock()
    mock_runner.run_evaluation.return_value = {
        "results": [
            {
                "model_name": "test-model",
                "score": 0.85,
                "accuracy": 0.80,
                "samples_processed": 10
            }
        ],
        "metadata": {
            "total_time": 30.5,
            "samples_count": 10
        }
    }
    return mock_runner


@pytest.fixture
def mock_planner_agent():
    """Mock planner agent."""
    mock_agent = Mock()
    mock_agent.generate_plan.return_value = {
        "plan": {
            "version": "1.0",
            "metadata": {
                "name": "Generated Plan",
                "language": "English",
                "subject_type": "General"
            }
        },
        "confidence": 0.9
    }
    return mock_agent