"""Celery tasks for BenchHub Plus."""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from celery import current_task
from sqlalchemy.orm import Session

from .celery_app import celery_app
from .hret_runner import create_hret_runner
from .hret_storage import HRETStorageManager
from .hret_mapper import HRETResultMapper
from ..core.credential_service import CredentialService
from ..core.db import SessionLocal, ExperimentSample, EvaluationTask
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
        credential_service = CredentialService(db)
        models = credential_service.hydrate_models(plan_data.get("models", []))
        
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


@celery_app.task(bind=True, name="apps.worker.tasks.run_hret_evaluation")
def run_hret_evaluation(
    self, 
    task_id: str, 
    plan_yaml: str, 
    models: List[Dict[str, Any]], 
    timeout_minutes: int = 30,
    store_results: bool = True
) -> Dict[str, Any]:
    """Run HRET evaluation task with proper result mapping and storage."""
    
    logger.info(f"Starting HRET evaluation task {task_id}")
    
    db = SessionLocal()
    
    try:
        # Update task status to STARTED
        task = db.query(EvaluationTask).filter(EvaluationTask.task_id == task_id).first()
        if task:
            task.status = "STARTED"
            db.commit()
        
        # Update progress
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": len(models), "status": "Initializing HRET runner"}
        )
        
        # Create HRET runner
        hret_runner = create_hret_runner()
        
        # Validate plan
        if not hret_runner.validate_plan(plan_yaml):
            raise ValueError("Invalid HRET plan configuration")
        
        # Update progress
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 1, "total": len(models), "status": "Running HRET evaluation"}
        )
        
        # Run HRET evaluation
        timeout_seconds = timeout_minutes * 60
        results = hret_runner.run_evaluation(plan_yaml, models, timeout_seconds)
        
        # Update progress
        current_task.update_state(
            state="PROGRESS",
            meta={"current": len(models), "total": len(models), "status": "Processing and storing results"}
        )
        
        # Store results if requested
        storage_stats = None
        if store_results:
            storage_manager = HRETStorageManager()
            
            # Note: In a real implementation, you would extract actual HRET results
            # and convert them using the mapper. For now, we'll use the existing
            # results structure from the runner.
            
            # Create mock model results and sample results for storage
            # This would be replaced with actual HRET result mapping
            model_results = []
            sample_results = []
            
            # Store in database
            storage_stats = storage_manager.store_evaluation_results(
                model_results=model_results,
                sample_results=sample_results,
                task_id=task_id
            )
            
            results["storage_stats"] = storage_stats
        
        # Update task status to SUCCESS
        if task:
            task.status = "SUCCESS"
            task.result = json.dumps(results)
            task.completed_at = db.func.now()
            db.commit()
        
        logger.info(f"HRET evaluation task {task_id} completed successfully")
        
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "results": results,
            "storage_stats": storage_stats
        }
        
    except Exception as e:
        logger.error(f"HRET evaluation task {task_id} failed: {e}")
        
        # Update task status to FAILURE
        if task:
            task.status = "FAILURE"
            task.error_message = str(e)
            task.completed_at = db.func.now()
            db.commit()
        
        # Re-raise exception for Celery
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, name="apps.worker.tasks.cleanup_task")
def cleanup_task(
    self,
    days_old: int = 7,
    resources: Optional[List[str]] = None,
    dry_run: bool = False,
    limit: int = 500,
    hard_delete: bool = False
) -> Dict[str, Any]:
    """Clean up old tasks, samples, and cache entries."""
    
    db = SessionLocal()
    valid_resources = {"tasks", "samples", "cache"}
    selected_resources = resources or ["tasks", "samples", "cache"]
    selected_resources = [res for res in selected_resources if res in valid_resources]
    
    if not selected_resources:
        raise ValueError("No valid resources provided for cleanup")

    logger.info(
        "Starting cleanup task resources=%s days_old=%s dry_run=%s limit=%s hard_delete=%s",
        selected_resources,
        days_old,
        dry_run,
        limit,
        hard_delete,
    )

    repo = TasksRepository(db)
    resource_results: Dict[str, Dict[str, Any]] = {}
    start_time = time.time()
    started_at_dt = datetime.utcnow()
    total_steps = len(selected_resources)
    progress_state = {
        "current": 0,
        "total": total_steps,
        "stage": "initializing",
        "eta_seconds": None
    }

    def _update_progress(stage: str, current: int) -> None:
        progress_state["current"] = current
        progress_state["stage"] = stage
        elapsed = time.time() - start_time
        if current > 0:
            remaining_steps = max(total_steps - current, 0)
            avg = elapsed / current
            progress_state["eta_seconds"] = int(avg * remaining_steps)
        meta = {
            "status": "RUNNING",
            "progress": progress_state.copy(),
            "resources": resource_results,
            "params": {
                "days_old": days_old,
                "resources": selected_resources,
                "dry_run": dry_run,
                "limit": limit,
                "hard_delete": hard_delete,
            },
        }
        try:
            self.update_state(state="PROGRESS", meta=meta)
        except Exception:
            # If updating state fails, continue cleanup.
            logger.debug("Progress update failed", exc_info=True)

    _update_progress("initializing", 0)

    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days_old)

        # Clean tasks
        if "tasks" in selected_resources:
            started_at = time.time()
            errors: List[str] = []
            try:
                cleaned_tasks = repo.cleanup_old_tasks(
                    days_old=days_old,
                    limit=limit,
                    dry_run=dry_run
                )
                resource_results["tasks"] = {
                    "deleted": cleaned_tasks,
                    "skipped": 0,
                    "errors": errors,
                    "duration_ms": int((time.time() - started_at) * 1000),
                }
            except Exception as task_error:
                logger.error("Task cleanup failed: %s", task_error)
                errors.append(str(task_error))
                resource_results["tasks"] = {
                    "deleted": 0,
                    "skipped": 0,
                    "errors": errors,
                    "duration_ms": int((time.time() - started_at) * 1000),
                }
            _update_progress("tasks", progress_state["current"] + 1)

        # Clean experiment samples
        if "samples" in selected_resources:
            started_at = time.time()
            errors = []
            try:
                samples_query = db.query(ExperimentSample).filter(
                    ExperimentSample.timestamp < cutoff_time
                )
                deleted_samples = 0
                if limit:
                    sample_ids = [
                        row.id
                        for row in samples_query.with_entities(ExperimentSample.id).limit(limit).all()
                    ]
                    deleted_samples = len(sample_ids)
                    if not dry_run and sample_ids:
                        (
                            db.query(ExperimentSample)
                            .filter(ExperimentSample.id.in_(sample_ids))
                            .delete(synchronize_session=False)
                        )
                else:
                    deleted_samples = samples_query.count()
                    if not dry_run and deleted_samples:
                        samples_query.delete(synchronize_session=False)

                if not dry_run:
                    db.commit()

                resource_results["samples"] = {
                    "deleted": deleted_samples,
                    "skipped": 0,
                    "errors": errors,
                    "duration_ms": int((time.time() - started_at) * 1000),
                }
            except Exception as sample_error:
                logger.error("Sample cleanup failed: %s", sample_error)
                db.rollback()
                errors.append(str(sample_error))
                resource_results["samples"] = {
                    "deleted": 0,
                    "skipped": 0,
                    "errors": errors,
                    "duration_ms": int((time.time() - started_at) * 1000),
                }
            _update_progress("samples", progress_state["current"] + 1)

        # Clean leaderboard cache
        if "cache" in selected_resources:
            started_at = time.time()
            errors = []
            try:
                cache_query = db.query(LeaderboardCache).filter(
                    LeaderboardCache.last_updated < cutoff_time
                )
                deleted_cache = 0
                if limit:
                    cache_rows = cache_query.limit(limit).all()
                    deleted_cache = len(cache_rows)
                else:
                    cache_rows = cache_query.all()
                    deleted_cache = len(cache_rows)

                if not dry_run and cache_rows:
                    if hard_delete:
                        ids = [row.id for row in cache_rows]
                        (
                            db.query(LeaderboardCache)
                            .filter(LeaderboardCache.id.in_(ids))
                            .delete(synchronize_session=False)
                        )
                    else:
                        now_ts = datetime.utcnow()
                        for row in cache_rows:
                            row.quarantined = True
                            row.deleted_at = now_ts
                    db.commit()

                resource_results["cache"] = {
                    "deleted": deleted_cache,
                    "skipped": 0,
                    "errors": errors,
                    "duration_ms": int((time.time() - started_at) * 1000),
                }
            except Exception as cache_error:
                logger.error("Cache cleanup failed: %s", cache_error)
                db.rollback()
                errors.append(str(cache_error))
                resource_results["cache"] = {
                    "deleted": 0,
                    "skipped": 0,
                    "errors": errors,
                    "duration_ms": int((time.time() - started_at) * 1000),
                }
            _update_progress("cache", progress_state["current"] + 1)

        elapsed_ms = int((time.time() - start_time) * 1000)
        has_errors = any(res.get("errors") for res in resource_results.values())
        total_deleted = sum(res.get("deleted", 0) for res in resource_results.values())
        status = "PARTIAL" if has_errors and total_deleted > 0 else "FAILED" if has_errors else "SUCCESS"
        first_error = None
        if has_errors:
            for res in resource_results.values():
                if res.get("errors"):
                    first_error = res["errors"][0]
                    break

        final_progress = {
            "current": total_steps,
            "total": total_steps,
            "stage": "completed",
            "eta_seconds": 0,
        }
        summary = {
            "deleted_total": total_deleted,
            "errors_total": sum(len(res.get("errors", [])) for res in resource_results.values()),
            "duration_ms": elapsed_ms,
            "dry_run": dry_run,
        }

        result_payload = {
            "status": status,
            "progress": final_progress,
            "resources": resource_results,
            "summary": summary,
            "params": {
                "days_old": days_old,
                "resources": selected_resources,
                "dry_run": dry_run,
                "limit": limit,
                "hard_delete": hard_delete,
            },
            "started_at": started_at_dt.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "last_error": first_error,
        }

        _update_progress("completed", total_steps)
        logger.info("Cleanup completed status=%s summary=%s", status, summary)
        return result_payload

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
