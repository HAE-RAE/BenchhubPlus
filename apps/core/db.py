"""Database configuration and models for BenchHub Plus."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    CheckConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from .config import get_settings

settings = get_settings()

# Create database engine
if settings.is_sqlite:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug,
    )
else:
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class LeaderboardCache(Base):
    """Leaderboard cache table for storing pre-computed results."""
    
    __tablename__ = "leaderboard_cache"
    
    model_name = Column(String(255), primary_key=True, nullable=False)
    language = Column(String(50), primary_key=True, nullable=False)
    subject_type = Column(String(100), primary_key=True, nullable=False)
    task_type = Column(String(100), primary_key=True, nullable=False)
    score = Column(Float, nullable=False)
    last_updated = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return (
            f"<LeaderboardCache(model_name='{self.model_name}', "
            f"language='{self.language}', subject_type='{self.subject_type}', "
            f"task_type='{self.task_type}', score={self.score})>"
        )


class EvaluationTask(Base):
    """Evaluation tasks table for tracking async evaluation jobs."""
    
    __tablename__ = "evaluation_tasks"
    
    task_id = Column(String(255), primary_key=True, nullable=False)
    status = Column(
        String(20), 
        nullable=False,
        default="PENDING"
    )
    plan_details = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'STARTED', 'SUCCESS', 'FAILURE')",
            name="check_status_values"
        ),
    )
    
    def __repr__(self) -> str:
        return (
            f"<EvaluationTask(task_id='{self.task_id}', "
            f"status='{self.status}', created_at='{self.created_at}')>"
        )


class ExperimentSample(Base):
    """Experiment samples table for storing individual evaluation results."""
    
    __tablename__ = "experiment_samples"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    skill_label = Column(String(100), nullable=False)
    target_label = Column(String(100), nullable=False)
    subject_label = Column(String(100), nullable=False)
    format_label = Column(String(100), nullable=False)
    dataset_name = Column(String(100), nullable=False)
    meta_data = Column(Text, nullable=True)  # JSON string
    correctness = Column(Float, nullable=False)
    timestamp = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return (
            f"<ExperimentSample(id={self.id}, dataset_name='{self.dataset_name}', "
            f"skill_label='{self.skill_label}', correctness={self.correctness})>"
        )


def create_tables() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database with tables."""
    create_tables()
    print("Database initialized successfully!")


if __name__ == "__main__":
    init_db()