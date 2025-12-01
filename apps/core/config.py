"""Configuration management for BenchHub Plus."""

import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./benchhub_plus.db",
        description="Database connection URL"
    )
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Frontend Configuration
    frontend_host: str = Field(default="0.0.0.0", description="Frontend host")
    frontend_port: int = Field(default=3000, description="Frontend port")
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for browser redirects"
    )
    
    # LLM Configuration (for Planner Agent)
    openai_api_key: str = Field(
        description="OpenAI API key for planner agent"
    )
    planner_model: str = Field(
        default="gpt-4", 
        description="Model to use for planning agent"
    )
    planner_temperature: float = Field(
        default=0.1, 
        description="Temperature for planner model"
    )
    
    # Security
    secret_key: str = Field(
        description="Secret key for API key encryption (Fernet). Used to encrypt/decrypt model API keys stored in database."
    )
    
    # Google OAuth Configuration
    google_client_id: str = Field(
        description="Google OAuth Client ID"
    )
    google_client_secret: str = Field(
        description="Google OAuth Client Secret"
    )
    google_redirect_uri: str = Field(
        default="http://localhost:8001/api/v1/auth/google/callback",
        description="Google OAuth Redirect URI"
    )
    
    # JWT Configuration
    jwt_secret_key: str = Field(
        description="JWT Secret Key for access tokens"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT Algorithm"
    )
    access_token_expire_hours: int = Field(
        default=24,
        description="Access token expiration time in hours"
    )
    
    # Celery Configuration
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # HRET Configuration
    # TODO: Add HRET specific configuration when integrated
    hret_config_path: str = Field(
        default="./config/hret_config.yaml",
        description="Path to HRET configuration file"
    )
    benchhub_data_path: str = Field(
        default="./data/benchhub",
        description="Path to BenchHub data directory"
    )
    
    # Cache Configuration
    cache_ttl_seconds: int = Field(
        default=3600, 
        description="Cache TTL in seconds"
    )
    max_cache_size: int = Field(
        default=1000, 
        description="Maximum cache size"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60, 
        description="Rate limit per minute"
    )
    rate_limit_burst: int = Field(
        default=10,
        description="Rate limit burst"
    )

    cors_allowed_origins: List[str] = Field(
        default_factory=list,
        description="Comma-separated list of allowed CORS origins"
    )
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.database_url.startswith("sqlite")
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return self.database_url.startswith("postgresql")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
