"""Pydantic schemas for BenchHub Plus API."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .categories import BENCHHUB_COARSE_CATEGORIES, BENCHHUB_FINE_CATEGORIES


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


class LeaderboardSuggestionRequest(BaseModel):
    """Request payload for leaderboard filter suggestions."""
    
    query: str = Field(..., description="User query describing desired leaderboard focus")


class LeaderboardSuggestionResponse(BaseModel):
    """Suggested filters derived from natural language query."""
    
    query: str
    language: Optional[str] = None
    subject_type: Optional[str] = None
    task_type: Optional[str] = None
    subject_type_options: List[str] = Field(default_factory=list)
    plan_summary: str
    used_planner: bool = False
    metadata: Optional[Dict[str, Any]] = None


class TaskStatus(BaseModel):
    """Task status information."""
    
    task_id: str
    status: str = Field(..., pattern="^(PENDING|STARTED|SUCCESS|FAILURE)$")
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
    """Configuration for evaluation plan based on BenchHub config structure."""
    
    # BenchHub specific fields
    problem_type: str = Field(..., description="Problem format: Binary/MCQA/short-form/open-ended")
    target_type: str = Field(..., description="Target type: General/Local")
    subject_type: List[str] = Field(..., description="Subject categories (coarse and fine-grained)")
    task_type: str = Field(..., description="Task type: Knowledge/Reasoning/Value/Alignment")
    external_tool_usage: bool = Field(default=False, description="Whether external tools are required")
    
    # Additional configuration
    language: str = Field(default="Korean", description="Target language (e.g., Korean, English)")
    sample_size: int = Field(default=100, ge=1, le=1000, description="Number of samples")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    
    @validator("problem_type")
    def validate_problem_type(cls, v: str) -> str:
        """Validate problem type."""
        valid_types = ["Binary", "MCQA", "short-form", "open-ended"]
        if v not in valid_types:
            raise ValueError(f"problem_type must be one of {valid_types}")
        return v
    
    @validator("target_type")
    def validate_target_type(cls, v: str) -> str:
        """Validate target type."""
        valid_types = ["General", "Local"]
        if v not in valid_types:
            raise ValueError(f"target_type must be one of {valid_types}")
        return v
    
    @validator("subject_type")
    def validate_subject_type(cls, v: List[str]) -> List[str]:
        """Validate subject type categories."""
        if not v:
            raise ValueError("subject_type cannot be empty")
        
        # Get all valid categories (coarse + fine-grained)
        all_fine_categories = []
        for fine_list in BENCHHUB_FINE_CATEGORIES.values():
            all_fine_categories.extend(fine_list)
        
        valid_categories = BENCHHUB_COARSE_CATEGORIES + all_fine_categories
        
        for category in v:
            if category not in valid_categories:
                raise ValueError(f"Invalid subject_type '{category}'. Must be one of the BenchHub categories.")
        
        return v
    
    @validator("task_type")
    def validate_task_type(cls, v: str) -> str:
        """Validate task type."""
        valid_types = ["Knowledge", "Reasoning", "Value", "Alignment"]
        if v not in valid_types:
            raise ValueError(f"task_type must be one of {valid_types}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "problem_type": "MCQA",
                "target_type": "General",
                "subject_type": ["Tech.", "Tech./Coding"],
                "task_type": "Knowledge",
                "external_tool_usage": False,
                "language": "Korean",
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
