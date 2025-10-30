"""Pydantic schemas for BenchHub Plus API."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


# BenchHub Categories Configuration
BENCHHUB_COARSE_CATEGORIES = [
    "Art & Sports",
    "Culture",
    "HASS",
    "Science",
    "Social Intelligence",
    "Tech."
]

BENCHHUB_FINE_CATEGORIES = {
    "Art & Sports": [
        "Art & Sports/Architecture",
        "Art & Sports/Clothing",
        "Art & Sports/Education",
        "Art & Sports/Fashion",
        "Art & Sports/Festivals",
        "Art & Sports/Food",
        "Art & Sports/Language",
        "Art & Sports/Literature",
        "Art & Sports/Media",
        "Art & Sports/Music",
        "Art & Sports/Painting",
        "Art & Sports/Performing",
        "Art & Sports/Photography",
        "Art & Sports/Sculpture",
        "Art & Sports/Sports",
        "Art & Sports/Urban Eng.",
        "Art & Sports/arts&sports/animal",
        "Art & Sports/arts&sports/animal_life",
        "Art & Sports/arts&sports/animals",
        "Art & Sports/arts&sports/animation",
        "Art & Sports/arts&sports/anime",
        "Art & Sports/arts&sports/art",
        "Art & Sports/arts&sports/arts",
        "Art & Sports/arts&sports/artwork",
        "Art & Sports/arts&sports/barking",
        "Art & Sports/arts&sports/boat",
        "Art & Sports/arts&sports/branding",
        "Art & Sports/arts&sports/character",
        "Art & Sports/arts&sports/collecting",
        "Art & Sports/arts&sports/dance",
        "Art & Sports/arts&sports/design",
        "Art & Sports/arts&sports/digital_design",
        "Art & Sports/arts&sports/dog",
        "Art & Sports/arts&sports/dogs",
        "Art & Sports/arts&sports/drink",
        "Art & Sports/arts&sports/equestrian",
        "Art & Sports/arts&sports/fantasy",
        "Art & Sports/arts&sports/farming",
        "Art & Sports/arts&sports/fiction",
        "Art & Sports/arts&sports/fitness",
        "Art & Sports/arts&sports/flower",
        "Art & Sports/arts&sports/furniture",
        "Art & Sports/arts&sports/game",
        "Art & Sports/arts&sports/gaming",
        "Art & Sports/arts&sports/graphics",
        "Art & Sports/arts&sports/illustration",
        "Art & Sports/arts&sports/infographic",
        "Art & Sports/arts&sports/landscape",
        "Art & Sports/arts&sports/landscapes",
        "Art & Sports/arts&sports/nature",
        "Art & Sports/arts&sports/poetry",
        "Art & Sports/arts&sports/puzzle",
        "Art & Sports/arts&sports/reading",
        "Art & Sports/arts&sports/scenic",
        "Art & Sports/arts&sports/speech",
        "Art & Sports/arts&sports/toy",
        "Art & Sports/arts&sports/transportation",
        "Art & Sports/arts&sports/typography",
        "Art & Sports/arts&sports/urban",
        "Art & Sports/arts&sports/urban_art",
        "Art & Sports/arts&sports/urban_design",
        "Art & Sports/arts&sports/urban_environment",
        "Art & Sports/arts&sports/urban_life",
        "Art & Sports/arts&sports/urbanism",
        "Art & Sports/arts&sports/video_games",
        "Art & Sports/arts&sports/website",
        "Art & Sports/arts&sports/wine",
        "Art & Sports/arts&sports/zoology"
    ],
    "Culture": [
        "Culture/Celebration Holiday",
        "Culture/Clothing",
        "Culture/Daily Life",
        "Culture/Family",
        "Culture/Food",
        "Culture/Holiday",
        "Culture/Housing",
        "Culture/Leisure",
        "Culture/Tradition",
        "Culture/Work Life",
        "Culture/culture/attractions",
        "Culture/culture/friendship",
        "Culture/culture/hobbies",
        "Culture/culture/nature"
    ],
    "HASS": [
        "HASS/Administration",
        "HASS/Art & Sports",
        "HASS/Biology",
        "HASS/Celebration Holiday",
        "HASS/Cognitive Studies",
        "HASS/Culture",
        "HASS/Daily Life",
        "HASS/Economics",
        "HASS/Education",
        "HASS/Family",
        "HASS/Food",
        "HASS/Geography",
        "HASS/HASS",
        "HASS/History",
        "HASS/Language",
        "HASS/Law",
        "HASS/Literature",
        "HASS/Math",
        "HASS/Media",
        "HASS/Music",
        "HASS/Philosophy",
        "HASS/Physics",
        "HASS/Politics",
        "HASS/Psychology",
        "HASS/Religion",
        "HASS/Sports",
        "HASS/Tech.",
        "HASS/Trade",
        "HASS/Tradition",
        "HASS/Urban Eng.",
        "HASS/Welfare",
        "HASS/Work Life",
        "HASS/social&humanity/animal_welfare",
        "HASS/social&humanity/biography",
        "HASS/social&humanity/branding",
        "HASS/social&humanity/celebrity",
        "HASS/social&humanity/communication",
        "HASS/social&humanity/crime",
        "HASS/social&humanity/customer_support",
        "HASS/social&humanity/data_science",
        "HASS/social&humanity/database",
        "HASS/social&humanity/databases",
        "HASS/social&humanity/date",
        "HASS/social&humanity/dates",
        "HASS/social&humanity/datetime",
        "HASS/social&humanity/director",
        "HASS/social&humanity/drama",
        "HASS/social&humanity/environment",
        "HASS/social&humanity/fiction",
        "HASS/social&humanity/finance",
        "HASS/social&humanity/friendship",
        "HASS/social&humanity/health",
        "HASS/social&humanity/hero",
        "HASS/social&humanity/identity",
        "HASS/social&humanity/leadership",
        "HASS/social&humanity/library",
        "HASS/social&humanity/lifestyle",
        "HASS/social&humanity/management",
        "HASS/social&humanity/museum",
        "HASS/social&humanity/organizations",
        "HASS/social&humanity/privacy",
        "HASS/social&humanity/real_estate",
        "HASS/social&humanity/sociology",
        "HASS/social&humanity/technology",
        "HASS/social&humanity/transport",
        "HASS/social&humanity/transportation",
        "HASS/social&humanity/website",
        "HASS/social&humanity/workplace"
    ],
    "Science": [
        "Science/Astronomy",
        "Science/Atmospheric Science",
        "Science/Biology",
        "Science/Biomedical Eng.",
        "Science/Chemistry",
        "Science/Earth Science",
        "Science/Electrical Eng.",
        "Science/Geology",
        "Science/History",
        "Science/Language",
        "Science/Life Science",
        "Science/Math",
        "Science/Physics",
        "Science/Religion",
        "Science/Statistics",
        "Science/science/color",
        "Science/science/dna",
        "Science/science/dna2protein",
        "Science/science/numerology",
        "Science/science/plant"
    ],
    "Social Intelligence": [
        "Social Intelligence/Bias",
        "Social Intelligence/Commonsense",
        "Social Intelligence/Language",
        "Social Intelligence/Norms",
        "Social Intelligence/Value/Alignment",
        "Social Intelligence/misc/abstract",
        "Social Intelligence/misc/animal",
        "Social Intelligence/misc/cliche",
        "Social Intelligence/misc/color",
        "Social Intelligence/misc/diagnosis",
        "Social Intelligence/misc/durable",
        "Social Intelligence/misc/hate_crime",
        "Social Intelligence/misc/health",
        "Social Intelligence/misc/idiomatic_expression",
        "Social Intelligence/misc/norm",
        "Social Intelligence/misc/proverb",
        "Social Intelligence/misc/thinking",
        "Social Intelligence/misc/wellbeing"
    ],
    "Tech.": [
        "Tech./AI",
        "Tech./Aerospace Eng.",
        "Tech./Agricultural Eng.",
        "Tech./Biomedical Eng.",
        "Tech./Chemical Eng.",
        "Tech./Civil Eng.",
        "Tech./Coding",
        "Tech./Electrical Eng.",
        "Tech./Energy",
        "Tech./Environmental Eng.",
        "Tech./Food",
        "Tech./Geography",
        "Tech./IT",
        "Tech./Marine Eng.",
        "Tech./Materials Eng.",
        "Tech./Mechanics",
        "Tech./Nuclear Eng.",
        "Tech./Physics",
        "Tech./Urban Eng.",
        "Tech./tech/aircraft",
        "Tech./tech/airline",
        "Tech./tech/airlines",
        "Tech./tech/algorithm",
        "Tech./tech/animal",
        "Tech./tech/animal_welfare",
        "Tech./tech/animation",
        "Tech./tech/aquarium",
        "Tech./tech/automotive",
        "Tech./tech/aviation",
        "Tech./tech/azure",
        "Tech./tech/boat",
        "Tech./tech/cloud",
        "Tech./tech/communication",
        "Tech./tech/communications",
        "Tech./tech/cv",
        "Tech./tech/database",
        "Tech./tech/db",
        "Tech./tech/dice",
        "Tech./tech/ethereum",
        "Tech./tech/finance",
        "Tech./tech/financial",
        "Tech./tech/geo_loc",
        "Tech./tech/geolocation",
        "Tech./tech/graphics",
        "Tech./tech/ios",
        "Tech./tech/marine_biology",
        "Tech./tech/marine_eng",
        "Tech./tech/mobile",
        "Tech./tech/monitoring",
        "Tech./tech/network",
        "Tech./tech/ocr",
        "Tech./tech/office",
        "Tech./tech/programming",
        "Tech./tech/real_estate",
        "Tech./tech/remote_sensing",
        "Tech./tech/robotics",
        "Tech./tech/secure",
        "Tech./tech/security",
        "Tech./tech/transportation",
        "Tech./tech/uuid",
        "Tech./tech/vehicle",
        "Tech./tech/voice"
    ]
}


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