"""FastAPI backend main application."""

import logging
import sys
from contextlib import asynccontextmanager

import redis.asyncio as redis_asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from ..core.config import get_settings
from ..core.db import init_db
from ..core.security import RedisRateLimiter
from ..worker.celery_app import celery_app
from .routes import auth, leaderboard, status, hret
from .seeding import seed_database  # <-- [수정] 시딩 함수 임포트

try:
    from kombu.exceptions import OperationalError
except Exception:  # pragma: no cover - kombu is an optional dependency for type hints
    OperationalError = Exception

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/backend.log") if "logs" else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting BenchHub Plus Backend...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
        
        # --- [수정] 이 부분 추가 ---
        # DB 테이블 생성 후, 시딩 로직 실행
        seed_database()
        # --- 여기까지 ---
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    redis_client = None
    celery_connection = None

    # Initialize Redis connection
    try:
        redis_client = redis_asyncio.from_url(settings.redis_url)
        await redis_client.ping()
        app.state.redis = redis_client
        app.state.redis_rate_limiter = RedisRateLimiter(
            redis_client,
            settings.rate_limit_per_minute,
            60,
        )
        logger.info("Redis connection established")
    except Exception as redis_error:
        logger.error(f"Failed to connect to Redis: {redis_error}")
        raise RuntimeError("Redis connection failed") from redis_error

    # Initialize Celery connection
    try:
        celery_connection = celery_app.connection()
        celery_connection.ensure_connection(max_retries=3)
        app.state.celery_connection = celery_connection
        logger.info("Celery broker connection established")
    except OperationalError as celery_error:
        logger.error(f"Failed to connect to Celery broker: {celery_error}")
        if redis_client:
            await redis_client.close()
        raise RuntimeError("Celery broker connection failed") from celery_error

    app.state.redis_status = "connected"
    app.state.celery_status = "connected"

    logger.info("Backend startup completed")

    yield

    # Shutdown
    logger.info("Shutting down BenchHub Plus Backend...")

    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")

    if celery_connection:
        celery_connection.release()
        logger.info("Celery connection released")


# Create FastAPI application
app = FastAPI(
    title="BenchHub Plus API",
    description="Interactive Leaderboard System for Dynamic LLM Evaluation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
allowed_origins = settings.cors_allowed_origins
if not allowed_origins:
    # Default to allowing frontend in development
    allowed_origins = [
        f"http://{settings.frontend_host}:{settings.frontend_port}",
        "http://localhost:8501",
    ]
    logger.warning(f"CORS allowed origins not configured, using defaults: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(leaderboard.router)
app.include_router(status.router)
app.include_router(hret.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "BenchHub Plus API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1")
async def api_info():
    """API information endpoint."""
    return {
        "name": "BenchHub Plus API",
        "version": "2.0.0",
        "endpoints": {
            "auth": {
                "google_login": "GET /api/v1/auth/google/login",
                "google_callback": "GET /api/v1/auth/google/callback",
                "me": "GET /api/v1/auth/me",
                "logout": "POST /api/v1/auth/logout"
            },
            "leaderboard": {
                "generate": "POST /api/v1/leaderboard/generate",
                "browse": "GET /api/v1/leaderboard/browse",
                "categories": "GET /api/v1/leaderboard/categories",
                "stats": "GET /api/v1/leaderboard/stats"
            },
            "hret": {
                "status": "GET /hret/status",
                "config": "GET /hret/config",
                "evaluate": "POST /hret/evaluate",
                "task_status": "GET /hret/evaluate/{task_id}",
                "validate_plan": "POST /hret/validate-plan",
                "results": "GET /hret/results",
                "leaderboard": "GET /hret/leaderboard"
            },
            "tasks": {
                "status": "GET /api/v1/tasks/{task_id}",
                "list": "GET /api/v1/tasks",
                "cancel": "DELETE /api/v1/tasks/{task_id}"
            },
            "system": {
                "health": "GET /api/v1/health",
                "stats": "GET /api/v1/stats"
            }
        }
    }


def create_app() -> FastAPI:
    """Factory function to create FastAPI app."""
    return app


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "apps.backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )