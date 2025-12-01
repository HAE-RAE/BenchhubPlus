"""Status and health check API routes."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status, Response, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from ...core.db import get_db
from ...core.schemas import TaskStatus, HealthResponse, TaskActionRequest, TaskDetailResponse
from ..repositories.tasks_repo import TasksRepository
from ..services.audit import AuditService
from ..services.orchestrator import EvaluationOrchestrator
from ..dependencies import require_admin, get_optional_user, get_current_user
from ...worker.celery_app import celery_app
from ...worker.tasks import run_evaluation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["status"])


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO8601 datetime string."""
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid datetime format") from exc


def _parse_policy_tags(raw: Optional[str]) -> List[str]:
    """Parse policy tags stored as JSON or comma string."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except Exception:
        pass
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request, response: Response, db: Session = Depends(get_db)):
    """Health check endpoint."""

    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"

    redis_status = "unknown"
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is None:
        redis_status = "unavailable"
    else:
        try:
            await redis_client.ping()
            redis_status = "connected"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            redis_status = "disconnected"

    celery_status = "unknown"
    try:
        inspection = celery_app.control.inspect(timeout=1)
        ping_result = inspection.ping() if inspection else None
        if ping_result:
            celery_status = "connected"
        else:
            celery_status = "no_workers"
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        celery_status = "disconnected"

    # Determine overall status
    component_statuses = [db_status, redis_status, celery_status]
    overall_status = "healthy" if all(status == "connected" for status in component_statuses) else "unhealthy"

    response_status = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    response.status_code = response_status

    health_payload = HealthResponse(
        status=overall_status,
        database_status=db_status,
        redis_status=redis_status,
        celery_status=celery_status
    )

    return health_payload


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task_status(
    task_id: str = Path(..., description="Task ID"),
    db: Session = Depends(get_db)
):
    """Get status of evaluation task."""
    
    try:
        orchestrator = EvaluationOrchestrator(db)
        task_info = orchestrator.get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/tasks/{task_id}")
async def control_task(
    task_id: str,
    payload: TaskActionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Control a task (cancel/hold/resume/restart)."""
    repo = TasksRepository(db)
    task = repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        action = payload.action.lower()
        if action == "cancel":
            success = repo.cancel_task(task_id)
            if not success:
                raise HTTPException(status_code=400, detail="Unable to cancel task")
        elif action == "hold":
            task.status = "HOLD"
            db.commit()
        elif action == "resume":
            task.status = "PENDING"
            db.commit()
        elif action == "restart":
            if not task.plan_details:
                raise HTTPException(status_code=400, detail="Task missing plan details for restart")
            task.status = "PENDING"
            task.completed_at = None
            task.error_message = None
            task.error_log = None
            task.result = None
            db.commit()
            try:
                run_evaluation.delay(task.task_id, task.plan_details)
            except Exception as dispatch_error:
                repo.update_task_status(
                    task.task_id,
                    "FAILURE",
                    error_message=str(dispatch_error),
                )
                raise HTTPException(status_code=500, detail="Failed to dispatch restart") from dispatch_error
        else:
            raise HTTPException(status_code=400, detail="Unsupported action")

        if payload.policy_tags is not None:
            repo.update_policy_tags(task_id, json.dumps(payload.policy_tags))

        AuditService(db).log_action(
            action=f"task.{action}",
            resource="task",
            resource_id=task_id,
            user_id=getattr(current_user, "id", None),
            metadata=payload.model_dump(),
        )
        return {"message": f"Task {task_id} updated", "action": action}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to control task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tasks/{task_id}/details", response_model=TaskDetailResponse)
async def get_task_details(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Return full task payload and logs."""
    repo = TasksRepository(db)
    task = repo.get_task_details(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    def _safe_json(payload: Optional[str]) -> Optional[Dict[str, Any]]:
        if payload is None:
            return None
        try:
            return json.loads(payload)
        except Exception:
            return {"raw": payload}

    return TaskDetailResponse(
        task_id=task.task_id,
        status=task.status,
        created_at=task.created_at,
        completed_at=task.completed_at,
        user_id=task.user_id,
        model_count=task.model_count,
        policy_tags=_parse_policy_tags(task.policy_tags),
        request_payload=_safe_json(task.request_payload),
        plan_details=_safe_json(task.plan_details),
        result=_safe_json(task.result),
        error_message=task.error_message,
        error_log=task.error_log,
    )


@router.get("/tasks")
async def list_tasks(
    statuses: Optional[List[str]] = Query(None, description="Filter by statuses"),
    user_id: Optional[int] = Query(None, description="Filter by user id"),
    start_date: Optional[str] = Query(None, description="Start date (ISO8601)"),
    end_date: Optional[str] = Query(None, description="End date (ISO8601)"),
    min_models: Optional[int] = Query(None, ge=0, description="Minimum model count"),
    max_models: Optional[int] = Query(None, ge=0, description="Maximum model count"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """List evaluation tasks with filters and pagination (admin)."""
    
    try:
        allowed_statuses = {"PENDING", "STARTED", "SUCCESS", "FAILURE", "CANCELLED", "HOLD"}
        if statuses:
            normalized = [status.upper() for status in statuses]
            for status_value in normalized:
                if status_value not in allowed_statuses:
                    raise HTTPException(status_code=400, detail=f"Unsupported status {status_value}")
            statuses = normalized
        
        repo = TasksRepository(db)
        tasks, total = repo.filter_tasks(
            statuses=statuses,
            user_id=user_id,
            start_date=_parse_datetime(start_date),
            end_date=_parse_datetime(end_date),
            min_models=min_models,
            max_models=max_models,
            page=page,
            page_size=page_size,
        )
        
        return {
            "tasks": [
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "created_at": task.created_at,
                    "completed_at": task.completed_at,
                    "policy_tags": _parse_policy_tags(task.policy_tags),
                    "user_id": task.user_id,
                    "model_count": task.model_count,
                    "has_error": bool(task.error_message),
                }
                for task in tasks
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str = Path(..., description="Task ID"),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Cancel a pending evaluation task."""
    
    try:
        repo = TasksRepository(db)
        success = repo.cancel_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Task not found or cannot be cancelled"
            )
        AuditService(db).log_action(
            action="task.cancel",
            resource="task",
            resource_id=task_id,
            user_id=getattr(current_user, "id", None),
            metadata=None,
        )
        return {"message": f"Task {task_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get comprehensive system statistics."""
    
    try:
        orchestrator = EvaluationOrchestrator(db)
        stats = orchestrator.get_system_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/maintenance/cleanup")
async def cleanup_old_data(
    days_old: int = 7,
    db: Session = Depends(get_db)
):
    """Clean up old tasks and data."""
    
    try:
        repo = TasksRepository(db)
        cleaned_tasks = repo.cleanup_old_tasks(days_old)
        
        # TODO: Add cleanup for other data types if needed
        
        return {
            "message": f"Cleanup completed",
            "cleaned_tasks": cleaned_tasks
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
