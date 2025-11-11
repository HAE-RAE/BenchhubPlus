"""Orchestrator service for managing evaluation workflows."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ...core.credential_service import CredentialService, StoredCredential
from ...core.db import LeaderboardCache

from ...core.plan.planner import PlannerAgent, create_planner_agent
from ...core.schemas import (
    LeaderboardQuery,
    LeaderboardResponse,
    LeaderboardEntry,
    LeaderboardSuggestionResponse,
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
        self.credential_service = CredentialService(db)
        
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
            stored_credentials = self.credential_service.register_models(query.models)

            secure_models = self._build_secure_models(query.models, stored_credentials)

            # Create evaluation plan using planner agent
            if self.planner_agent:
                plan_metadata = self.planner_agent.create_evaluation_plan(
                    query.query, secure_models
                )
                plan_metadata = self._attach_credential_references(
                    plan_metadata,
                    stored_credentials
                )
                plan_details = json.dumps(plan_metadata)
            else:
                # Fallback: create basic plan without LLM
                plan_details = self._create_fallback_plan(
                    query,
                    secure_models,
                    stored_credentials
                )
            
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
                    json.dumps(cached_results, default=str)
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
            
            # Normalize subject_type from list to string (DB stores as string)
            subject_key = (
                "/".join(config.subject_type)
                if isinstance(config.subject_type, list)
                else str(config.subject_type)
            )
            
            # Check cache for each model
            cached_entries = []
            cache_hit_count = 0
            
            for model in query.models:
                cached_entry = self.leaderboard_repo.get_cached_entry(
                    model.name,
                    config.language,
                    subject_key,
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
            self.db.rollback()
            return None
    
    def _create_fallback_plan(
        self,
        query: LeaderboardQuery,
        secure_models: List[ModelInfo],
        stored_credentials: List[StoredCredential]
    ) -> str:
        """Create fallback plan when planner agent is not available."""

        # Simple fallback plan
        fallback_plan = {
            "query": query.query,
            "models": [
                {
                    "name": model.name,
                    "api_base": model.api_base,
                    "model_type": model.model_type,
                }
                for model in secure_models
            ],
            "config": {
                "language": "English",  # Default
                "subject_type": "General",  # Default
                "task_type": "QA",  # Default
                "sample_size": 100
            },
            "fallback": True,
            "created_at": datetime.utcnow().isoformat()
        }

        fallback_plan = self._attach_credential_references(
            fallback_plan,
            stored_credentials
        )

        return json.dumps(fallback_plan)

    def _build_secure_models(
        self,
        models: List[ModelInfo],
        stored_credentials: List[StoredCredential]
    ) -> List[ModelInfo]:
        """Return sanitized models without raw API keys."""

        secure_models: List[ModelInfo] = []
        for model, stored in zip(models, stored_credentials):
            secure_model = ModelInfo(
                name=model.name,
                api_base=model.api_base,
                api_key=f"credential:{stored.id}",
                model_type=model.model_type,
            )
            secure_models.append(secure_model)

            # Scrub original model reference to avoid lingering secrets
            model.api_key = "REDACTED"

        return secure_models

    def _attach_credential_references(
        self,
        plan_data: Dict[str, Any],
        stored_credentials: List[StoredCredential]
    ) -> Dict[str, Any]:
        """Attach credential identifiers and remove sensitive fields."""

        plan_models = plan_data.get("models", [])

        if len(plan_models) != len(stored_credentials):
            raise ValueError("Plan metadata models do not match stored credentials")

        sanitized_models = []
        for model_entry, credential in zip(plan_models, stored_credentials):
            sanitized = {
                key: value
                for key, value in model_entry.items()
                if key != "api_key"
            }
            sanitized["credential_id"] = credential.id
            sanitized["credential_hash"] = credential.credential_hash
            sanitized_models.append(sanitized)

        plan_data["models"] = sanitized_models
        plan_data.setdefault("metadata", {})["secured_credentials"] = True
        return plan_data
    
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

    def _default_plan_config(self) -> PlanConfig:
        """Create a safe default plan configuration."""
        return PlanConfig(
            problem_type="MCQA",
            target_type="General",
            subject_type=["Science"],
            task_type="Knowledge",
            external_tool_usage=False,
            language="English",
            sample_size=100
        )

    def suggest_leaderboard_filters(self, query: str) -> LeaderboardSuggestionResponse:
        """Suggest leaderboard filters based on a natural language query."""
        
        normalized_query = (query or "").strip()
        
        if not normalized_query:
            return LeaderboardSuggestionResponse(
                query=query or "",
                language=None,
                subject_type=None,
                task_type=None,
                subject_type_options=[],
                plan_summary="필터 없이 전체 리더보드를 보여드릴게요.",
                used_planner=False,
                metadata={"reason": "empty_query"}
            )
        
        plan_config: Optional[PlanConfig] = None
        used_planner = False
        planner_error: Optional[str] = None
        
        if self.planner_agent:
            try:
                plan_config = self.planner_agent.parse_query(normalized_query)
                used_planner = True
            except Exception as e:
                planner_error = str(e)
                logger.warning("Planner failed to parse query '%s': %s", normalized_query, e)
        
        if plan_config is None:
            plan_config = self._default_plan_config()
        
        subject_options: List[str] = []
        raw_subjects = plan_config.subject_type
        if isinstance(raw_subjects, list):
            subject_options = [item for item in raw_subjects if isinstance(item, str) and item]
        elif isinstance(raw_subjects, str):
            subject_options = [raw_subjects]
        
        primary_subject = subject_options[-1] if subject_options else None
        language = plan_config.language or None
        task_type = plan_config.task_type or None
        
        summary_parts = [
            language or "모든 언어",
            primary_subject or "전체 과목",
            task_type or "전체 태스크"
        ]
        plan_summary = " · ".join(summary_parts) + " 기준으로 추천 필터를 설정했어요."
        
        metadata: Dict[str, Any] = {
            "plan_config": plan_config.dict(),
            "planner_error": planner_error
        }
        
        return LeaderboardSuggestionResponse(
            query=normalized_query,
            language=language,
            subject_type=primary_subject,
            task_type=task_type,
            subject_type_options=subject_options,
            plan_summary=plan_summary,
            used_planner=used_planner,
            metadata=metadata
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
            subject_type_raw = config.get("subject_type", "Unknown")
            task_type = config.get("task_type", "Unknown")

            # Normalize subject_type from plan (can be list)
            subject_key = (
                "/".join(subject_type_raw)
                if isinstance(subject_type_raw, list)
                else str(subject_type_raw)
            )
            
            # Update cache for each model result
            for result in evaluation_results:
                model_name = result.get("model_name")
                score = result.get("average_score", 0.0)
                
                if model_name and isinstance(score, (int, float)):
                    self.leaderboard_repo.upsert_entry(
                        model_name=model_name,
                        language=language,
                        subject_type=subject_key,
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
