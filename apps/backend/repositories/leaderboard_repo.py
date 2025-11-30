"""Repository for leaderboard cache operations."""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from ...core.db import LeaderboardCache


class LeaderboardRepository:
    """Repository for leaderboard cache operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_cached_entry(
        self,
        model_name: str,
        language: str,
        subject_type: str,
        task_type: str
    ) -> Optional[LeaderboardCache]:
        """Get cached leaderboard entry."""
        return self.db.query(LeaderboardCache).filter(
            LeaderboardCache.model_name == model_name,
            LeaderboardCache.language == language,
            LeaderboardCache.subject_type == subject_type,
            LeaderboardCache.task_type == task_type,
            LeaderboardCache.quarantined.is_(False),
            LeaderboardCache.deleted_at.is_(None),
        ).first()

    def get_by_id(self, entry_id: int) -> Optional[LeaderboardCache]:
        """Fetch entry by ID."""
        return self.db.query(LeaderboardCache).filter(LeaderboardCache.id == entry_id).first()
    
    def get_leaderboard(
        self,
        language: Optional[str] = None,
        subject_type: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 100,
        include_quarantined: bool = False
    ) -> List[LeaderboardCache]:
        """Get leaderboard entries with optional filtering."""
        query = self.db.query(LeaderboardCache)
        
        if language:
            query = query.filter(LeaderboardCache.language == language)
        if subject_type:
            query = query.filter(LeaderboardCache.subject_type == subject_type)
        if task_type:
            query = query.filter(LeaderboardCache.task_type == task_type)

        if not include_quarantined:
            query = query.filter(
                LeaderboardCache.quarantined.is_(False),
                LeaderboardCache.deleted_at.is_(None),
            )
        
        return query.order_by(LeaderboardCache.score.desc()).limit(limit).all()
    
    def upsert_entry(
        self,
        model_name: str,
        language: str,
        subject_type: str,
        task_type: str,
        score: float,
        quarantined: bool = False
    ) -> LeaderboardCache:
        """Insert or update leaderboard entry."""
        existing = (
            self.db.query(LeaderboardCache)
            .filter(
                LeaderboardCache.model_name == model_name,
                LeaderboardCache.language == language,
                LeaderboardCache.subject_type == subject_type,
                LeaderboardCache.task_type == task_type,
            )
            .first()
        )
        
        if existing:
            existing.score = score
            existing.last_updated = datetime.utcnow()
            existing.quarantined = quarantined
            existing.deleted_at = None
            entry = existing
        else:
            entry = LeaderboardCache(
                model_name=model_name,
                language=language,
                subject_type=subject_type,
                task_type=task_type,
                score=score,
                quarantined=quarantined,
                last_updated=datetime.utcnow()
            )
            self.db.add(entry)
        
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def delete_entry(
        self,
        model_name: str,
        language: str,
        subject_type: str,
        task_type: str
    ) -> bool:
        """Delete leaderboard entry."""
        entry = self.get_cached_entry(
            model_name, language, subject_type, task_type
        )
        
        if entry:
            self.db.delete(entry)
            self.db.commit()
            return True
        
        return False

    def soft_delete(self, entry_id: int, quarantine: bool = True) -> bool:
        """Soft delete (quarantine) an entry."""
        entry = self.get_by_id(entry_id)
        if not entry:
            return False
        entry.quarantined = quarantine
        entry.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def hard_delete(self, entry_id: int) -> bool:
        """Physically remove an entry."""
        entry = self.get_by_id(entry_id)
        if not entry:
            return False
        self.db.delete(entry)
        self.db.commit()
        return True

    def manual_entry(
        self,
        model_name: str,
        language: str,
        subject_type: str,
        task_type: str,
        score: float,
        quarantined: bool = False,
    ) -> LeaderboardCache:
        """Create or update an entry from admin input."""
        return self.upsert_entry(
            model_name=model_name,
            language=language,
            subject_type=subject_type,
            task_type=task_type,
            score=score,
            quarantined=quarantined,
        )
    
    def clear_cache(self, older_than_hours: Optional[int] = None) -> int:
        """Clear cache entries, optionally only older than specified hours."""
        query = self.db.query(LeaderboardCache)
        
        if older_than_hours:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            query = query.filter(LeaderboardCache.last_updated < cutoff_time)
        
        count = query.count()
        query.delete()
        self.db.commit()
        
        return count
    
    def get_model_rankings(self, model_name: str) -> List[LeaderboardCache]:
        """Get all rankings for a specific model."""
        return self.db.query(LeaderboardCache).filter(
            LeaderboardCache.model_name == model_name
        ).order_by(LeaderboardCache.score.desc()).all()
    
    def get_category_stats(
        self,
        language: str,
        subject_type: str,
        task_type: str
    ) -> dict:
        """Get statistics for a specific category."""
        from sqlalchemy import func
        
        stats = self.db.query(
            func.count(LeaderboardCache.model_name).label('model_count'),
            func.avg(LeaderboardCache.score).label('avg_score'),
            func.max(LeaderboardCache.score).label('max_score'),
            func.min(LeaderboardCache.score).label('min_score')
        ).filter(
            LeaderboardCache.language == language,
            LeaderboardCache.subject_type == subject_type,
            LeaderboardCache.task_type == task_type
        ).first()
        
        return {
            'model_count': stats.model_count or 0,
            'average_score': float(stats.avg_score) if stats.avg_score else 0.0,
            'max_score': float(stats.max_score) if stats.max_score else 0.0,
            'min_score': float(stats.min_score) if stats.min_score else 0.0,
        }
