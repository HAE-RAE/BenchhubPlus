"""Orchestrator service for managing evaluation workflows."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ...core.db import LeaderboardCache

from ...core.plan.planner import PlannerAgent, create_planner_agent
from ...core.schemas import (
    LeaderboardQuery,
    LeaderboardResponse,
    LeaderboardEntry,
    TaskResponse,
    ModelInfo,
    PlanConfig
)
from ...core.security import sanitize_model_name, validate_api_endpoint, mask_api_key
from ..repositories.leaderboard_repo import LeaderboardRepository
from ..repositories.tasks_repo import TasksRepository

logger = logging.getLogger(__name__)


class EvaluationOrchestrator:
    """Orchestrates evaluation workflows and manages cache."""
    
    def __init__(self, db: Session):
        self.db = db
        self.leaderboard_repo = LeaderboardRepository(db)
        self.tasks_repo = TasksRepository(db)
        self.planner_agent: Optional[PlannerAgent] = None
        
        # Initialize planner agent if possible
        try:
            self.planner_agent = create_planner_agent()
            logger.info("Planner agent initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize planner agent: {e}")
    
    def generate_leaderboard(self, query: LeaderboardQuery) -> TaskResponse:
        """Generate leaderboard for given query and models."""
        
        # Validate input
        self._validate_query(query)
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        try:
            plan_metadata: Optional[Dict[str, Any]] = None

            # Create evaluation plan using planner agent
            if self.planner_agent:
                plan_metadata = self.planner_agent.create_evaluation_plan(
                    query.query, query.models
                )
                plan_details = json.dumps(plan_metadata)
            else:
                # Fallback: create basic plan without LLM
                plan_details = self._create_fallback_plan(query)
            
            # Check cache first
            cached_results = self._check_cache(query, plan_metadata if self.planner_agent else None)
            
            if cached_results:
                # Return cached results immediately
                logger.info(f"Cache hit for query: {query.query}")
                
                # Create a "completed" task with cached results
                task = self.tasks_repo.create_task(task_id, plan_details)
                self.tasks_repo.update_task_status(
                    task_id, 
                    "SUCCESS", 
                    json.dumps(cached_results)
                )
                
                return TaskResponse(
                    task_id=task_id,
                    status="SUCCESS",
                    message="Results retrieved from cache"
                )
            
            # Cache miss - create evaluation task
            task = self.tasks_repo.create_task(task_id, plan_details)

            try:
                from ...worker.tasks import run_evaluation

                async_result = run_evaluation.delay(task_id, plan_details)
                logger.info(
                    "Dispatched evaluation task %s to worker (celery id=%s)",
                    task_id,
                    getattr(async_result, "id", "unknown")
                )
            except Exception as dispatch_error:
                logger.error(
                    "Failed to dispatch evaluation task %s: %s",
                    task_id,
                    dispatch_error
                )
                self.tasks_repo.update_task_status(
                    task_id,
                    "FAILURE",
                    error_message=str(dispatch_error)
                )
                raise RuntimeError("Failed to dispatch evaluation task") from dispatch_error

            return TaskResponse(
                task_id=task_id,
                status="PENDING",
                message="Evaluation task accepted for asynchronous processing"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate leaderboard: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of evaluation task."""
        task = self.tasks_repo.get_task(task_id)
        
        if not task:
            return None
        
        result = {
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
        
        return result
    
    def _validate_query(self, query: LeaderboardQuery) -> None:
        """Validate leaderboard query."""
        if not query.query.strip():
            raise ValueError("Query cannot be empty")
        
        if len(query.query) > 1000:
            raise ValueError("Query too long (max 1000 characters)")
        
        if not query.models:
            raise ValueError("At least one model must be provided")
        
        if len(query.models) > 10:
            raise ValueError("Maximum 10 models allowed per request")
        
        # Validate each model
        for model in query.models:
            if not validate_api_endpoint(model.api_base):
                raise ValueError(f"Invalid API endpoint: {model.api_base}")
            
            # Sanitize model name
            model.name = sanitize_model_name(model.name)
            
            logger.info(f"Validated model: {model.name} with API key: {mask_api_key(model.api_key)}")
    
    def _check_cache(
        self, 
        query: LeaderboardQuery, 
        plan_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Check if results are available in cache."""
        
        if not plan_metadata:
            return None
        
        try:
            config = PlanConfig(**plan_metadata["config"])
            
            # Check cache for each model
            cached_entries = []
            cache_hit_count = 0
            
            for model in query.models:
                cached_entry = self.leaderboard_repo.get_cached_entry(
                    model.name,
                    config.language,
                    config.subject_type,
                    config.task_type
                )
                
                if cached_entry:
                    cached_entries.append(LeaderboardEntry(
                        model_name=cached_entry.model_name,
                        language=cached_entry.language,
                        subject_type=cached_entry.subject_type,
                        task_type=cached_entry.task_type,
                        score=cached_entry.score,
                        last_updated=cached_entry.last_updated
                    ))
                    cache_hit_count += 1
            
            # Return cached results only if we have all models cached
            if cache_hit_count == len(query.models):
                return {
                    "entries": [entry.dict() for entry in cached_entries],
                    "query": query.query,
                    "generated_at": datetime.utcnow(),
                    "total_models": len(query.models),
                    "cache_hit": True
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            return None
    
    def _create_fallback_plan(self, query: LeaderboardQuery) -> str:
        """Create fallback plan when planner agent is not available."""
        
        # Simple fallback plan
        fallback_plan = {
            "query": query.query,
            "models": [model.dict() for model in query.models],
            "config": {
                "language": "English",  # Default
                "subject_type": "General",  # Default
                "task_type": "QA",  # Default
                "sample_size": 100
            },
            "fallback": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return json.dumps(fallback_plan)
    
    def get_leaderboard_by_criteria(
        self,
        language: Optional[str] = None,
        subject_type: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 100
    ) -> LeaderboardResponse:
        """Get leaderboard by specific criteria."""
        
        entries = self.leaderboard_repo.get_leaderboard(
            language=language,
            subject_type=subject_type,
            task_type=task_type,
            limit=limit
        )
        
        leaderboard_entries = [
            LeaderboardEntry(
                model_name=entry.model_name,
                language=entry.language,
                subject_type=entry.subject_type,
                task_type=entry.task_type,
                score=entry.score,
                last_updated=entry.last_updated
            )
            for entry in entries
        ]
        
        # Create query description
        query_parts = []
        if language:
            query_parts.append(f"language={language}")
        if subject_type:
            query_parts.append(f"subject={subject_type}")
        if task_type:
            query_parts.append(f"task={task_type}")
        
        query_description = " AND ".join(query_parts) if query_parts else "all categories"
        
        return LeaderboardResponse(
            entries=leaderboard_entries,
            query=query_description,
            generated_at=datetime.utcnow(),
            total_models=len(leaderboard_entries)
        )
    
    def update_cache_from_results(
        self,
        task_id: str,
        evaluation_results: List[Dict[str, Any]]
    ) -> None:
        """Update cache with evaluation results."""
        
        task = self.tasks_repo.get_task(task_id)
        if not task or not task.plan_details:
            logger.error(f"Task {task_id} not found or missing plan details")
            return
        
        try:
            plan_data = json.loads(task.plan_details)
            config = plan_data.get("config", {})
            
            language = config.get("language", "Unknown")
            subject_type = config.get("subject_type", "Unknown")
            task_type = config.get("task_type", "Unknown")
            
            # Update cache for each model result
            for result in evaluation_results:
                model_name = result.get("model_name")
                score = result.get("average_score", 0.0)
                
                if model_name and isinstance(score, (int, float)):
                    self.leaderboard_repo.upsert_entry(
                        model_name=model_name,
                        language=language,
                        subject_type=subject_type,
                        task_type=task_type,
                        score=float(score)
                    )
                    
                    logger.info(f"Updated cache for {model_name}: {score}")
            
        except Exception as e:
            logger.error(f"Failed to update cache from results: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""

        task_stats = self.tasks_repo.get_task_stats()

        # Get cache statistics
        from sqlalchemy import func
        cache_count = self.db.query(func.count(LeaderboardCache.model_name)).scalar()
        if cache_count is None:
            cache_count = 0

        return {
            "tasks": task_stats,
            "cache_entries": cache_count,
            "planner_available": self.planner_agent is not None,
            "timestamp": datetime.utcnow()
        }