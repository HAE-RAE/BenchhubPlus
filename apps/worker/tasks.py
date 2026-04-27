"""Celery tasks for BenchHub Plus."""

import json
import logging
import re
import time
from contextlib import contextmanager
from dataclasses import asdict
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

logger = logging.getLogger(__name__)


# Loggers that HRET / llm_eval emit progress messages on. Attach a single
# handler to each so we can translate noisy library logs into structured
# Celery PROGRESS updates the SPA can render.
_HRET_PROGRESS_LOGGERS = (
    "runner",
    "openai_backend",
    "string_match",
    "benchhub_dataset",
    "llm_eval.evaluator",
)


class _HretProgressHandler(logging.Handler):
    """Translate HRET log lines into Celery PROGRESS updates.

    HRET is a black-box pipeline with no progress callback. The cleanest
    way to surface meaningful per-sample progress to the UI is to listen
    to the library's own log messages and republish them as task state
    transitions.
    """

    _PATTERNS = (
        (
            re.compile(r"Total samples in '[^']+' split:\s*(\d+)"),
            "scanning",
            "Scanning dataset ({n:,} candidates)",
        ),
        (
            re.compile(r"Finished loading\. Total HRET formatted samples:\s*(\d+)"),
            "filtered",
            "Filtered to {n:,} matching samples",
        ),
        (
            re.compile(r"Applied sample_size=\d+\. Final sample count:\s*(\d+)"),
            "ready",
            "Selected {n} samples for evaluation",
        ),
        (
            re.compile(r"Starting batch generation for\s*(\d+) items"),
            "inferring",
            "Generating model outputs (0/{n})",
        ),
        (
            re.compile(r"Batch generation completed"),
            "inferred",
            "Generation complete",
        ),
        (
            re.compile(r"Inference completed for\s*(\d+) items"),
            "inferred",
            "Generation complete ({n}/{n})",
        ),
        (
            re.compile(r"Starting evaluation with '([^']+)'"),
            "scoring",
            "Scoring outputs",
        ),
        (
            re.compile(r"Pipeline run completed in\s*([\d.]+)\s*seconds"),
            "scored",
            "Evaluation pipeline complete",
        ),
    )

    def __init__(self, total_samples: int) -> None:
        super().__init__(level=logging.INFO)
        self.total_samples = max(int(total_samples or 0), 0)
        self.current = 0
        self.stage_key = "starting"
        self._last_status: Optional[str] = None

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            message = record.getMessage()
        except Exception:
            return

        for pattern, key, template in self._PATTERNS:
            match = pattern.search(message)
            if not match:
                continue

            value = int(match.group(1)) if match.groups() and match.group(1).isdigit() else None
            status = template.format(n=value) if value is not None else template

            if key == "ready" and value:
                self.total_samples = value
                self.current = 0
            elif key == "inferred" and self.total_samples:
                self.current = self.total_samples
            elif key == "scored" and self.total_samples:
                self.current = self.total_samples

            self.stage_key = key
            self._publish(status)
            return

    def _publish(self, status: str) -> None:
        if status == self._last_status:
            return
        self._last_status = status
        try:
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": self.current,
                    "total": max(self.total_samples, 1),
                    "status": status,
                },
            )
        except Exception:
            pass


@contextmanager
def _hret_progress_capture(total_samples: int):
    """Attach the progress handler to HRET loggers for the duration of the task."""
    handler = _HretProgressHandler(total_samples)
    attached: List[logging.Logger] = []
    for name in _HRET_PROGRESS_LOGGERS:
        log = logging.getLogger(name)
        log.addHandler(handler)
        attached.append(log)
    try:
        yield handler
    finally:
        for log in attached:
            try:
                log.removeHandler(handler)
            except Exception:
                pass


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
        # Commit so SQLite write lock is released before the long-running
        # evaluation phase; otherwise the storage manager (separate session)
        # would block on an open transaction held by this session.
        db.commit()
        
        if not plan_yaml or not models:
            raise ValueError("Invalid plan data: missing plan_yaml or models")

        sample_size = 0
        try:
            sample_size = int(plan_data.get("config", {}).get("sample_size", 0))
        except (TypeError, ValueError):
            sample_size = 0
        progress_total = max(sample_size, 1)

        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": progress_total, "status": "Initializing evaluation runner"},
        )
        
        # Create HRET runner and execute evaluation
        hret_runner = create_hret_runner()
        
        # Validate plan
        if not hret_runner.validate_plan(plan_yaml):
            raise ValueError("Invalid HRET plan configuration")
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": progress_total, "status": "Loading dataset"},
        )

        # Run evaluation. The progress capture context attaches a logging
        # handler to HRET's internal loggers so per-sample milestones are
        # republished to Celery state for the SPA.
        with _hret_progress_capture(sample_size):
            results, raw_results = hret_runner.run_evaluation(plan_yaml, models)

        current_task.update_state(
            state="PROGRESS",
            meta={
                "current": progress_total,
                "total": progress_total,
                "status": "Processing results",
            },
        )
        
        mapper = HRETResultMapper()
        mapped_model_results = []
        mapped_sample_results = []

        for raw_result in raw_results:
            try:
                model_result, sample_results = mapper.map_hret_result_to_benchhub(
                    raw_result["evaluation_result"],
                    raw_result["model_info"],
                    raw_result["dataset_info"],
                    raw_result.get("execution_time", 0.0),
                )
                mapped_model_results.append(model_result)
                mapped_sample_results.extend(sample_results)
            except Exception as map_error:
                logger.error(f"Failed to map HRET result for {raw_result.get('model_info', {}).get('name')}: {map_error}")

        storage_stats = None
        if mapped_model_results or mapped_sample_results:
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": progress_total,
                    "total": progress_total,
                    "status": f"Storing {len(mapped_sample_results)} samples",
                },
            )
            storage_manager = HRETStorageManager()
            storage_stats = storage_manager.store_evaluation_results(
                model_results=mapped_model_results,
                sample_results=mapped_sample_results,
                task_id=task_id,
            )

        if mapped_model_results:
            results["model_results"] = [asdict(model_result) for model_result in mapped_model_results]
        results["storage_stats"] = storage_stats
        
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
        
        n_models = len(models)
        # Steps: init(0), validate(1), run_per_model(2..n+1), process(n+2), store(n+3)
        total_steps = n_models + 4

        def _progress(step: int, status_msg: str) -> None:
            current_task.update_state(
                state="PROGRESS",
                meta={"current": step, "total": total_steps, "status": status_msg},
            )

        _progress(0, "Initializing evaluation runner")

        # Create HRET runner
        hret_runner = create_hret_runner()

        _progress(1, "Validating evaluation plan")

        # Validate plan
        if not hret_runner.validate_plan(plan_yaml):
            raise ValueError("Invalid HRET plan configuration")

        model_names = [m.get("name", f"Model {i+1}") for i, m in enumerate(models)]
        _progress(2, f"Running benchmark — {', '.join(model_names)}")

        # Run HRET evaluation
        timeout_seconds = timeout_minutes * 60
        results, raw_results = hret_runner.run_evaluation(plan_yaml, models, timeout_seconds)

        _progress(n_models + 2, "Mapping evaluation results")
        
        storage_stats = None
        if store_results:
            mapper = HRETResultMapper()
            mapped_model_results = []
            mapped_sample_results = []

            for raw_result in raw_results:
                try:
                    model_result, sample_results = mapper.map_hret_result_to_benchhub(
                        raw_result["evaluation_result"],
                        raw_result["model_info"],
                        raw_result["dataset_info"],
                        raw_result.get("execution_time", 0.0),
                    )
                    mapped_model_results.append(model_result)
                    mapped_sample_results.extend(sample_results)
                except Exception as map_error:
                    logger.error(
                        "Failed to map HRET result for %s: %s",
                        raw_result.get("model_info", {}).get("name"),
                        map_error,
                    )

            if mapped_model_results or mapped_sample_results:
                _progress(n_models + 3, "Storing results to database")
                storage_manager = HRETStorageManager()
                storage_stats = storage_manager.store_evaluation_results(
                    model_results=mapped_model_results,
                    sample_results=mapped_sample_results,
                    task_id=task_id,
                )

            if mapped_model_results:
                results["model_results"] = [asdict(model_result) for model_result in mapped_model_results]
            results["storage_stats"] = storage_stats
        
        # Update task status to SUCCESS
        if task:
            task.status = "SUCCESS"
            task.result = json.dumps(results)
            task.completed_at = datetime.utcnow()
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
            task.completed_at = datetime.utcnow()
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
