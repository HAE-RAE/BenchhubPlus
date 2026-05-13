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
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

from .config import get_settings

settings = get_settings()


def _is_pgbouncer_url(url: str) -> bool:
    """Detect Supabase / pgbouncer transaction-pooling endpoints.

    Supabase exposes its transaction pooler on port 6543 with a hostname like
    `aws-0-<region>.pooler.supabase.com`. The session pooler / direct
    connection (5432) supports prepared statements normally.
    """
    if not url:
        return False
    lowered = url.lower()
    return (
        ":6543" in lowered
        or "pooler.supabase" in lowered
        or "pgbouncer=true" in lowered
    )


# Create database engine
if settings.is_sqlite:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False, "timeout": 30},
        echo=settings.debug,
    )

    # SQLite serializes writes via a single global lock. Without WAL mode and
    # a generous busy_timeout, concurrent Celery workers (prefork pool) hit
    # "database is locked" the moment two of them try to update task status
    # at once — and our task wrappers crash with PendingRollbackError before
    # they can even surface a real failure to the user.
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()
elif _is_pgbouncer_url(settings.database_url):
    # Supabase transaction pooler: pgbouncer in transaction mode does NOT
    # preserve session state across queries, so we disable client-side
    # connection pooling (NullPool) and turn off prepared statement caching.
    # The pooler itself handles connection reuse upstream.
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        poolclass=NullPool,
        connect_args={
            # psycopg2 has no per-connection prepared statement cache, but
            # SQLAlchemy emits prepared statements for some dialects. Forcing
            # plain text execution avoids "prepared statement already exists"
            # errors when pgbouncer reuses backend connections.
            "options": "-c statement_timeout=60000",
            "sslmode": "require",
        },
    )
else:
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        # Production-grade pool settings: drop dead connections before use,
        # recycle long-lived connections to dodge proxy idle-timeouts, and
        # cap concurrency so we don't exhaust the DB's max_connections.
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# TODO: Add relationships to other tables after review:
class User(Base):
    """User accounts for GitHub OAuth authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    github_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    full_name = Column(String(255), nullable=True)
    picture_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(50), default="user", nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    default_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    default_workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_users_github_id', 'github_id'),
        Index('idx_users_email', 'email'),
        Index('idx_users_role', 'role'),
        Index('idx_users_default_org', 'default_org_id'),
        Index('idx_users_default_workspace', 'default_workspace_id'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, full_name='{self.full_name}', email='{self.email}', github_id='{self.github_id}')>"
        )


class Organization(Base):
    """Tenant organization for multi-tenant support."""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Workspace(Base):
    """Workspace within an organization."""

    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_workspace_slug"),
    )


class WorkspaceMembership(Base):
    """Membership mapping between users and workspaces."""

    __tablename__ = "workspace_memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(50), default="member", nullable=False)
    is_owner = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
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


class BenchmarkSample(Base):
    """Sample benchmark questions for Data Review preview."""

    __tablename__ = "benchmark_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    language = Column(String(50), nullable=False, index=True)
    subject_type = Column(String(100), nullable=False, index=True)
    task_type = Column(String(100), nullable=False, index=True)
    problem_type = Column(String(50), nullable=True)
    benchmark_name = Column(String(200), nullable=True)
    prompt = Column(Text, nullable=False)
    options = Column(Text, nullable=True)   # JSON string
    answer_str = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_bench_samples_lang_subj", "language", "subject_type"),
        Index("idx_bench_samples_task", "task_type"),
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


class EvaluationDraft(Base):
    """Draft evaluation specs being built conversationally.

    Stores the chat thread and the partially filled spec until the user
    clicks RUN, at which point the draft is converted into an
    ``EvaluationTask`` and marked ``launched``.

    Sensitive material like model API keys is *never* persisted here —
    those are collected by the SPA at launch time and forwarded directly
    to the existing ``/leaderboard/generate`` endpoint.
    """

    __tablename__ = "evaluation_drafts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    # JSON-encoded slot bag (query, category_*, sample_scale, suggested_models).
    spec = Column(Text, nullable=False, default="{}")
    # JSON array of {role, content, created_at} — the visible chat thread.
    messages = Column(Text, nullable=False, default="[]")
    status = Column(String(32), nullable=False, default="draft", index=True)
    launched_task_id = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_evaluation_drafts_user_status", "user_id", "status"),
        Index("idx_evaluation_drafts_updated_at", "updated_at"),
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


def _migrate_users_org_workspace_columns() -> None:
    """Add default_org_id and default_workspace_id to users if missing (migration)."""
    from sqlalchemy import text
    with engine.connect() as conn:
        for col, ref in [
            ("default_org_id", "organizations(id)"),
            ("default_workspace_id", "workspaces(id)"),
        ]:
            try:
                conn.execute(text(
                    f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} INTEGER REFERENCES {ref}"
                ))
                conn.commit()
            except Exception as e:
                conn.rollback()
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    raise


def _migrate_evaluation_tasks_columns() -> None:
    """Add missing columns to evaluation_tasks if they don't exist."""
    from sqlalchemy import text
    simple_cols = [
        ("user_id",         "INTEGER REFERENCES users(id)"),
        ("error_log",       "TEXT"),
        ("policy_tags",     "TEXT"),
        ("model_count",     "INTEGER"),
        ("request_payload", "TEXT"),
        ("updated_at",      "TIMESTAMPTZ DEFAULT NOW()"),
    ]
    with engine.connect() as conn:
        for col, col_def in simple_cols:
            try:
                conn.execute(text(
                    f"ALTER TABLE evaluation_tasks ADD COLUMN IF NOT EXISTS {col} {col_def}"
                ))
                conn.commit()
            except Exception as e:
                conn.rollback()
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    raise
        # Ensure CHECK constraint exists (safe to ignore if already present)
        try:
            conn.execute(text(
                "ALTER TABLE evaluation_tasks ADD CONSTRAINT check_status_values "
                "CHECK (status IN ('PENDING','STARTED','SUCCESS','FAILURE','CANCELLED','HOLD'))"
            ))
            conn.commit()
        except Exception:
            conn.rollback()


def _migrate_leaderboard_cache_columns() -> None:
    """Ensure leaderboard_cache has id PK and all required columns."""
    from sqlalchemy import text
    with engine.connect() as conn:
        # Add missing columns
        for col, col_def in [
            ("quarantined", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("deleted_at",  "TIMESTAMPTZ"),
            ("created_at",  "TIMESTAMPTZ NOT NULL DEFAULT NOW()"),
        ]:
            try:
                conn.execute(text(
                    f"ALTER TABLE leaderboard_cache ADD COLUMN IF NOT EXISTS {col} {col_def}"
                ))
                conn.commit()
            except Exception as e:
                conn.rollback()
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    raise

        # Add id column and promote to primary key if not already done
        try:
            conn.execute(text(
                "ALTER TABLE leaderboard_cache ADD COLUMN IF NOT EXISTS id SERIAL"
            ))
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            conn.execute(text(
                "ALTER TABLE leaderboard_cache DROP CONSTRAINT IF EXISTS leaderboard_cache_pkey"
            ))
            conn.execute(text(
                "ALTER TABLE leaderboard_cache ADD PRIMARY KEY (id)"
            ))
            conn.commit()
        except Exception:
            conn.rollback()

        # Unique constraint
        try:
            conn.execute(text(
                "ALTER TABLE leaderboard_cache ADD CONSTRAINT uq_leaderboard_cache_entry "
                "UNIQUE (model_name, language, subject_type, task_type)"
            ))
            conn.commit()
        except Exception:
            conn.rollback()


def init_db() -> None:
    """Initialize database with tables."""
    create_tables()
    if not settings.is_sqlite:
        _migrate_users_org_workspace_columns()
        _migrate_evaluation_tasks_columns()
        _migrate_leaderboard_cache_columns()
    print("Database initialized successfully!")


if __name__ == "__main__":
    init_db()
