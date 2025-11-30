"""Repository for evaluation tasks operations."""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from ...core.db import EvaluationTask


class TasksRepository:
    """Repository for evaluation tasks operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(
        self,
        task_id: str,
        plan_details: Optional[str] = None,
        user_id: Optional[int] = None,
        request_payload: Optional[str] = None,
        model_count: Optional[int] = None,
        policy_tags: Optional[str] = None,
    ) -> EvaluationTask:
        """Create new evaluation task."""
        task = EvaluationTask(
            task_id=task_id,
            status="PENDING",
            plan_details=plan_details,
            request_payload=request_payload,
            model_count=model_count,
            policy_tags=policy_tags,
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def get_task(self, task_id: str) -> Optional[EvaluationTask]:
        """Get task by ID."""
        return self.db.query(EvaluationTask).filter(
            EvaluationTask.task_id == task_id
        ).first()
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        policy_tags: Optional[str] = None,
        error_log: Optional[str] = None,
    ) -> Optional[EvaluationTask]:
        """Update task status and result."""
        task = self.get_task(task_id)
        
        if task:
            task.status = status
            if result:
                task.result = result
            if error_message:
                task.error_message = error_message
            if policy_tags is not None:
                task.policy_tags = policy_tags
            if error_log is not None:
                task.error_log = error_log
            
            if status in ["SUCCESS", "FAILURE"]:
                task.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(task)
        
        return task

    def update_policy_tags(self, task_id: str, policy_tags: str) -> Optional[EvaluationTask]:
        """Update policy tags for a task."""
        task = self.get_task(task_id)
        if not task:
            return None
        task.policy_tags = policy_tags
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_pending_tasks(self, limit: int = 100) -> List[EvaluationTask]:
        """Get pending tasks."""
        return self.db.query(EvaluationTask).filter(
            EvaluationTask.status == "PENDING"
        ).order_by(EvaluationTask.created_at).limit(limit).all()
    
    def get_running_tasks(self, limit: int = 100) -> List[EvaluationTask]:
        """Get running tasks."""
        return self.db.query(EvaluationTask).filter(
            EvaluationTask.status == "STARTED"
        ).order_by(EvaluationTask.created_at).limit(limit).all()
    
    def get_completed_tasks(
        self,
        limit: int = 100,
        hours_back: int = 24
    ) -> List[EvaluationTask]:
        """Get completed tasks within time window."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        return self.db.query(EvaluationTask).filter(
            EvaluationTask.status.in_(["SUCCESS", "FAILURE", "CANCELLED"]),
            EvaluationTask.completed_at >= cutoff_time
        ).order_by(EvaluationTask.completed_at.desc()).limit(limit).all()

    def get_recent_tasks(self, limit: int = 50) -> List[EvaluationTask]:
        """Get most recent tasks regardless of status."""
        return (
            self.db.query(EvaluationTask)
            .order_by(EvaluationTask.created_at.desc())
            .limit(limit)
            .all()
        )
    
    def cleanup_old_tasks(self, days_old: int = 7) -> int:
        """Clean up old completed tasks."""
        cutoff_time = datetime.utcnow() - timedelta(days=days_old)
        
        count = self.db.query(EvaluationTask).filter(
            EvaluationTask.status.in_(["SUCCESS", "FAILURE"]),
            EvaluationTask.completed_at < cutoff_time
        ).count()
        
        self.db.query(EvaluationTask).filter(
            EvaluationTask.status.in_(["SUCCESS", "FAILURE"]),
            EvaluationTask.completed_at < cutoff_time
        ).delete()
        
        self.db.commit()
        return count
    
    def get_task_stats(self) -> dict:
        """Get task statistics."""
        stats = self.db.query(
            EvaluationTask.status,
            func.count(EvaluationTask.task_id).label('count')
        ).group_by(EvaluationTask.status).all()
        
        result = {
            'PENDING': 0,
            'STARTED': 0,
            'SUCCESS': 0,
            'FAILURE': 0,
            'CANCELLED': 0,
            'HOLD': 0
        }
        
        for stat in stats:
            result[stat.status] = stat.count
        
        # Add total
        result['TOTAL'] = sum(result.values())
        
        return result
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self.get_task(task_id)
        
        if task and task.status in ["PENDING", "HOLD", "STARTED"]:
            task.status = "CANCELLED"
            task.error_message = "Task cancelled by user"
            task.completed_at = datetime.utcnow()
            
            self.db.commit()
            return True
        
        return False

    def filter_tasks(
        self,
        statuses: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_models: Optional[int] = None,
        max_models: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[EvaluationTask], int]:
        """Filter tasks with pagination."""
        query = self.db.query(EvaluationTask)

        if statuses:
            query = query.filter(EvaluationTask.status.in_(statuses))
        if user_id:
            query = query.filter(EvaluationTask.user_id == user_id)
        if start_date:
            query = query.filter(EvaluationTask.created_at >= start_date)
        if end_date:
            query = query.filter(EvaluationTask.created_at <= end_date)
        if min_models is not None:
            query = query.filter(EvaluationTask.model_count >= min_models)
        if max_models is not None:
            query = query.filter(EvaluationTask.model_count <= max_models)

        total = query.count()
        items = (
            query.order_by(EvaluationTask.created_at.desc())
            .offset(max(0, (page - 1) * page_size))
            .limit(page_size)
            .all()
        )
        return items, total

    def get_task_details(self, task_id: str) -> Optional[EvaluationTask]:
        """Return full details for a task."""
        return self.db.query(EvaluationTask).filter(EvaluationTask.task_id == task_id).first()
