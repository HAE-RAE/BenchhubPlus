"""Leaderboard API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...core.schemas import (
    LeaderboardQuery,
    LeaderboardResponse,
    TaskResponse,
    ErrorResponse
)
from ...core.security import rate_limiter
from ..services.orchestrator import EvaluationOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/leaderboard", tags=["leaderboard"])


@router.post("/generate", response_model=TaskResponse)
async def generate_leaderboard(
    query: LeaderboardQuery,
    db: Session = Depends(get_db)
):
    """Generate leaderboard for given query and models."""
    
    # TODO: Add rate limiting based on IP or user
    # client_ip = request.client.host
    # if not rate_limiter.is_allowed(client_ip):
    #     raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        orchestrator = EvaluationOrchestrator(db)
        result = orchestrator.generate_leaderboard(query)
        
        logger.info(f"Generated leaderboard task: {result.task_id}")
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/browse", response_model=LeaderboardResponse)
async def browse_leaderboard(
    language: Optional[str] = Query(None, description="Filter by language"),
    subject_type: Optional[str] = Query(None, description="Filter by subject type"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of entries"),
    db: Session = Depends(get_db)
):
    """Browse existing leaderboard entries with optional filtering."""
    
    try:
        orchestrator = EvaluationOrchestrator(db)
        result = orchestrator.get_leaderboard_by_criteria(
            language=language,
            subject_type=subject_type,
            task_type=task_type,
            limit=limit
        )
        
        logger.info(f"Retrieved {len(result.entries)} leaderboard entries")
        return result
        
    except Exception as e:
        logger.error(f"Failed to browse leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get available categories (languages, subjects, tasks)."""
    
    try:
        from sqlalchemy import distinct
        from ...core.db import LeaderboardCache
        
        # Get distinct values for each category
        languages = db.query(distinct(LeaderboardCache.language)).all()
        subjects = db.query(distinct(LeaderboardCache.subject_type)).all()
        tasks = db.query(distinct(LeaderboardCache.task_type)).all()
        
        return {
            "languages": [lang[0] for lang in languages],
            "subject_types": [subj[0] for subj in subjects],
            "task_types": [task[0] for task in tasks]
        }
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats")
async def get_leaderboard_stats(db: Session = Depends(get_db)):
    """Get leaderboard statistics."""
    
    try:
        orchestrator = EvaluationOrchestrator(db)
        stats = orchestrator.get_system_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/cache")
async def clear_cache(
    older_than_hours: Optional[int] = Query(None, ge=1, description="Clear entries older than N hours"),
    db: Session = Depends(get_db)
):
    """Clear leaderboard cache."""
    
    try:
        from ..repositories.leaderboard_repo import LeaderboardRepository
        
        repo = LeaderboardRepository(db)
        count = repo.clear_cache(older_than_hours)
        
        logger.info(f"Cleared {count} cache entries")
        return {"message": f"Cleared {count} cache entries"}
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")