"""Database configuration and models for BenchHub Plus."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    CheckConstraint,
    ForeignKey,
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

# TODO: Add relationships to other tables after review:
class User(Base):
    """User accounts for Google OAuth authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    google_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    full_name = Column(String(255), nullable=True)
    picture_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(50), default="user", nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_users_google_id', 'google_id'),
        Index('idx_users_email', 'email'),
        Index('idx_users_role', 'role'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, full_name='{self.full_name}', email='{self.email}', google_id='{self.google_id}')>"
        )


class LeaderboardCache(Base):
    """Leaderboard cache table for storing pre-computed results."""
    
    __tablename__ = "leaderboard_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(255), nullable=False)
    language = Column(String(50), nullable=False)
    subject_type = Column(String(100), nullable=False)
    task_type = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    quarantined = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_updated = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "model_name",
            "language",
            "subject_type",
            "task_type",
            name="uq_leaderboard_cache_entry",
        ),
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(
        String(20), 
        nullable=False,
        default="PENDING"
    )
    plan_details = Column(Text, nullable=True)
    request_payload = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    error_log = Column(Text, nullable=True)
    policy_tags = Column(Text, nullable=True)
    model_count = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 'CANCELLED', 'HOLD')",
            name="check_status_values"
        ),
        Index("idx_tasks_status_created", "status", "created_at"),
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


class ModelCredential(Base):
    """Securely stored model API credentials."""

    __tablename__ = "model_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(255), nullable=False)
    model_type = Column(String(100), nullable=True)
    api_base = Column(String(255), nullable=False)
    credential_hash = Column(String(128), nullable=False, unique=True)
    encrypted_api_key = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("credential_hash", name="uq_model_credentials_hash"),
    )

    def __repr__(self) -> str:
        return (
            "<ModelCredential(id={id}, model_name='{name}', api_base='{base}')>".format(
                id=self.id,
                name=self.model_name,
                base=self.api_base,
            )
        )


class AuditLog(Base):
    """Audit trail for administrative actions."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    meta = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_audit_resource", "resource", "created_at"),
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
