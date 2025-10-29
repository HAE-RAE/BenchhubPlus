"""Storage utilities for HRET evaluation results in BenchhubPlus database."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Import database models
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import SessionLocal, ExperimentSample, LeaderboardCache, EvaluationTask
from worker.hret_mapper import BenchhubSample, BenchhubModelResult, HRETResultMapper

logger = logging.getLogger(__name__)


class HRETStorageManager:
    """Manages storage of HRET evaluation results in BenchhubPlus database."""
    
    def __init__(self):
        """Initialize HRET storage manager."""
        self.mapper = HRETResultMapper()
    
    def store_evaluation_results(
        self,
        model_results: List[BenchhubModelResult],
        sample_results: List[BenchhubSample],
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store HRET evaluation results in BenchhubPlus database.
        
        Args:
            model_results: List of model evaluation results
            sample_results: List of sample evaluation results
            task_id: Optional task ID for tracking
            
        Returns:
            Dictionary with storage statistics
        """
        
        storage_stats = {
            "samples_stored": 0,
            "leaderboard_entries_updated": 0,
            "errors": [],
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        db = SessionLocal()
        try:
            # Store sample results
            samples_stored = self._store_sample_results(db, sample_results)
            storage_stats["samples_stored"] = samples_stored
            
            # Update leaderboard cache
            leaderboard_updates = self._update_leaderboard_cache(db, model_results)
            storage_stats["leaderboard_entries_updated"] = leaderboard_updates
            
            # Update evaluation task status if provided
            if task_id:
                self._update_evaluation_task(db, task_id, "SUCCESS", storage_stats)
            
            db.commit()
            logger.info(f"Successfully stored HRET evaluation results: {storage_stats}")
            
        except Exception as e:
            db.rollback()
            error_msg = f"Failed to store HRET evaluation results: {e}"
            logger.error(error_msg)
            storage_stats["errors"].append(error_msg)
            
            # Update task status to failure if provided
            if task_id:
                try:
                    self._update_evaluation_task(db, task_id, "FAILURE", {"error": str(e)})
                    db.commit()
                except Exception as task_error:
                    logger.error(f"Failed to update task status: {task_error}")
            
        finally:
            db.close()
        
        return storage_stats
    
    def _store_sample_results(self, db: Session, sample_results: List[BenchhubSample]) -> int:
        """Store sample results in ExperimentSample table."""
        
        stored_count = 0
        
        for sample in sample_results:
            try:
                db_sample = ExperimentSample(
                    prompt=sample.prompt,
                    answer=sample.answer,
                    skill_label=sample.skill_label,
                    target_label=sample.target_label,
                    subject_label=sample.subject_label,
                    format_label=sample.format_label,
                    dataset_name=sample.dataset_name,
                    meta_data=sample.meta_data,
                    correctness=sample.correctness
                )
                
                db.add(db_sample)
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store sample result: {e}")
                continue
        
        return stored_count
    
    def _update_leaderboard_cache(self, db: Session, model_results: List[BenchhubModelResult]) -> int:
        """Update leaderboard cache with model results."""
        
        updated_count = 0
        
        for model_result in model_results:
            try:
                # Create leaderboard entries for different categories
                entries_to_update = self._generate_leaderboard_entries(model_result)
                
                for entry in entries_to_update:
                    # Check if entry exists
                    existing_entry = db.query(LeaderboardCache).filter(
                        LeaderboardCache.model_name == entry["model_name"],
                        LeaderboardCache.language == entry["language"],
                        LeaderboardCache.subject_type == entry["subject_type"],
                        LeaderboardCache.task_type == entry["task_type"]
                    ).first()
                    
                    if existing_entry:
                        # Update existing entry
                        existing_entry.score = entry["score"]
                        existing_entry.last_updated = entry["last_updated"]
                    else:
                        # Create new entry
                        new_entry = LeaderboardCache(**entry)
                        db.add(new_entry)
                    
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to update leaderboard for model {model_result.model_name}: {e}")
                continue
        
        return updated_count
    
    def _generate_leaderboard_entries(self, model_result: BenchhubModelResult) -> List[Dict[str, Any]]:
        """Generate leaderboard entries for a model result."""
        
        entries = []
        
        # Extract metadata
        metadata = model_result.metadata
        dataset_name = metadata.get("dataset_name", "unknown")
        
        # Determine categories based on dataset and metadata
        language = self._determine_language(dataset_name, metadata)
        subject_types = self._determine_subject_types(dataset_name, metadata)
        task_types = self._determine_task_types(dataset_name, metadata)
        
        # Create entries for each combination
        for subject_type in subject_types:
            for task_type in task_types:
                entry = {
                    "model_name": model_result.model_name,
                    "language": language,
                    "subject_type": subject_type,
                    "task_type": task_type,
                    "score": model_result.accuracy,
                    "last_updated": datetime.utcnow()
                }
                entries.append(entry)
        
        return entries
    
    def _determine_language(self, dataset_name: str, metadata: Dict[str, Any]) -> str:
        """Determine language from dataset name and metadata."""
        
        # Check metadata first
        if "target_lang" in metadata:
            lang_map = {"ko": "Korean", "en": "English", "zh": "Chinese", "ja": "Japanese"}
            return lang_map.get(metadata["target_lang"], metadata["target_lang"])
        
        # Infer from dataset name
        dataset_name = dataset_name.lower()
        if any(korean_indicator in dataset_name for korean_indicator in ["korean", "ko", "haerae", "kmmlu"]):
            return "Korean"
        elif "english" in dataset_name or "en" in dataset_name:
            return "English"
        
        return "Korean"  # Default for Korean-focused BenchhubPlus
    
    def _determine_subject_types(self, dataset_name: str, metadata: Dict[str, Any]) -> List[str]:
        """Determine subject types from dataset name and metadata."""
        
        subjects = []
        dataset_name = dataset_name.lower()
        
        # Map dataset names to subjects
        subject_mapping = {
            "math": ["Mathematics"],
            "science": ["Science"],
            "history": ["History"],
            "literature": ["Literature"],
            "law": ["Law"],
            "medicine": ["Medicine"],
            "economics": ["Economics"],
            "geography": ["Geography"],
            "korean": ["Korean Language"],
            "english": ["English Language"],
            "computer": ["Computer Science"],
            "philosophy": ["Philosophy"],
            "psychology": ["Psychology"],
            "sociology": ["Sociology"]
        }
        
        for key, subject_list in subject_mapping.items():
            if key in dataset_name:
                subjects.extend(subject_list)
        
        # If no specific subjects found, use General
        if not subjects:
            subjects = ["General"]
        
        return subjects
    
    def _determine_task_types(self, dataset_name: str, metadata: Dict[str, Any]) -> List[str]:
        """Determine task types from dataset name and metadata."""
        
        tasks = []
        dataset_name = dataset_name.lower()
        
        # Map dataset names to task types
        task_mapping = {
            "qa": ["QA"],
            "question": ["QA"],
            "reasoning": ["Reasoning"],
            "math": ["Math", "Reasoning"],
            "reading": ["Reading Comprehension"],
            "comprehension": ["Reading Comprehension"],
            "knowledge": ["Knowledge"],
            "generation": ["Generation"],
            "classification": ["Classification"],
            "multiple_choice": ["Multiple Choice"],
            "short_answer": ["Short Answer"],
            "long_answer": ["Long Answer"]
        }
        
        for key, task_list in task_mapping.items():
            if key in dataset_name:
                tasks.extend(task_list)
        
        # If no specific tasks found, use QA as default
        if not tasks:
            tasks = ["QA"]
        
        return list(set(tasks))  # Remove duplicates
    
    def _update_evaluation_task(
        self, 
        db: Session, 
        task_id: str, 
        status: str, 
        result: Dict[str, Any]
    ) -> None:
        """Update evaluation task status and result."""
        
        try:
            task = db.query(EvaluationTask).filter(EvaluationTask.task_id == task_id).first()
            
            if task:
                task.status = status
                task.result = str(result) if result else None
                
                if status in ["SUCCESS", "FAILURE"]:
                    task.completed_at = datetime.utcnow()
                
                logger.info(f"Updated evaluation task {task_id} status to {status}")
            else:
                logger.warning(f"Evaluation task {task_id} not found")
                
        except Exception as e:
            logger.error(f"Failed to update evaluation task {task_id}: {e}")
    
    def get_evaluation_results(
        self,
        model_name: Optional[str] = None,
        dataset_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve evaluation results from database."""
        
        db = SessionLocal()
        try:
            query = db.query(ExperimentSample)
            
            if model_name:
                query = query.filter(ExperimentSample.meta_data.contains(f'"model_name": "{model_name}"'))
            
            if dataset_name:
                query = query.filter(ExperimentSample.dataset_name == dataset_name)
            
            results = query.limit(limit).all()
            
            return [
                {
                    "id": result.id,
                    "prompt": result.prompt,
                    "answer": result.answer,
                    "skill_label": result.skill_label,
                    "target_label": result.target_label,
                    "subject_label": result.subject_label,
                    "format_label": result.format_label,
                    "dataset_name": result.dataset_name,
                    "meta_data": result.meta_data,
                    "correctness": result.correctness,
                    "timestamp": result.timestamp.isoformat()
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to retrieve evaluation results: {e}")
            return []
        finally:
            db.close()
    
    def get_leaderboard_data(
        self,
        language: Optional[str] = None,
        subject_type: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve leaderboard data from cache."""
        
        db = SessionLocal()
        try:
            query = db.query(LeaderboardCache)
            
            if language:
                query = query.filter(LeaderboardCache.language == language)
            
            if subject_type:
                query = query.filter(LeaderboardCache.subject_type == subject_type)
            
            if task_type:
                query = query.filter(LeaderboardCache.task_type == task_type)
            
            results = query.order_by(LeaderboardCache.score.desc()).all()
            
            return [
                {
                    "model_name": result.model_name,
                    "language": result.language,
                    "subject_type": result.subject_type,
                    "task_type": result.task_type,
                    "score": result.score,
                    "last_updated": result.last_updated.isoformat()
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to retrieve leaderboard data: {e}")
            return []
        finally:
            db.close()
    
    def determine_categories(
        self,
        language: str,
        subjects: List[str],
        tasks: List[str]
    ) -> Dict[str, Any]:
        """Determine categories for evaluation results (for testing)."""
        
        return {
            "language": language,
            "subjects": subjects,
            "tasks": tasks,
            "primary_subject": subjects[0] if subjects else "General",
            "primary_task": tasks[0] if tasks else "QA",
            "category_count": len(subjects) + len(tasks),
            "metadata": {
                "categorization_method": "automatic",
                "timestamp": datetime.utcnow().isoformat()
            }
        }


def create_hret_storage_manager() -> HRETStorageManager:
    """Factory function to create HRET storage manager."""
    return HRETStorageManager()