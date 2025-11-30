"""Leaderboard API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...core.db import get_db, User
from ...core.schemas import (
    LeaderboardQuery,
    LeaderboardResponse,
    LeaderboardEntry,
    LeaderboardSuggestionRequest,
    LeaderboardSuggestionResponse,
    TaskResponse,
    ErrorResponse
)
from ...core.security import rate_limiter
from ..services.orchestrator import EvaluationOrchestrator
from ..dependencies import get_optional_user, require_admin
from ..services.audit import AuditService
from ..repositories.leaderboard_repo import LeaderboardRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/leaderboard", tags=["leaderboard"])


class LeaderboardAdminEntry(BaseModel):
    """Payload for manual leaderboard moderation."""

    model_name: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)
    subject_type: str = Field(..., min_length=1)
    task_type: str = Field(..., min_length=1)
    score: float = Field(..., ge=0.0)
    quarantined: bool = Field(default=False)


@router.post("/generate", response_model=TaskResponse)
async def generate_leaderboard(
    query: LeaderboardQuery,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Generate leaderboard for given query and models."""

    client_ip = request.client.host if request.client else "anonymous"

    remaining = None
    limiter = getattr(request.app.state, "redis_rate_limiter", None)

    if limiter:
        allowed, remaining = await limiter.is_allowed(client_ip)
    else:
        allowed = rate_limiter.is_allowed(client_ip)
        remaining = rate_limiter.get_remaining(client_ip)

    if not allowed:
        headers = {"Retry-After": "60"}
        if remaining is not None:
            headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers=headers,
        )

    try:
        orchestrator = EvaluationOrchestrator(db)
        user_id = current_user.id if current_user else None
        result = orchestrator.generate_leaderboard(query, user_id=user_id)

        logger.info(f"Generated leaderboard task: {result.task_id}")
        response_headers = {}
        if remaining is not None:
            response_headers["X-RateLimit-Remaining"] = str(max(0, remaining - 1))

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=result.dict(),
            headers=response_headers or None,
        )
        
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
    include_quarantined: bool = Query(False, description="Include quarantined entries"),
    db: Session = Depends(get_db)
):
    """Browse existing leaderboard entries with optional filtering."""
    
    try:
        orchestrator = EvaluationOrchestrator(db)
        result = orchestrator.get_leaderboard_by_criteria(
            language=language,
            subject_type=subject_type,
            task_type=task_type,
            limit=limit,
            include_quarantined=include_quarantined,
        )
        
        logger.info(f"Retrieved {len(result.entries)} leaderboard entries")
        return result
        
    except Exception as e:
        logger.error(f"Failed to browse leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/suggest", response_model=LeaderboardSuggestionResponse)
async def suggest_leaderboard_filters(
    payload: LeaderboardSuggestionRequest,
    db: Session = Depends(get_db)
):
    """Suggest leaderboard filters derived from a natural language query."""
    
    try:
        orchestrator = EvaluationOrchestrator(db)
        suggestion = orchestrator.suggest_leaderboard_filters(payload.query)
        logger.info(
            "Provided leaderboard suggestion for query '%s' (used_planner=%s)",
            payload.query,
            suggestion.used_planner
        )
        return suggestion
    except Exception as e:
        logger.error(f"Failed to suggest leaderboard filters: {e}")
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


@router.post(
    "/entries",
    dependencies=[Depends(require_admin)],
    response_model=LeaderboardEntry,
    status_code=status.HTTP_201_CREATED,
)
async def create_leaderboard_entry(
    payload: LeaderboardAdminEntry,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create or update a leaderboard entry manually (admin)."""
    try:
        repo = LeaderboardRepository(db)
        entry = repo.manual_entry(
            model_name=payload.model_name,
            language=payload.language,
            subject_type=payload.subject_type,
            task_type=payload.task_type,
            score=payload.score,
            quarantined=payload.quarantined,
        )
        AuditService(db).log_action(
            action="leaderboard.manual_entry",
            resource="leaderboard",
            resource_id=str(entry.id),
            user_id=current_user.id,
            metadata=payload.model_dump(),
        )
        return LeaderboardEntry(
            id=entry.id,
            model_name=entry.model_name,
            language=entry.language,
            subject_type=entry.subject_type,
            task_type=entry.task_type,
            score=entry.score,
            last_updated=entry.last_updated,
            quarantined=entry.quarantined,
        )
    except Exception as e:
        logger.error(f"Failed to create leaderboard entry: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/entries/{entry_id}",
    dependencies=[Depends(require_admin)],
)
async def delete_leaderboard_entry(
    entry_id: int,
    quarantine: bool = Query(True, description="Soft delete (quarantine) entry"),
    hard: bool = Query(False, description="Hard delete instead of quarantine"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete or quarantine leaderboard entry."""
    try:
        repo = LeaderboardRepository(db)
        deleted = False
        if hard:
            deleted = repo.hard_delete(entry_id)
        else:
            deleted = repo.soft_delete(entry_id, quarantine=quarantine)

        if not deleted:
            raise HTTPException(status_code=404, detail="Entry not found")

        AuditService(db).log_action(
            action="leaderboard.delete" if hard else "leaderboard.quarantine",
            resource="leaderboard",
            resource_id=str(entry_id),
            user_id=current_user.id,
            metadata={"hard": hard, "quarantine": quarantine},
        )
        return {"message": "Entry deleted" if hard else "Entry quarantined"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete leaderboard entry: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/cache")
async def clear_cache(
    older_than_hours: Optional[int] = Query(None, ge=1, description="Clear entries older than N hours"),
    db: Session = Depends(get_db)
):
    """Clear leaderboard cache."""
    
    try:
        repo = LeaderboardRepository(db)
        count = repo.clear_cache(older_than_hours)
        
        logger.info(f"Cleared {count} cache entries")
        return {"message": f"Cleared {count} cache entries"}
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
