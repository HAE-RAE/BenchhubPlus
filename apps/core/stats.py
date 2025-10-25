"""Statistics and aggregation utilities for BenchHub Plus."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from .db import ExperimentSample, LeaderboardCache


def calculate_model_score(
    db: Session,
    model_name: str,
    language: str,
    subject_type: str,
    task_type: str,
    time_window_hours: Optional[int] = None
) -> Optional[float]:
    """Calculate aggregated score for a model on specific criteria."""
    
    query = db.query(func.avg(ExperimentSample.correctness)).filter(
        ExperimentSample.skill_label == task_type,
        ExperimentSample.subject_label == subject_type,
        ExperimentSample.target_label == language,
    )
    
    # Add time window filter if specified
    if time_window_hours:
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        query = query.filter(ExperimentSample.timestamp >= cutoff_time)
    
    result = query.scalar()
    return float(result) if result is not None else None


def get_leaderboard_data(
    db: Session,
    language: Optional[str] = None,
    subject_type: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """Get leaderboard data with optional filtering."""
    
    query = db.query(LeaderboardCache)
    
    if language:
        query = query.filter(LeaderboardCache.language == language)
    if subject_type:
        query = query.filter(LeaderboardCache.subject_type == subject_type)
    if task_type:
        query = query.filter(LeaderboardCache.task_type == task_type)
    
    results = query.order_by(LeaderboardCache.score.desc()).limit(limit).all()
    
    return [
        {
            "model_name": result.model_name,
            "language": result.language,
            "subject_type": result.subject_type,
            "task_type": result.task_type,
            "score": result.score,
            "last_updated": result.last_updated,
        }
        for result in results
    ]


def update_leaderboard_cache(
    db: Session,
    model_name: str,
    language: str,
    subject_type: str,
    task_type: str,
    score: float
) -> None:
    """Update or insert leaderboard cache entry."""
    
    existing = db.query(LeaderboardCache).filter(
        LeaderboardCache.model_name == model_name,
        LeaderboardCache.language == language,
        LeaderboardCache.subject_type == subject_type,
        LeaderboardCache.task_type == task_type,
    ).first()
    
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
            last_updated=datetime.utcnow(),
        )
        db.add(new_entry)
    
    db.commit()


def get_model_performance_stats(
    db: Session,
    model_name: str,
    time_window_hours: int = 24
) -> Dict:
    """Get comprehensive performance statistics for a model."""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
    
    # Basic stats
    total_samples = db.query(ExperimentSample).filter(
        ExperimentSample.timestamp >= cutoff_time
    ).count()
    
    if total_samples == 0:
        return {
            "total_samples": 0,
            "average_score": 0.0,
            "score_distribution": {},
            "performance_by_category": {},
        }
    
    # Average score
    avg_score = db.query(func.avg(ExperimentSample.correctness)).filter(
        ExperimentSample.timestamp >= cutoff_time
    ).scalar()
    
    # Score distribution
    samples = db.query(ExperimentSample.correctness).filter(
        ExperimentSample.timestamp >= cutoff_time
    ).all()
    
    scores = [s[0] for s in samples]
    score_distribution = {
        "min": min(scores),
        "max": max(scores),
        "median": sorted(scores)[len(scores) // 2],
        "std": pd.Series(scores).std(),
    }
    
    # Performance by category
    category_stats = db.query(
        ExperimentSample.skill_label,
        ExperimentSample.subject_label,
        func.avg(ExperimentSample.correctness).label("avg_score"),
        func.count(ExperimentSample.id).label("sample_count")
    ).filter(
        ExperimentSample.timestamp >= cutoff_time
    ).group_by(
        ExperimentSample.skill_label,
        ExperimentSample.subject_label
    ).all()
    
    performance_by_category = {
        f"{stat.skill_label}_{stat.subject_label}": {
            "average_score": float(stat.avg_score),
            "sample_count": stat.sample_count,
        }
        for stat in category_stats
    }
    
    return {
        "total_samples": total_samples,
        "average_score": float(avg_score) if avg_score else 0.0,
        "score_distribution": score_distribution,
        "performance_by_category": performance_by_category,
    }


def get_trending_models(
    db: Session,
    time_window_hours: int = 24,
    limit: int = 10
) -> List[Dict]:
    """Get trending models based on recent performance."""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
    
    # Get models with recent activity
    trending = db.query(
        LeaderboardCache.model_name,
        func.avg(LeaderboardCache.score).label("avg_score"),
        func.count(LeaderboardCache.model_name).label("category_count")
    ).filter(
        LeaderboardCache.last_updated >= cutoff_time
    ).group_by(
        LeaderboardCache.model_name
    ).order_by(
        func.avg(LeaderboardCache.score).desc()
    ).limit(limit).all()
    
    return [
        {
            "model_name": model.model_name,
            "average_score": float(model.avg_score),
            "category_count": model.category_count,
        }
        for model in trending
    ]


def calculate_category_difficulty(
    db: Session,
    language: str,
    subject_type: str,
    task_type: str,
    time_window_hours: int = 168  # 1 week
) -> Dict:
    """Calculate difficulty metrics for a specific category."""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
    
    samples = db.query(ExperimentSample.correctness).filter(
        ExperimentSample.target_label == language,
        ExperimentSample.subject_label == subject_type,
        ExperimentSample.skill_label == task_type,
        ExperimentSample.timestamp >= cutoff_time
    ).all()
    
    if not samples:
        return {
            "difficulty_score": 0.0,
            "sample_count": 0,
            "average_performance": 0.0,
            "performance_variance": 0.0,
        }
    
    scores = [s[0] for s in samples]
    avg_performance = sum(scores) / len(scores)
    
    # Difficulty is inverse of average performance
    difficulty_score = 1.0 - avg_performance
    
    # Calculate variance
    variance = sum((s - avg_performance) ** 2 for s in scores) / len(scores)
    
    return {
        "difficulty_score": difficulty_score,
        "sample_count": len(samples),
        "average_performance": avg_performance,
        "performance_variance": variance,
    }


def generate_performance_report(
    db: Session,
    model_names: List[str],
    time_window_hours: int = 24
) -> Dict:
    """Generate comprehensive performance report for multiple models."""
    
    report = {
        "generated_at": datetime.utcnow(),
        "time_window_hours": time_window_hours,
        "models": {},
        "summary": {},
    }
    
    all_scores = []
    
    for model_name in model_names:
        model_stats = get_model_performance_stats(
            db, model_name, time_window_hours
        )
        report["models"][model_name] = model_stats
        
        if model_stats["total_samples"] > 0:
            all_scores.append(model_stats["average_score"])
    
    # Generate summary statistics
    if all_scores:
        report["summary"] = {
            "total_models": len(model_names),
            "active_models": len(all_scores),
            "best_score": max(all_scores),
            "worst_score": min(all_scores),
            "average_score": sum(all_scores) / len(all_scores),
        }
    else:
        report["summary"] = {
            "total_models": len(model_names),
            "active_models": 0,
            "best_score": 0.0,
            "worst_score": 0.0,
            "average_score": 0.0,
        }
    
    return report