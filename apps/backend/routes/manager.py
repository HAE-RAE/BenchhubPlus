"""Manager endpoints for admin snapshot, audit logs, and moderation helpers."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from ...core.db import get_db, User
from ...core.schemas import ManagerSnapshot, ComponentHealth, LeaderboardEntry, AuditLogEntry
from ...core.config import get_settings
from ...worker.celery_app import celery_app
from ...worker.hret_runner import HRET_AVAILABLE
from ..dependencies import require_admin
from ..repositories.tasks_repo import TasksRepository
from ..repositories.leaderboard_repo import LeaderboardRepository
from ..services.orchestrator import EvaluationOrchestrator
from ..services.audit import AuditService
from .status import _parse_policy_tags

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/manager", tags=["manager"])
settings = get_settings()


def _component(name: str, status: str, version: Optional[str] = None, detail: Optional[Dict[str, Any]] = None) -> ComponentHealth:
    return ComponentHealth(
        name=name,
        status=status,
        version=version,
        detail=detail or {},
        checked_at=datetime.utcnow(),
    )


@router.get("/snapshot", response_model=ManagerSnapshot)
async def manager_snapshot(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Return aggregated snapshot for manager console."""
    orchestrator = EvaluationOrchestrator(db)
    repo = TasksRepository(db)
    leaderboard_repo = LeaderboardRepository(db)

    # Health checks
    health_map: Dict[str, ComponentHealth] = {}
    try:
        db.execute(text("SELECT 1"))
        health_map["database"] = _component("database", "connected")
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        health_map["database"] = _component("database", "disconnected", detail={"error": str(exc)})

    redis_client = getattr(request.app.state, "redis", None)
    if redis_client:
        try:
            await redis_client.ping()
            health_map["redis"] = _component("redis", "connected")
        except Exception as exc:
            health_map["redis"] = _component("redis", "disconnected", detail={"error": str(exc)})
    else:
        health_map["redis"] = _component("redis", "unavailable")

    try:
        inspection = celery_app.control.inspect(timeout=1)
        ping_result = inspection.ping() if inspection else None
        celery_status = "connected" if ping_result else "no_workers"
        health_map["celery"] = _component("celery", celery_status)
    except Exception as exc:
        health_map["celery"] = _component("celery", "disconnected", detail={"error": str(exc)})

    planner_status = "healthy" if orchestrator.planner_agent else "unavailable"
    health_map["planner"] = _component("planner", planner_status)
    health_map["hret"] = _component("hret", "available" if HRET_AVAILABLE else "unavailable")

    # Capacity and statistics
    system_stats = orchestrator.get_system_stats()
    tasks_stats = system_stats.get("tasks", {})
    capacity = {
        "pending": tasks_stats.get("PENDING", 0),
        "running": tasks_stats.get("STARTED", 0),
        "success": tasks_stats.get("SUCCESS", 0),
        "failure": tasks_stats.get("FAILURE", 0),
        "cancelled": tasks_stats.get("CANCELLED", 0),
        "cache_entries": system_stats.get("cache_entries", 0),
    }

    # Recent tasks
    recent_tasks = repo.get_recent_tasks(limit=20)
    task_items = []
    for task in recent_tasks:
        query_summary = ""
        if task.plan_details:
            try:
                plan_json = json.loads(task.plan_details)
                query_summary = plan_json.get("query") or plan_json.get("metadata", {}).get("name", "")
            except Exception:
                query_summary = ""
        duration = None
        if task.completed_at:
            duration = (task.completed_at - task.created_at).total_seconds()
        task_items.append(
            {
                "task_id": task.task_id,
                "status": task.status,
                "submitted_at": task.created_at,
                "completed_at": task.completed_at,
                "duration_seconds": duration,
                "policy_tags": _parse_policy_tags(task.policy_tags),
                "user_id": task.user_id,
                "model_count": task.model_count,
                "error_message": task.error_message,
                "query": query_summary,
            }
        )

    # Leaderboard entries
    leaderboard_entries = leaderboard_repo.get_leaderboard(limit=10, include_quarantined=True)
    leaderboard_models = [
        LeaderboardEntry(
            id=entry.id,
            model_name=entry.model_name,
            language=entry.language,
            subject_type=entry.subject_type,
            task_type=entry.task_type,
            score=entry.score,
            last_updated=entry.last_updated,
            quarantined=entry.quarantined,
        )
        for entry in leaderboard_entries
    ]

    return ManagerSnapshot(
        timestamp=datetime.utcnow(),
        health=health_map,
        capacity=capacity,
        tasks=task_items,
        leaderboard=leaderboard_models,
        planner_available=orchestrator.planner_agent is not None,
        hret_available=HRET_AVAILABLE,
    )


@router.get("/audit")
async def audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    resource: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List audit logs."""
    service = AuditService(db)
    logs, total = service.list_logs(limit=limit, offset=offset, resource=resource)

    def _parse_metadata(raw: Optional[str]) -> Optional[Dict[str, Any]]:
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return {"raw": raw}

    items = [
        AuditLogEntry(
            id=log.id,
            action=log.action,
            resource=log.resource,
            resource_id=log.resource_id,
            user_id=log.user_id,
            metadata=_parse_metadata(log.meta),
            created_at=log.created_at,
        )
        for log in logs
    ]

    return {"logs": items, "total": total, "limit": limit, "offset": offset}
