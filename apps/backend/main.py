"""FastAPI backend main application."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from ..core.config import get_settings
from ..core.db import init_db
from .routes import leaderboard, status, hret

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
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # TODO: Initialize Redis connection
    # TODO: Initialize Celery connection
    
    logger.info("Backend startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BenchHub Plus Backend...")


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
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