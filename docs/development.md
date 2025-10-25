# Development Guide

This guide covers development setup, architecture, and contribution guidelines for BenchHub Plus.

## 🏗️ Architecture Overview

BenchHub Plus follows a microservices architecture with the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   Celery        │
│   Frontend      │◄──►│   Backend       │◄──►│   Workers       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │   PostgreSQL    │    │     Redis       │
         │              │   Database      │    │     Cache       │
         └──────────────┤                 │    └─────────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   HRET Toolkit  │
                        │   Integration   │
                        └─────────────────┘
```

### Component Responsibilities

- **Frontend (Streamlit)**: User interface, form handling, visualization
- **Backend (FastAPI)**: REST API, business logic, request orchestration
- **Workers (Celery)**: Async task processing, HRET integration, model evaluation
- **Database (PostgreSQL)**: Data persistence, caching, task tracking
- **Cache (Redis)**: Session storage, task queue, temporary data

## 🛠️ Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Git
- Docker (optional but recommended)

### Quick Setup

```bash
# Clone repository
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus

# Setup development environment
./scripts/setup.sh

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start development services
./scripts/deploy.sh development
```

### Manual Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Setup database
createdb benchhub_plus_dev
python -c "from apps.core.db import init_db; init_db()"

# Start services individually
./scripts/dev-backend.sh    # Terminal 1
./scripts/dev-worker.sh     # Terminal 2  
./scripts/dev-frontend.sh   # Terminal 3
```

## 📁 Project Structure

```
BenchhubPlus/
├── apps/                          # Application modules
│   ├── backend/                   # FastAPI backend
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── routers/              # API route handlers
│   │   ├── services/             # Business logic layer
│   │   └── repositories/         # Data access layer
│   ├── frontend/                 # Streamlit frontend
│   │   ├── streamlit_app.py      # Main Streamlit app
│   │   └── components/           # UI components
│   ├── worker/                   # Celery workers
│   │   ├── celery_app.py         # Celery configuration
│   │   ├── tasks/                # Async task definitions
│   │   └── hret_runner.py        # HRET integration
│   ├── core/                     # Shared core modules
│   │   ├── config.py             # Configuration management
│   │   ├── db.py                 # Database setup
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── schemas.py            # Pydantic schemas
│   │   └── security.py           # Security utilities
│   └── planner/                  # AI planning agent
│       ├── agent.py              # LLM-based planner
│       └── templates/            # Plan templates
├── docs/                         # Documentation
├── scripts/                      # Deployment scripts
├── tests/                        # Test suites
├── logs/                         # Application logs
├── docker-compose.yml            # Production deployment
├── docker-compose.dev.yml        # Development deployment
└── pyproject.toml               # Python dependencies
```

## 🔧 Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ... develop your feature ...

# Run tests
./scripts/test.sh

# Commit changes
git add .
git commit -m "feat: add your feature description"

# Push and create PR
git push origin feature/your-feature-name
```

### 2. Code Style

We use the following tools for code quality:

```bash
# Install development tools
pip install black isort flake8 mypy pytest

# Format code
black apps/
isort apps/

# Lint code
flake8 apps/
mypy apps/

# Run tests
pytest tests/
```

### 3. Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_models.py      # Database model tests
│   ├── test_services.py    # Service layer tests
│   └── test_utils.py       # Utility function tests
├── integration/            # Integration tests
│   ├── test_api.py         # API endpoint tests
│   ├── test_worker.py      # Worker task tests
│   └── test_database.py    # Database integration tests
├── e2e/                    # End-to-end tests
│   ├── test_evaluation.py  # Full evaluation flow
│   └── test_frontend.py    # Frontend interaction tests
└── fixtures/               # Test data and fixtures
    ├── sample_data.json
    └── mock_responses.py
```

### Running Tests

```bash
# All tests
pytest

# Specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# With coverage
pytest --cov=apps tests/

# Specific test file
pytest tests/unit/test_models.py

# Specific test function
pytest tests/unit/test_models.py::test_leaderboard_cache_creation
```

### Writing Tests

```python
# Unit test example
import pytest
from apps.core.models import LeaderboardCache

def test_leaderboard_cache_creation():
    cache = LeaderboardCache(
        model_name="test-model",
        score=0.85,
        language="English",
        subject_type="Math",
        task_type="QA"
    )
    assert cache.model_name == "test-model"
    assert cache.score == 0.85

# Integration test example
import pytest
from fastapi.testclient import TestClient
from apps.backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## 🔌 Adding New Features

### 1. Backend API Endpoint

```python
# apps/backend/routers/new_feature.py
from fastapi import APIRouter, Depends
from apps.core.schemas import NewFeatureRequest, NewFeatureResponse
from apps.backend.services.new_feature_service import NewFeatureService

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.post("/", response_model=NewFeatureResponse)
async def create_new_feature(
    request: NewFeatureRequest,
    service: NewFeatureService = Depends()
):
    return await service.create_feature(request)
```

### 2. Database Model

```python
# apps/core/models.py
from sqlalchemy import Column, String, DateTime, Float
from apps.core.db import Base

class NewFeatureModel(Base):
    __tablename__ = "new_features"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 3. Pydantic Schema

```python
# apps/core/schemas.py
from pydantic import BaseModel
from datetime import datetime

class NewFeatureRequest(BaseModel):
    name: str
    value: float

class NewFeatureResponse(BaseModel):
    id: str
    name: str
    value: float
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 4. Service Layer

```python
# apps/backend/services/new_feature_service.py
from apps.core.schemas import NewFeatureRequest, NewFeatureResponse
from apps.backend.repositories.new_feature_repository import NewFeatureRepository

class NewFeatureService:
    def __init__(self, repository: NewFeatureRepository):
        self.repository = repository
    
    async def create_feature(self, request: NewFeatureRequest) -> NewFeatureResponse:
        feature = await self.repository.create(request)
        return NewFeatureResponse.from_orm(feature)
```

### 5. Repository Layer

```python
# apps/backend/repositories/new_feature_repository.py
from sqlalchemy.orm import Session
from apps.core.models import NewFeatureModel
from apps.core.schemas import NewFeatureRequest

class NewFeatureRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, request: NewFeatureRequest) -> NewFeatureModel:
        feature = NewFeatureModel(
            id=str(uuid.uuid4()),
            name=request.name,
            value=request.value
        )
        self.db.add(feature)
        self.db.commit()
        self.db.refresh(feature)
        return feature
```

### 6. Frontend Component

```python
# apps/frontend/components/new_feature.py
import streamlit as st

def render_new_feature_form():
    st.subheader("New Feature")
    
    name = st.text_input("Feature Name")
    value = st.number_input("Feature Value", min_value=0.0)
    
    if st.button("Create Feature"):
        # Call API
        response = requests.post("/api/v1/new-feature/", json={
            "name": name,
            "value": value
        })
        
        if response.status_code == 200:
            st.success("Feature created successfully!")
        else:
            st.error("Failed to create feature")
```

## 🔄 Async Task Development

### Creating New Tasks

```python
# apps/worker/tasks/new_task.py
from apps.worker.celery_app import celery_app
from celery import Task

@celery_app.task(bind=True)
def new_evaluation_task(self: Task, task_data: dict):
    """New evaluation task implementation."""
    
    try:
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100}
        )
        
        # Perform task logic
        result = perform_evaluation(task_data)
        
        # Update progress
        self.update_state(
            state='PROGRESS', 
            meta={'current': 100, 'total': 100}
        )
        
        return result
        
    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc)}
        )
        raise
```

### Task Monitoring

```python
# Check task status
from apps.worker.celery_app import celery_app

result = celery_app.AsyncResult(task_id)
print(f"Status: {result.status}")
print(f"Result: {result.result}")
```

## 🐛 Debugging

### Backend Debugging

```python
# Add to your code for debugging
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")

# Use debugger
import pdb; pdb.set_trace()
```

### Frontend Debugging

```python
# Streamlit debugging
st.write("Debug info:", variable)
st.json(data_structure)

# Session state debugging
st.write("Session state:", st.session_state)
```

### Worker Debugging

```bash
# Run worker with debug logging
celery -A apps.worker.celery_app worker --loglevel=debug

# Monitor tasks
celery -A apps.worker.celery_app events

# Inspect workers
celery -A apps.worker.celery_app inspect active
```

## 📊 Performance Optimization

### Database Optimization

```python
# Use database indexes
class LeaderboardCache(Base):
    __tablename__ = "leaderboard_cache"
    
    # Add indexes for frequently queried fields
    __table_args__ = (
        Index('idx_model_score', 'model_name', 'score'),
        Index('idx_language_subject', 'language', 'subject_type'),
    )

# Use query optimization
def get_leaderboard_optimized(db: Session, filters: dict):
    query = db.query(LeaderboardCache)
    
    # Add filters efficiently
    if filters.get('language'):
        query = query.filter(LeaderboardCache.language == filters['language'])
    
    # Use pagination
    return query.offset(filters.get('offset', 0)).limit(filters.get('limit', 100))
```

### Caching Strategy

```python
# Redis caching
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Compute and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(expiration=1800)
def expensive_computation(data):
    # Expensive operation
    return result
```

## 🔐 Security Considerations

### API Security

```python
# Input validation
from pydantic import BaseModel, validator

class EvaluationRequest(BaseModel):
    query: str
    models: List[ModelConfig]
    
    @validator('query')
    def validate_query(cls, v):
        if len(v) > 1000:
            raise ValueError('Query too long')
        return v.strip()

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/leaderboard/generate")
@limiter.limit("10/minute")
async def generate_leaderboard(request: Request, ...):
    # Endpoint implementation
    pass
```

### Data Protection

```python
# Encrypt sensitive data
from cryptography.fernet import Fernet

def encrypt_api_key(api_key: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted_key.encode()).decode()
```

## 📝 Documentation

### Code Documentation

```python
def evaluate_model(model_config: ModelConfig, samples: List[Sample]) -> EvaluationResult:
    """
    Evaluate a model on given samples.
    
    Args:
        model_config: Configuration for the model to evaluate
        samples: List of evaluation samples
        
    Returns:
        EvaluationResult containing scores and metrics
        
    Raises:
        ModelAPIError: If model API call fails
        ValidationError: If samples are invalid
        
    Example:
        >>> config = ModelConfig(name="gpt-4", api_key="sk-...")
        >>> samples = [Sample(question="What is 2+2?", answer="4")]
        >>> result = evaluate_model(config, samples)
        >>> print(result.average_score)
        0.95
    """
    # Implementation
    pass
```

### API Documentation

```python
# FastAPI automatic documentation
@app.post(
    "/api/v1/leaderboard/generate",
    response_model=TaskResponse,
    summary="Generate Leaderboard",
    description="Create a new evaluation task based on natural language query",
    responses={
        200: {"description": "Task created successfully"},
        400: {"description": "Invalid request data"},
        422: {"description": "Validation error"}
    }
)
async def generate_leaderboard(request: EvaluationRequest):
    """
    Generate a new leaderboard evaluation.
    
    This endpoint accepts a natural language query and model configurations,
    then creates an asynchronous evaluation task.
    """
    pass
```

## 🚀 Deployment

### Environment Configuration

```bash
# Production environment variables
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export CELERY_BROKER_URL="redis://host:6379/0"
export OPENAI_API_KEY="sk-..."
export DEBUG="false"
export LOG_LEVEL="info"
```

### Docker Build

```bash
# Build images
docker build -f Dockerfile.backend -t benchhub-backend .
docker build -f Dockerfile.worker -t benchhub-worker .
docker build -f Dockerfile.frontend -t benchhub-frontend .

# Run with docker-compose
docker-compose up -d
```

### Health Checks

```python
# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """System health check."""
    
    # Check database
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    # Check Redis
    try:
        redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    
    # Overall status
    status = "healthy" if all([
        db_status == "connected",
        redis_status == "connected"
    ]) else "unhealthy"
    
    return {
        "status": status,
        "database_status": db_status,
        "redis_status": redis_status,
        "timestamp": datetime.utcnow()
    }
```

## 🤝 Contributing

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests for new functionality**
5. **Ensure all tests pass**
6. **Update documentation**
7. **Submit pull request**

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact considered
- [ ] Backward compatibility maintained

### Issue Templates

Use the provided issue templates for:
- Bug reports
- Feature requests
- Documentation improvements
- Performance issues

---

*For questions about development or to discuss architectural decisions, please open a discussion in our GitHub repository.*