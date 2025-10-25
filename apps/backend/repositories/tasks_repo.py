"""Repository for evaluation tasks operations."""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from ...core.db import EvaluationTask


class TasksRepository:
    """Repository for evaluation tasks operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(
        self,
        task_id: str,
        plan_details: Optional[str] = None
    ) -> EvaluationTask:
        """Create new evaluation task."""
        task = EvaluationTask(
            task_id=task_id,
            status="PENDING",
            plan_details=plan_details,
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
        error_message: Optional[str] = None
    ) -> Optional[EvaluationTask]:
        """Update task status and result."""
        task = self.get_task(task_id)
        
        if task:
            task.status = status
            if result:
                task.result = result
            if error_message:
                task.error_message = error_message
            
            if status in ["SUCCESS", "FAILURE"]:
                task.completed_at = datetime.utcnow()
            
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
            EvaluationTask.status.in_(["SUCCESS", "FAILURE"]),
            EvaluationTask.completed_at >= cutoff_time
        ).order_by(EvaluationTask.completed_at.desc()).limit(limit).all()
    
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
        from sqlalchemy import func
        
        stats = self.db.query(
            EvaluationTask.status,
            func.count(EvaluationTask.task_id).label('count')
        ).group_by(EvaluationTask.status).all()
        
        result = {
            'PENDING': 0,
            'STARTED': 0,
            'SUCCESS': 0,
            'FAILURE': 0
        }
        
        for stat in stats:
            result[stat.status] = stat.count
        
        # Add total
        result['TOTAL'] = sum(result.values())
        
        return result
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self.get_task(task_id)
        
        if task and task.status == "PENDING":
            task.status = "FAILURE"
            task.error_message = "Task cancelled by user"
            task.completed_at = datetime.utcnow()
            
            self.db.commit()
            return True
        
        return False