"""Configuration management for BenchHub Plus."""

import logging
import os
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


_INSECURE_SECRET_DEFAULTS = {
    "",
    "change-me",
    "changeme",
    "secret",
    "secretkey",
    "password",
    "dev",
    "development",
    "test",
}


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
    db_pool_size: int = Field(
        default=10,
        description="SQLAlchemy connection pool size (ignored on SQLite / pgbouncer pooler)"
    )
    db_max_overflow: int = Field(
        default=20,
        description="SQLAlchemy connection pool overflow"
    )
    db_pool_timeout: int = Field(
        default=30,
        description="Seconds to wait for a free connection before giving up"
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
    dev_auth_bypass: bool = Field(
        default=False,
        description="Enable development auth bypass (non-production only)"
    )
    
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
    
    # GitHub OAuth Configuration
    github_client_id: str = Field(
        description="GitHub OAuth Client ID"
    )
    github_client_secret: str = Field(
        description="GitHub OAuth Client Secret"
    )
    github_redirect_uri: str = Field(
        default="http://localhost:8001/api/v1/auth/github/callback",
        description="GitHub OAuth Redirect URI"
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

    # Cookie / transport security
    cookie_secure: Optional[bool] = Field(
        default=None,
        description="Force Secure cookie flag. If unset, defaults to True when debug=False."
    )
    cookie_samesite: str = Field(
        default="lax",
        description="SameSite policy for auth cookies (lax, strict, none)"
    )

    # Trusted host header validation (production hardening)
    trusted_hosts: List[str] = Field(
        default_factory=list,
        description="Hosts allowed in Host header. Empty disables the check."
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def _validate_jwt_secret(cls, v: str) -> str:
        if v is None or len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(48))'"
            )
        if v.strip().lower() in _INSECURE_SECRET_DEFAULTS:
            raise ValueError("JWT_SECRET_KEY must not be a placeholder value")
        return v

    @field_validator("secret_key")
    @classmethod
    def _validate_secret_key(cls, v: str) -> str:
        if v is None or len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(48))'"
            )
        if v.strip().lower() in _INSECURE_SECRET_DEFAULTS:
            raise ValueError("SECRET_KEY must not be a placeholder value")
        return v

    @field_validator("cookie_samesite")
    @classmethod
    def _validate_samesite(cls, v: str) -> str:
        normalized = (v or "lax").lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("cookie_samesite must be one of: lax, strict, none")
        return normalized

    @model_validator(mode="after")
    def _enforce_production_safety(self) -> "Settings":
        """Refuse dangerous combinations when debug is off."""
        if not self.debug and self.dev_auth_bypass:
            raise ValueError(
                "DEV_AUTH_BYPASS=true is not allowed when DEBUG=false. "
                "Disable dev auth bypass before running in production."
            )
        return self

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.database_url.startswith("sqlite")

    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return self.database_url.startswith("postgresql")

    @property
    def is_production(self) -> bool:
        """Treat any non-debug, non-dev-bypass deployment as production-grade."""
        return not (self.debug or self.dev_auth_bypass)

    @property
    def effective_cookie_secure(self) -> bool:
        """Resolve Secure cookie flag with production-safe default."""
        if self.cookie_secure is not None:
            return bool(self.cookie_secure)
        return self.is_production


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
