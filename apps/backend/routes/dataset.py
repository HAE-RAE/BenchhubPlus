"""Dataset browse API — exposes benchmark sample questions and recent model names."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.db import get_db, BenchmarkSample, ModelCredential, EvaluationTask
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dataset", tags=["dataset"])


@router.get("/models/recent")
async def recent_models(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return recently used model names from this user's task history.

    The shared ``model_credentials`` table currently has no per-user column,
    so for non-admins we restrict the response to model names that appear
    in the caller's own evaluation tasks. Admins see the global view.
    """
    is_admin = bool(current_user and (current_user.is_admin or current_user.role == "admin"))
    names: set[str] = set()

    if is_admin:
        # Admins get the full global view (credentials + all task names).
        for (name,) in (
            db.query(ModelCredential.model_name)
            .order_by(ModelCredential.created_at.desc())
            .limit(limit)
            .all()
        ):
            if name:
                names.add(name)

        task_query = (
            db.query(EvaluationTask.model_name)
            .filter(EvaluationTask.model_name.isnot(None))
        )
    else:
        # Non-admins: only model names from the caller's own tasks. This
        # closes the tenant-leak where one user could enumerate models
        # configured by another user.
        task_query = (
            db.query(EvaluationTask.model_name)
            .filter(
                EvaluationTask.model_name.isnot(None),
                EvaluationTask.user_id == current_user.id,
            )
        )

    for (name,) in (
        task_query.order_by(EvaluationTask.created_at.desc()).limit(limit).all()
    ):
        if name:
            # model_name may be comma-separated if multiple models
            for part in name.split(","):
                part = part.strip()
                if part and part != "configuring...":
                    names.add(part)

    return {"models": sorted(names)}


@router.get("/sample")
async def sample_benchmark_data(
    language: Optional[str] = Query(None),
    subject_type: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return sample benchmark questions for the given filters."""
    q = db.query(BenchmarkSample)
    if language:
        q = q.filter(BenchmarkSample.language == language)
    if subject_type:
        q = q.filter(BenchmarkSample.subject_type == subject_type)
    if task_type:
        q = q.filter(BenchmarkSample.task_type == task_type)

    rows = q.limit(limit).all()

    return {
        "total": q.count(),
        "samples": [
            {
                "id": r.id,
                "language": r.language,
                "subject_type": r.subject_type,
                "task_type": r.task_type,
                "problem_type": r.problem_type,
                "benchmark_name": r.benchmark_name,
                "prompt": r.prompt,
                "options": r.options,
                "answer_str": r.answer_str,
            }
            for r in rows
        ],
    }


@router.get("/categories")
async def list_categories(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return available (language, subject_type, task_type) combinations with counts."""
    from sqlalchemy import func as sqlfunc
    rows = (
        db.query(
            BenchmarkSample.language,
            BenchmarkSample.subject_type,
            BenchmarkSample.task_type,
            sqlfunc.count(BenchmarkSample.id).label("count"),
        )
        .group_by(
            BenchmarkSample.language,
            BenchmarkSample.subject_type,
            BenchmarkSample.task_type,
        )
        .all()
    )
    return [
        {"language": r.language, "subject_type": r.subject_type, "task_type": r.task_type, "count": r.count}
        for r in rows
    ]
