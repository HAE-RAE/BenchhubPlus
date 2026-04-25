"""Status and health check API routes."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status, Response, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field, validator
from celery import states

from ...core.db import User, get_db
from ...core.schemas import (
    TaskStatus,
    HealthResponse,
    TaskActionRequest,
    TaskDetailResponse,
    CleanupTaskStatus,
    CleanupProgress,
)
from ...core.security import validate_task_identifier
from ..repositories.tasks_repo import TasksRepository
from ..services.audit import AuditService
from ..services.orchestrator import EvaluationOrchestrator
from ..dependencies import require_admin, get_optional_user, get_current_user
from ...worker.celery_app import celery_app
from ...worker.tasks import run_evaluation, cleanup_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["status"])


CLEANUP_ALLOWED_RESOURCES = {"tasks", "samples", "cache"}


class CleanupRequest(BaseModel):
    """Request payload for maintenance cleanup."""

    resources: List[str] = Field(
        default_factory=lambda: ["tasks", "samples", "cache"],
        description="List of resources to clean: tasks, samples, cache",
    )
    days_old: int = Field(7, ge=1, description="Remove data older than N days")
    limit: int = Field(500, ge=1, le=10000, description="Maximum records per resource to delete")
    dry_run: bool = Field(False, description="Report counts without deleting")
    hard_delete: bool = Field(False, description="Hard delete cache (otherwise quarantine)")

    @validator("resources")
    def validate_resources(cls, value: List[str]) -> List[str]:
        """Ensure resources are allowed."""
        filtered = [res for res in value if res in CLEANUP_ALLOWED_RESOURCES]
        if not filtered:
            raise ValueError(f"resources must include one of {sorted(CLEANUP_ALLOWED_RESOURCES)}")
        return filtered


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


def _is_admin(user: Optional[User]) -> bool:
    return bool(user and (user.is_admin or user.role == "admin"))


def _authorize_task_access(task, user: Optional[User]) -> None:
    """Ensure current user can access the task."""
    if task.user_id is None:
        return
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if _is_admin(user) or task.user_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Not authorized to access this task")


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
    task_id: str = Path(..., description="Task ID", min_length=1, max_length=128),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get status of evaluation task."""

    validate_task_identifier(task_id)
    try:
        repo = TasksRepository(db)
        task = repo.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        _authorize_task_access(task, current_user)

        result: Dict[str, Any] = {
            "task_id": task.task_id,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
        }

        if task.result:
            try:
                result["result"] = json.loads(task.result)
            except json.JSONDecodeError:
                result["result"] = task.result

        if task.error_message:
            result["error_message"] = task.error_message

        # Include request_payload for model configs + sample scale (strip api_key)
        if task.request_payload:
            try:
                rp = json.loads(task.request_payload)
                models_safe = [
                    {k: v for k, v in m.items() if k != "api_key"}
                    for m in (rp.get("models") or [])
                ]
                result["request_payload"] = {
                    "sample_scale": rp.get("sample_scale", "medium"),
                    "models": models_safe,
                    "query": rp.get("query", ""),
                    "category_language": rp.get("category_language"),
                    "category_subject": rp.get("category_subject"),
                    "category_task_type": rp.get("category_task_type"),
                }
            except Exception:
                pass

        # Enrich with Celery PROGRESS meta when task is running
        if task.status in ("PENDING", "STARTED", "PROGRESS"):
            try:
                async_result = celery_app.AsyncResult(task.task_id)
                if async_result.state == "PROGRESS" and isinstance(async_result.info, dict):
                    meta = async_result.info
                    result["stage"] = meta.get("status", "")
                    result["stage_current"] = meta.get("current", 0)
                    result["stage_total"] = meta.get("total", 1)
                elif async_result.state == "STARTED":
                    result["stage"] = "Starting evaluation"
                    result["stage_current"] = 0
                    result["stage_total"] = 1
            except Exception:
                pass
        
        return result
        
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
    validate_task_identifier(task_id)
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
    current_user: User = Depends(get_current_user),
):
    """Return full task payload and logs."""
    validate_task_identifier(task_id)
    repo = TasksRepository(db)
    task = repo.get_task_details(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _authorize_task_access(task, current_user)

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
    current_user: User = Depends(get_current_user),
):
    """List evaluation tasks with filters and pagination (admin or own tasks)."""
    
    try:
        allowed_statuses = {"PENDING", "STARTED", "SUCCESS", "FAILURE", "CANCELLED", "HOLD"}
        if statuses:
            normalized = [status.upper() for status in statuses]
            for status_value in normalized:
                if status_value not in allowed_statuses:
                    raise HTTPException(status_code=400, detail=f"Unsupported status {status_value}")
            statuses = normalized
        
        if not _is_admin(current_user):
            user_id = current_user.id

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
        
        def _extract_query(task) -> str:
            if task.request_payload:
                try:
                    return json.loads(task.request_payload).get("query", "") or ""
                except Exception:
                    pass
            return ""

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
                    "query": _extract_query(task),
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


@router.delete("/tasks/{task_id}/hard")
async def delete_task(
    task_id: str = Path(..., description="Task ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hard-delete a task from the database."""
    validate_task_identifier(task_id)
    try:
        repo = TasksRepository(db)
        task = repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        _authorize_task_access(task, current_user)
        repo.delete_task(task_id)
        AuditService(db).log_action(
            action="task.delete",
            resource="task",
            resource_id=task_id,
            user_id=getattr(current_user, "id", None),
            metadata=None,
        )
        return {"message": f"Task {task_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str = Path(..., description="Task ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending evaluation task."""

    validate_task_identifier(task_id)
    try:
        repo = TasksRepository(db)
        task = repo.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found",
            )

        _authorize_task_access(task, current_user)
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
async def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive system statistics."""
    
    try:
        orchestrator = EvaluationOrchestrator(db)
        stats = orchestrator.get_system_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/maintenance/cleanup",
    response_model=CleanupTaskStatus,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_admin)],
)
async def schedule_cleanup(
    payload: CleanupRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Schedule cleanup as an async task (202)."""

    try:
        async_result = cleanup_task.delay(
            days_old=payload.days_old,
            resources=payload.resources,
            dry_run=payload.dry_run,
            limit=payload.limit,
            hard_delete=payload.hard_delete,
        )

        AuditService(db).log_action(
            action="maintenance.cleanup.schedule",
            resource="maintenance",
            resource_id=getattr(async_result, "id", None),
            user_id=getattr(current_user, "id", None),
            metadata=payload.model_dump(),
        )

        progress = CleanupProgress(
            current=0,
            total=len(payload.resources),
            stage="queued",
            eta_seconds=None,
        )

        return CleanupTaskStatus(
            task_id=getattr(async_result, "id", ""),
            status="PENDING",
            progress=progress,
            resources={},
            summary={"dry_run": payload.dry_run},
            params=payload.model_dump(),
            dry_run=payload.dry_run,
        )
    except Exception as e:
        logger.error(f"Failed to schedule cleanup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/maintenance/cleanup/{task_id}",
    response_model=CleanupTaskStatus,
    dependencies=[Depends(require_admin)],
)
async def get_cleanup_status(
    task_id: str,
    db: Session = Depends(get_db),
):
    """Get status/result of a cleanup task."""

    validate_task_identifier(task_id)
    try:
        async_result = celery_app.AsyncResult(task_id)
        info = async_result.info or {}
        if not isinstance(info, dict):
            info = {"last_error": str(info) if info else None}

        if async_result.state == states.SUCCESS:
            task_status = info.get("status", "SUCCESS")
        elif async_result.state in (states.STARTED, states.RETRY, "PROGRESS"):
            task_status = "RUNNING"
        elif async_result.state == states.FAILURE:
            task_status = "FAILED"
        elif async_result.state == states.REVOKED:
            task_status = "CANCELLED"
        else:
            task_status = "PENDING"

        progress_payload = info.get("progress")
        progress = None
        if progress_payload:
            progress = CleanupProgress(**progress_payload)

        last_error = info.get("last_error")
        if async_result.state == states.FAILURE and not last_error:
            last_error = str(async_result.result)

        return CleanupTaskStatus(
            task_id=task_id,
            status=task_status,
            progress=progress,
            resources=info.get("resources"),
            summary=info.get("summary"),
            params=info.get("params"),
            dry_run=info.get("summary", {}).get("dry_run") if info else None,
            started_at=info.get("started_at"),
            completed_at=info.get("completed_at"),
            last_error=last_error if task_status in ("FAILED", "PARTIAL") else None,
        )
    except Exception as e:
        logger.error(f"Failed to fetch cleanup status {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
