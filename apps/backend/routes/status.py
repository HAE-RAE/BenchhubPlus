"""Status and health check API routes."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from ...core.db import get_db
from ...core.schemas import TaskStatus, HealthResponse
from ..repositories.tasks_repo import TasksRepository
from ..services.orchestrator import EvaluationOrchestrator
from ...worker.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["status"])


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


@router.get("/tasks")
async def list_tasks(
    status: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List evaluation tasks with optional status filter."""
    
    try:
        repo = TasksRepository(db)
        
        if status == "pending":
            tasks = repo.get_pending_tasks(limit)
        elif status == "running":
            tasks = repo.get_running_tasks(limit)
        elif status == "completed":
            tasks = repo.get_completed_tasks(limit)
        else:
            # Get recent tasks of all statuses
            all_tasks = []
            all_tasks.extend(repo.get_pending_tasks(limit // 3))
            all_tasks.extend(repo.get_running_tasks(limit // 3))
            all_tasks.extend(repo.get_completed_tasks(limit // 3))
            
            # Sort by creation time
            tasks = sorted(all_tasks, key=lambda x: x.created_at, reverse=True)[:limit]
        
        return {
            "tasks": [
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "created_at": task.created_at,
                    "completed_at": task.completed_at,
                    "has_error": bool(task.error_message)
                }
                for task in tasks
            ],
            "total": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str = Path(..., description="Task ID"),
    db: Session = Depends(get_db)
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