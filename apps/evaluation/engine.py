"""Evaluation engine for score calculation and result aggregation."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.db import ExperimentSample, LeaderboardCache
from ..core.schemas import LeaderboardEntry, ModelInfo
from ..core.stats import StatisticsCalculator

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """Engine for calculating scores and aggregating evaluation results."""
    
    def __init__(self, db: Session):
        self.db = db
        self.stats_calculator = StatisticsCalculator()
    
    def calculate_model_scores(
        self,
        model_name: str,
        language: str,
        subject_type: str,
        task_type: str,
        recalculate: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Calculate comprehensive scores for a model."""
        
        try:
            # Check if we have cached results and don't need to recalculate
            if not recalculate:
                cached_entry = self._get_cached_score(
                    model_name, language, subject_type, task_type
                )
                if cached_entry:
                    return self._format_score_result(cached_entry)
            
            # Get sample data for the model
            samples = self._get_model_samples(
                model_name, language, subject_type, task_type
            )
            
            if not samples:
                logger.warning(f"No samples found for {model_name}")
                return None
            
            # Calculate various metrics
            scores = self._calculate_metrics(samples)
            
            # Update cache
            self._update_cache(
                model_name, language, subject_type, task_type, scores["overall_score"]
            )
            
            logger.info(f"Calculated scores for {model_name}: {scores['overall_score']:.3f}")
            return scores
            
        except Exception as e:
            logger.error(f"Failed to calculate scores for {model_name}: {e}")
            return None
    
    def aggregate_results(
        self,
        model_results: List[Dict[str, Any]],
        aggregation_method: str = "weighted_average"
    ) -> Dict[str, Any]:
        """Aggregate results from multiple models."""
        
        try:
            if not model_results:
                return {"error": "No model results provided"}
            
            aggregated = {
                "total_models": len(model_results),
                "aggregation_method": aggregation_method,
                "timestamp": datetime.utcnow(),
                "model_scores": [],
                "summary": {}
            }
            
            # Process each model result
            all_scores = []
            for result in model_results:
                model_name = result.get("model_name")
                score = result.get("average_score", 0.0)
                
                if model_name and isinstance(score, (int, float)):
                    all_scores.append(score)
                    aggregated["model_scores"].append({
                        "model_name": model_name,
                        "score": float(score),
                        "rank": 0  # Will be calculated later
                    })
            
            # Sort by score and assign ranks
            aggregated["model_scores"].sort(key=lambda x: x["score"], reverse=True)
            for i, model_score in enumerate(aggregated["model_scores"]):
                model_score["rank"] = i + 1
            
            # Calculate summary statistics
            if all_scores:
                aggregated["summary"] = {
                    "mean_score": self.stats_calculator.mean(all_scores),
                    "median_score": self.stats_calculator.median(all_scores),
                    "std_dev": self.stats_calculator.std_dev(all_scores),
                    "min_score": min(all_scores),
                    "max_score": max(all_scores),
                    "score_range": max(all_scores) - min(all_scores)
                }
            
            logger.info(f"Aggregated results for {len(model_results)} models")
            return aggregated
            
        except Exception as e:
            logger.error(f"Failed to aggregate results: {e}")
            return {"error": str(e)}
    
    def generate_leaderboard(
        self,
        language: Optional[str] = None,
        subject_type: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 100,
        min_samples: int = 10
    ) -> List[LeaderboardEntry]:
        """Generate leaderboard with filtering and minimum sample requirements."""
        
        try:
            query = self.db.query(LeaderboardCache)
            
            # Apply filters
            if language:
                query = query.filter(LeaderboardCache.language == language)
            if subject_type:
                query = query.filter(LeaderboardCache.subject_type == subject_type)
            if task_type:
                query = query.filter(LeaderboardCache.task_type == task_type)
            
            # Get entries ordered by score
            entries = query.order_by(LeaderboardCache.score.desc()).limit(limit).all()
            
            # Filter by minimum samples if required
            if min_samples > 0:
                filtered_entries = []
                for entry in entries:
                    sample_count = self._get_sample_count(
                        entry.model_name,
                        entry.language,
                        entry.subject_type,
                        entry.task_type
                    )
                    if sample_count >= min_samples:
                        filtered_entries.append(entry)
                entries = filtered_entries
            
            # Convert to LeaderboardEntry objects
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
            
            logger.info(f"Generated leaderboard with {len(leaderboard_entries)} entries")
            return leaderboard_entries
            
        except Exception as e:
            logger.error(f"Failed to generate leaderboard: {e}")
            return []
    
    def compare_models(
        self,
        model_names: List[str],
        language: str,
        subject_type: str,
        task_type: str
    ) -> Dict[str, Any]:
        """Compare multiple models across various metrics."""
        
        try:
            comparison = {
                "models": model_names,
                "criteria": {
                    "language": language,
                    "subject_type": subject_type,
                    "task_type": task_type
                },
                "results": [],
                "statistical_tests": {},
                "timestamp": datetime.utcnow()
            }
            
            model_data = []
            
            # Get data for each model
            for model_name in model_names:
                samples = self._get_model_samples(
                    model_name, language, subject_type, task_type
                )
                
                if samples:
                    scores = [sample.correctness for sample in samples]
                    metrics = self._calculate_metrics(samples)
                    
                    model_data.append({
                        "model_name": model_name,
                        "sample_count": len(samples),
                        "scores": scores,
                        "metrics": metrics
                    })
                    
                    comparison["results"].append({
                        "model_name": model_name,
                        "sample_count": len(samples),
                        "overall_score": metrics["overall_score"],
                        "confidence_interval": metrics.get("confidence_interval", [0, 0]),
                        "percentiles": metrics.get("percentiles", {})
                    })
            
            # Perform statistical tests if we have multiple models
            if len(model_data) >= 2:
                comparison["statistical_tests"] = self._perform_statistical_tests(model_data)
            
            logger.info(f"Compared {len(model_names)} models")
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare models: {e}")
            return {"error": str(e)}
    
    def _get_cached_score(
        self,
        model_name: str,
        language: str,
        subject_type: str,
        task_type: str
    ) -> Optional[LeaderboardCache]:
        """Get cached score entry."""
        
        return self.db.query(LeaderboardCache).filter(
            LeaderboardCache.model_name == model_name,
            LeaderboardCache.language == language,
            LeaderboardCache.subject_type == subject_type,
            LeaderboardCache.task_type == task_type
        ).first()
    
    def _get_model_samples(
        self,
        model_name: str,
        language: str,
        subject_type: str,
        task_type: str
    ) -> List[ExperimentSample]:
        """Get experiment samples for a model."""
        
        return self.db.query(ExperimentSample).filter(
            ExperimentSample.meta_data.contains(f'"model_name": "{model_name}"'),
            ExperimentSample.target_label == language,
            ExperimentSample.subject_label == subject_type,
            ExperimentSample.skill_label == task_type
        ).all()
    
    def _get_sample_count(
        self,
        model_name: str,
        language: str,
        subject_type: str,
        task_type: str
    ) -> int:
        """Get count of samples for a model."""
        
        return self.db.query(func.count(ExperimentSample.id)).filter(
            ExperimentSample.meta_data.contains(f'"model_name": "{model_name}"'),
            ExperimentSample.target_label == language,
            ExperimentSample.subject_label == subject_type,
            ExperimentSample.skill_label == task_type
        ).scalar() or 0
    
    def _calculate_metrics(self, samples: List[ExperimentSample]) -> Dict[str, Any]:
        """Calculate comprehensive metrics from samples."""
        
        scores = [sample.correctness for sample in samples]
        
        if not scores:
            return {"overall_score": 0.0, "sample_count": 0}
        
        # Basic statistics
        mean_score = self.stats_calculator.mean(scores)
        median_score = self.stats_calculator.median(scores)
        std_dev = self.stats_calculator.std_dev(scores)
        
        # Confidence interval
        confidence_interval = self.stats_calculator.confidence_interval(scores)
        
        # Percentiles
        percentiles = {
            "25th": self.stats_calculator.percentile(scores, 25),
            "50th": median_score,
            "75th": self.stats_calculator.percentile(scores, 75),
            "90th": self.stats_calculator.percentile(scores, 90),
            "95th": self.stats_calculator.percentile(scores, 95)
        }
        
        # Score distribution
        distribution = self._calculate_score_distribution(scores)
        
        return {
            "overall_score": mean_score,
            "median_score": median_score,
            "std_dev": std_dev,
            "sample_count": len(scores),
            "confidence_interval": confidence_interval,
            "percentiles": percentiles,
            "distribution": distribution,
            "min_score": min(scores),
            "max_score": max(scores)
        }
    
    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate score distribution in bins."""
        
        bins = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }
        
        for score in scores:
            if score < 0.2:
                bins["0.0-0.2"] += 1
            elif score < 0.4:
                bins["0.2-0.4"] += 1
            elif score < 0.6:
                bins["0.4-0.6"] += 1
            elif score < 0.8:
                bins["0.6-0.8"] += 1
            else:
                bins["0.8-1.0"] += 1
        
        return bins
    
    def _update_cache(
        self,
        model_name: str,
        language: str,
        subject_type: str,
        task_type: str,
        score: float
    ) -> None:
        """Update leaderboard cache."""
        
        try:
            # Check if entry exists
            existing = self._get_cached_score(
                model_name, language, subject_type, task_type
            )
            
            if existing:
                existing.score = score
                existing.last_updated = datetime.utcnow()
            else:
                new_entry = LeaderboardCache(
                    model_name=model_name,
                    language=language,
                    subject_type=subject_type,
                    task_type=task_type,
                    score=score,
                    last_updated=datetime.utcnow()
                )
                self.db.add(new_entry)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update cache: {e}")
            self.db.rollback()
    
    def _format_score_result(self, cached_entry: LeaderboardCache) -> Dict[str, Any]:
        """Format cached score result."""
        
        return {
            "overall_score": cached_entry.score,
            "model_name": cached_entry.model_name,
            "language": cached_entry.language,
            "subject_type": cached_entry.subject_type,
            "task_type": cached_entry.task_type,
            "last_updated": cached_entry.last_updated,
            "cached": True
        }
    
    def _perform_statistical_tests(self, model_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform statistical tests between models."""
        
        try:
            # TODO: Implement proper statistical tests
            # For now, return placeholder results
            
            tests = {
                "t_test": {
                    "description": "T-test for comparing means",
                    "results": []
                },
                "anova": {
                    "description": "ANOVA for multiple group comparison",
                    "f_statistic": 0.0,
                    "p_value": 1.0
                }
            }
            
            # Pairwise t-tests (placeholder)
            for i in range(len(model_data)):
                for j in range(i + 1, len(model_data)):
                    model1 = model_data[i]
                    model2 = model_data[j]
                    
                    # Placeholder t-test result
                    tests["t_test"]["results"].append({
                        "model1": model1["model_name"],
                        "model2": model2["model_name"],
                        "t_statistic": 0.0,
                        "p_value": 0.5,
                        "significant": False
                    })
            
            return tests
            
        except Exception as e:
            logger.error(f"Failed to perform statistical tests: {e}")
            return {"error": str(e)}


def create_evaluation_engine(db: Session) -> EvaluationEngine:
    """Factory function to create evaluation engine."""
    return EvaluationEngine(db)