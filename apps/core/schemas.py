"""Pydantic schemas for BenchHub Plus API."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class ModelInfo(BaseModel):
    """Model information for evaluation."""
    
    name: str = Field(..., description="Model name")
    api_base: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key")
    model_type: str = Field(default="openai", description="Model type (openai, anthropic, etc.)")
    
    @validator("api_base")
    def validate_api_base(cls, v: str) -> str:
        """Validate API base URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("API base must start with http:// or https://")
        return v.rstrip("/")


class LeaderboardQuery(BaseModel):
    """Query for generating leaderboard."""
    
    query: str = Field(..., description="Natural language query")
    models: List[ModelInfo] = Field(..., description="List of models to evaluate")
    
    @validator("models")
    def validate_models(cls, v: List[ModelInfo]) -> List[ModelInfo]:
        """Validate models list."""
        if not v:
            raise ValueError("At least one model must be provided")
        if len(v) > 10:  # Reasonable limit
            raise ValueError("Maximum 10 models allowed per request")
        return v


class LeaderboardEntry(BaseModel):
    """Single entry in leaderboard."""
    
    model_name: str
    language: str
    subject_type: str
    task_type: str
    score: float
    last_updated: datetime
    
    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    """Response containing leaderboard data."""
    
    entries: List[LeaderboardEntry]
    query: str
    generated_at: datetime
    total_models: int
    
    @validator("entries")
    def sort_entries(cls, v: List[LeaderboardEntry]) -> List[LeaderboardEntry]:
        """Sort entries by score descending."""
        return sorted(v, key=lambda x: x.score, reverse=True)


class TaskStatus(BaseModel):
    """Task status information."""
    
    task_id: str
    status: str = Field(..., regex="^(PENDING|STARTED|SUCCESS|FAILURE)$")
    plan_details: Optional[str] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    """Response for task creation."""
    
    task_id: str
    status: str
    message: str


class ExperimentSampleCreate(BaseModel):
    """Schema for creating experiment sample."""
    
    prompt: str
    answer: str
    skill_label: str
    target_label: str
    subject_label: str
    format_label: str
    dataset_name: str
    meta_data: Optional[Dict[str, Any]] = None
    correctness: float = Field(..., ge=0.0, le=1.0)


class ExperimentSampleResponse(BaseModel):
    """Response schema for experiment sample."""
    
    id: int
    prompt: str
    answer: str
    skill_label: str
    target_label: str
    subject_label: str
    format_label: str
    dataset_name: str
    meta_data: Optional[Dict[str, Any]] = None
    correctness: float
    timestamp: datetime
    
    class Config:
        from_attributes = True


class PlanConfig(BaseModel):
    """Configuration for evaluation plan."""
    
    language: str = Field(..., description="Target language (e.g., Korean, English)")
    subject_type: str = Field(..., description="Subject type (e.g., Technology, Science)")
    task_type: str = Field(..., description="Task type (e.g., Programming, Math)")
    sample_size: int = Field(default=100, ge=1, le=1000, description="Number of samples")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    
    class Config:
        schema_extra = {
            "example": {
                "language": "Korean",
                "subject_type": "Technology",
                "task_type": "Programming",
                "sample_size": 100,
                "seed": 42
            }
        }


class EvaluationResult(BaseModel):
    """Result of model evaluation."""
    
    model_name: str
    total_samples: int
    correct_samples: int
    accuracy: float
    average_score: float
    execution_time: float
    metadata: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "2.0.0"
    database_status: str = "connected"
    redis_status: str = "connected"