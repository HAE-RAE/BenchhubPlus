"""HRET integration API routes for BenchhubPlus."""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...core.db import get_db, EvaluationTask
from ...core.schemas import ModelInfo
from ...worker.celery_app import celery_app
from ...worker.hret_runner import HRETRunner, HRET_AVAILABLE
from ...worker.hret_config import HRETConfigManager
from ...worker.hret_storage import HRETStorageManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hret", tags=["HRET Integration"])


class HRETEvaluationRequest(BaseModel):
    """Request model for HRET evaluation."""
    
    plan_yaml: str = Field(..., description="YAML plan configuration")
    models: List[ModelInfo] = Field(..., description="List of models to evaluate")
    timeout_minutes: int = Field(default=30, description="Evaluation timeout in minutes")
    store_results: bool = Field(default=True, description="Whether to store results in database")


class HRETEvaluationResponse(BaseModel):
    """Response model for HRET evaluation."""
    
    task_id: str = Field(..., description="Evaluation task ID")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")


class HRETStatusResponse(BaseModel):
    """Response model for HRET evaluation status."""
    
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    progress: Optional[Dict[str, Any]] = Field(None, description="Progress information")
    result: Optional[Dict[str, Any]] = Field(None, description="Evaluation result")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Task creation time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")


class HRETConfigResponse(BaseModel):
    """Response model for HRET configuration."""
    
    supported_datasets: List[str] = Field(..., description="Supported datasets")
    supported_models: List[str] = Field(..., description="Supported model backends")
    supported_evaluation_methods: List[str] = Field(..., description="Supported evaluation methods")
    example_plan: str = Field(..., description="Example plan YAML")


@router.get("/status", response_model=Dict[str, Any])
async def get_hret_status():
    """Get HRET integration status."""
    
    return {
        "hret_available": HRET_AVAILABLE,
        "version": "1.0.0",
        "integration_status": "active" if HRET_AVAILABLE else "unavailable",
        "supported_features": [
            "evaluation_execution",
            "result_mapping",
            "database_storage",
            "configuration_management"
        ] if HRET_AVAILABLE else []
    }


@router.get("/config", response_model=HRETConfigResponse)
async def get_hret_config():
    """Get HRET configuration information."""
    
    if not HRET_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="HRET is not available. Please install haerae-evaluation-toolkit."
        )
    
    try:
        config_manager = HRETConfigManager()
        
        # Create example plan
        example_plan_path = config_manager.create_example_plan()
        with open(example_plan_path, "r", encoding="utf-8") as f:
            example_plan = f.read()
        
        return HRETConfigResponse(
            supported_datasets=config_manager.get_supported_datasets(),
            supported_models=config_manager.get_supported_models(),
            supported_evaluation_methods=config_manager.get_supported_evaluation_methods(),
            example_plan=example_plan
        )
        
    except Exception as e:
        logger.error(f"Failed to get HRET config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate", response_model=HRETEvaluationResponse)
async def start_hret_evaluation(
    request: HRETEvaluationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start HRET evaluation task."""
    
    if not HRET_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="HRET is not available. Please install haerae-evaluation-toolkit."
        )
    
    try:
        # Validate plan
        runner = HRETRunner()
        if not runner.validate_plan(request.plan_yaml):
            raise HTTPException(
                status_code=400,
                detail="Invalid plan configuration"
            )
        
        # Create evaluation task
        task_id = f"hret_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(request.plan_yaml) % 10000:04d}"
        
        # Store task in database
        db_task = EvaluationTask(
            task_id=task_id,
            status="PENDING",
            plan_details=json.dumps({
                "plan_yaml": request.plan_yaml,
                "models": [model.dict() for model in request.models],
                "timeout_minutes": request.timeout_minutes,
                "store_results": request.store_results
            })
        )
        db.add(db_task)
        db.commit()
        
        # Start background task
        background_tasks.add_task(
            run_hret_evaluation_task,
            task_id=task_id,
            plan_yaml=request.plan_yaml,
            models=[model.dict() for model in request.models],
            timeout_minutes=request.timeout_minutes,
            store_results=request.store_results
        )
        
        # Estimate duration based on number of models and samples
        estimated_duration = len(request.models) * 5  # 5 minutes per model estimate
        
        return HRETEvaluationResponse(
            task_id=task_id,
            status="PENDING",
            message="HRET evaluation task started successfully",
            estimated_duration=estimated_duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start HRET evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluate/{task_id}", response_model=HRETStatusResponse)
async def get_hret_evaluation_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get HRET evaluation task status."""
    
    try:
        # Get task from database
        task = db.query(EvaluationTask).filter(EvaluationTask.task_id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Parse result if available
        result = None
        if task.result:
            try:
                result = json.loads(task.result)
            except json.JSONDecodeError:
                result = {"raw_result": task.result}
        
        return HRETStatusResponse(
            task_id=task.task_id,
            status=task.status,
            progress=None,  # TODO: Implement progress tracking
            result=result,
            error=task.error_message,
            created_at=task.created_at,
            completed_at=task.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PlanValidationRequest(BaseModel):
    """Request model for plan validation."""
    plan_yaml: str = Field(..., description="YAML plan to validate")


@router.post("/validate-plan")
async def validate_hret_plan(request: PlanValidationRequest):
    """Validate HRET plan configuration."""
    
    if not HRET_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="HRET is not available. Please install haerae-evaluation-toolkit."
        )
    
    try:
        runner = HRETRunner()
        is_valid = runner.validate_plan(request.plan_yaml)
        
        return {
            "valid": is_valid,
            "message": "Plan is valid" if is_valid else "Plan validation failed"
        }
        
    except Exception as e:
        logger.error(f"Plan validation error: {e}")
        return {
            "valid": False,
            "message": f"Validation error: {str(e)}"
        }


@router.get("/results")
async def get_hret_results(
    model_name: Optional[str] = None,
    dataset_name: Optional[str] = None,
    limit: int = 100
):
    """Get HRET evaluation results."""
    
    try:
        storage_manager = HRETStorageManager()
        results = storage_manager.get_evaluation_results(
            model_name=model_name,
            dataset_name=dataset_name,
            limit=limit
        )
        
        return {
            "results": results,
            "count": len(results),
            "filters": {
                "model_name": model_name,
                "dataset_name": dataset_name,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get HRET results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard")
async def get_hret_leaderboard(
    language: Optional[str] = None,
    subject_type: Optional[str] = None,
    task_type: Optional[str] = None
):
    """Get HRET-based leaderboard data."""
    
    try:
        storage_manager = HRETStorageManager()
        leaderboard_data = storage_manager.get_leaderboard_data(
            language=language,
            subject_type=subject_type,
            task_type=task_type
        )
        
        return {
            "leaderboard": leaderboard_data,
            "count": len(leaderboard_data),
            "filters": {
                "language": language,
                "subject_type": subject_type,
                "task_type": task_type
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get HRET leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_hret_evaluation_task(
    task_id: str,
    plan_yaml: str,
    models: List[Dict[str, Any]],
    timeout_minutes: int,
    store_results: bool
):
    """Background task to run HRET evaluation."""
    
    db = None
    try:
        # Get database session
        from ...core.db import SessionLocal
        db = SessionLocal()
        
        # Update task status to STARTED
        task = db.query(EvaluationTask).filter(EvaluationTask.task_id == task_id).first()
        if task:
            task.status = "STARTED"
            db.commit()
        
        # Run HRET evaluation
        runner = HRETRunner()
        timeout_seconds = timeout_minutes * 60
        
        results = runner.run_evaluation(
            plan_yaml=plan_yaml,
            models=models,
            timeout=timeout_seconds
        )
        
        # Store results if requested
        if store_results:
            storage_manager = HRETStorageManager()
            
            # Convert results to storage format
            from ...worker.hret_mapper import HRETResultMapper
            mapper = HRETResultMapper()
            
            # This is a simplified version - in practice, you'd need to properly
            # extract HRET results and convert them
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
            task.completed_at = datetime.utcnow()
            db.commit()
        
        logger.info(f"HRET evaluation task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"HRET evaluation task {task_id} failed: {e}")
        
        # Update task status to FAILURE
        if db and task:
            task.status = "FAILURE"
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            db.commit()
    
    finally:
        if db:
            db.close()