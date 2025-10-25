"""Celery tasks for BenchHub Plus."""

import json
import logging
from typing import Any, Dict, List

from celery import current_task
from sqlalchemy.orm import Session

from .celery_app import celery_app
from .hret_runner import create_hret_runner
from ..core.db import SessionLocal, ExperimentSample
from ..backend.repositories.tasks_repo import TasksRepository
from ..backend.services.orchestrator import EvaluationOrchestrator

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="apps.worker.tasks.run_evaluation")
def run_evaluation(self, task_id: str, plan_details: str) -> Dict[str, Any]:
    """Run model evaluation task."""
    
    logger.info(f"Starting evaluation task {task_id}")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Update task status to STARTED
        repo = TasksRepository(db)
        repo.update_task_status(task_id, "STARTED")
        
        # Parse plan details
        plan_data = json.loads(plan_details)
        plan_yaml = plan_data.get("plan_yaml", "")
        models = plan_data.get("models", [])
        
        if not plan_yaml or not models:
            raise ValueError("Invalid plan data: missing plan_yaml or models")
        
        # Update task progress
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": len(models), "status": "Initializing HRET runner"}
        )
        
        # Create HRET runner and execute evaluation
        hret_runner = create_hret_runner()
        
        # Validate plan
        if not hret_runner.validate_plan(plan_yaml):
            raise ValueError("Invalid HRET plan configuration")
        
        # Update progress
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 1, "total": len(models), "status": "Running evaluation"}
        )
        
        # Run evaluation
        results = hret_runner.run_evaluation(plan_yaml, models)
        
        # Update progress
        current_task.update_state(
            state="PROGRESS",
            meta={"current": len(models), "total": len(models), "status": "Processing results"}
        )
        
        # Store sample-level results in database
        _store_sample_results(db, results, plan_data)
        
        # Update leaderboard cache
        orchestrator = EvaluationOrchestrator(db)
        orchestrator.update_cache_from_results(task_id, results["model_results"])
        
        # Update task status to SUCCESS
        repo.update_task_status(task_id, "SUCCESS", json.dumps(results))
        
        logger.info(f"Evaluation task {task_id} completed successfully")
        
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Evaluation task {task_id} failed: {e}")
        
        # Update task status to FAILURE
        repo = TasksRepository(db)
        repo.update_task_status(task_id, "FAILURE", error_message=str(e))
        
        # Re-raise exception for Celery
        raise
        
    finally:
        db.close()


@celery_app.task(name="apps.worker.tasks.cleanup_task")
def cleanup_task(days_old: int = 7) -> Dict[str, Any]:
    """Clean up old tasks and data."""
    
    logger.info(f"Starting cleanup task for data older than {days_old} days")
    
    db = SessionLocal()
    
    try:
        repo = TasksRepository(db)
        cleaned_tasks = repo.cleanup_old_tasks(days_old)
        
        # TODO: Add cleanup for other data types if needed
        # - Old experiment samples
        # - Expired cache entries
        # - Temporary files
        
        logger.info(f"Cleanup completed: {cleaned_tasks} tasks cleaned")
        
        return {
            "status": "SUCCESS",
            "cleaned_tasks": cleaned_tasks,
            "days_old": days_old
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise
        
    finally:
        db.close()


def _store_sample_results(
    db: Session,
    results: Dict[str, Any],
    plan_data: Dict[str, Any]
) -> None:
    """Store sample-level results in database."""
    
    try:
        config = plan_data.get("config", {})
        
        # For each model result, we need to generate and store sample data
        # In a real implementation, this would come from HRET output
        # For now, we'll generate placeholder sample data
        
        for model_result in results["model_results"]:
            model_name = model_result["model_name"]
            total_samples = model_result["total_samples"]
            average_score = model_result["average_score"]
            
            # Generate sample-level data (placeholder)
            import random
            random.seed(42)  # For reproducible results
            
            for i in range(min(total_samples, 100)):  # Limit to 100 samples for demo
                # Generate a score around the average with some variance
                score = max(0.0, min(1.0, random.gauss(average_score, 0.1)))
                
                sample = ExperimentSample(
                    prompt=f"Sample prompt {i+1} for evaluation",
                    answer=f"Generated answer from {model_name}",
                    skill_label=config.get("task_type", "QA"),
                    target_label=config.get("language", "English"),
                    subject_label=config.get("subject_type", "General"),
                    format_label="text",
                    dataset_name="benchhub_evaluation",
                    meta_data=json.dumps({
                        "model_name": model_name,
                        "sample_index": i,
                        "task_id": plan_data.get("task_id"),
                        "evaluation_type": "simulated"
                    }),
                    correctness=score
                )
                
                db.add(sample)
        
        db.commit()
        logger.info("Sample results stored in database")
        
    except Exception as e:
        logger.error(f"Failed to store sample results: {e}")
        db.rollback()
        raise


# Task for testing Celery connectivity
@celery_app.task(name="apps.worker.tasks.test_task")
def test_task(message: str = "Hello from Celery!") -> Dict[str, Any]:
    """Test task to verify Celery is working."""
    
    logger.info(f"Test task executed with message: {message}")
    
    return {
        "status": "SUCCESS",
        "message": message,
        "worker_id": current_task.request.id
    }


# Periodic task for maintenance (if using celery-beat)
@celery_app.task(name="apps.worker.tasks.periodic_cleanup")
def periodic_cleanup() -> Dict[str, Any]:
    """Periodic cleanup task."""
    
    logger.info("Running periodic cleanup")
    
    # Run cleanup for data older than 7 days
    result = cleanup_task.delay(7)
    
    return {
        "status": "SCHEDULED",
        "cleanup_task_id": result.id
    }