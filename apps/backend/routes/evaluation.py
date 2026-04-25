"""Conversational evaluation spec endpoints.

Drafts hold the chat thread plus the partially filled spec until the user
hits RUN. At launch time we hand off to the existing
``/api/v1/leaderboard/generate`` orchestrator with the model API keys the
SPA collected separately (we never persist the keys with the draft).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from ...core.db import EvaluationDraft, User, get_db
from ...core.plan.chat_planner import (
    ALLOWED_MODEL_TYPES,
    ChatMessage as PlannerMessage,
    EvaluationChatPlanner,
    REQUIRED_SLOTS,
    SAMPLE_SCALES,
)
from ...core.schemas import LeaderboardQuery, ModelInfo
from ..dependencies import get_current_user
from ..repositories.leaderboard_repo import LeaderboardRepository
from ..services.audit import AuditService
from ..services.orchestrator import EvaluationOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])


# --- request / response shapes -------------------------------------------------


class ChatMessageIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ModelLaunchInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    api_base: str = Field(..., min_length=1, max_length=255)
    api_key: str = Field(..., min_length=1, max_length=400)
    model_type: str = Field(default="openai")

    @validator("model_type")
    def _check_model_type(cls, v: str) -> str:
        v = (v or "openai").strip().lower()
        if v not in ALLOWED_MODEL_TYPES:
            raise ValueError(f"model_type must be one of {ALLOWED_MODEL_TYPES}")
        return v


class LaunchRequest(BaseModel):
    models: List[ModelLaunchInput] = Field(..., min_items=1, max_items=10)


# --- helpers -------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _planner() -> EvaluationChatPlanner:
    # Cheap to construct; the OpenAI client is built lazily and reused
    # within a single process. Keeping it per-request avoids stale-client
    # issues if the api key ever rotates.
    return EvaluationChatPlanner()


def _get_owned_draft(db: Session, draft_id: int, user: User) -> EvaluationDraft:
    draft = (
        db.query(EvaluationDraft)
        .filter(EvaluationDraft.id == draft_id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    is_admin = bool(user.is_admin or user.role == "admin")
    if draft.user_id != user.id and not is_admin:
        # Mask the existence of someone else's draft.
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


def _load_json(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _serialize(draft: EvaluationDraft) -> Dict[str, Any]:
    spec = _load_json(draft.spec, {}) or {}
    messages = _load_json(draft.messages, []) or []
    return {
        "id": draft.id,
        "title": draft.title or _derive_title(spec, messages),
        "status": draft.status,
        "spec": spec,
        "messages": messages,
        "missing_slots": [s for s in REQUIRED_SLOTS if not spec.get(s)],
        "launched_task_id": draft.launched_task_id,
        "created_at": draft.created_at,
        "updated_at": draft.updated_at,
    }


def _derive_title(spec: Dict[str, Any], messages: List[Dict[str, Any]]) -> str:
    if isinstance(spec.get("query"), str) and spec["query"].strip():
        return spec["query"].strip()[:80]
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = str(msg.get("content") or "").strip()
            if content:
                return content[:80]
    return "Untitled draft"


def _store_messages(messages: List[Dict[str, Any]]) -> str:
    # Trim to the last 200 messages to keep the row reasonable.
    trimmed = messages[-200:]
    return json.dumps(trimmed, ensure_ascii=False)


# --- routes --------------------------------------------------------------------


@router.post("/drafts", status_code=status.HTTP_201_CREATED)
async def create_draft(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new conversational draft."""
    draft = EvaluationDraft(
        user_id=current_user.id,
        spec="{}",
        messages="[]",
        status="draft",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return _serialize(draft)


@router.get("/drafts")
async def list_drafts(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the caller's drafts, newest first."""
    rows = (
        db.query(EvaluationDraft)
        .filter(EvaluationDraft.user_id == current_user.id)
        .order_by(
            EvaluationDraft.updated_at.desc().nullslast(),
            EvaluationDraft.created_at.desc(),
        )
        .limit(limit)
        .all()
    )
    return {"drafts": [_serialize(r) for r in rows]}


@router.get("/drafts/{draft_id}")
async def get_draft(
    draft_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    draft = _get_owned_draft(db, draft_id, current_user)
    return _serialize(draft)


@router.delete("/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft(
    draft_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    draft = _get_owned_draft(db, draft_id, current_user)
    db.delete(draft)
    db.commit()
    return None


@router.post("/drafts/{draft_id}/messages")
async def append_message(
    payload: ChatMessageIn,
    draft_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a user turn to the conversation and run the planner."""
    draft = _get_owned_draft(db, draft_id, current_user)
    if draft.status != "draft":
        raise HTTPException(
            status_code=409,
            detail=f"Draft is {draft.status} and can no longer be edited",
        )

    spec: Dict[str, Any] = _load_json(draft.spec, {}) or {}
    messages: List[Dict[str, Any]] = _load_json(draft.messages, []) or []

    user_msg = {
        "role": "user",
        "content": payload.message.strip(),
        "created_at": _now().isoformat(),
    }
    messages.append(user_msg)

    history = [
        PlannerMessage(role=m.get("role", "user"), content=str(m.get("content") or ""))
        for m in messages[:-1]
        if m.get("role") in ("user", "assistant")
    ]

    leaderboard_repo = LeaderboardRepository(db)

    def _search(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Tool dispatcher for ``search_existing_leaderboard``.

        Translates the agent's filter dict into a leaderboard query and
        returns rows in a JSON-serialisable shape. Quarantined entries are
        excluded so the agent doesn't recommend tainted results.
        """
        try:
            limit = int(filters.get("limit") or 10)
        except (TypeError, ValueError):
            limit = 10
        limit = max(1, min(limit, 25))
        rows = leaderboard_repo.get_leaderboard(
            language=filters.get("language") or None,
            subject_type=filters.get("subject_type") or None,
            task_type=filters.get("task_type") or None,
            limit=limit,
            include_quarantined=False,
        )
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append({
                "id": r.id,
                "model_name": r.model_name,
                "language": r.language,
                "subject_type": r.subject_type,
                "task_type": r.task_type,
                "score": float(r.score) if r.score is not None else None,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
            })
        return out

    result = _planner().respond(
        spec=spec,
        history=history,
        user_message=user_msg["content"],
        leaderboard_search=_search,
    )

    if result.spec_patch:
        spec.update(result.spec_patch)

    serialized_lookups = [
        {"filters": lk.filters, "entries": lk.entries}
        for lk in result.lookups
    ]

    assistant_msg = {
        "role": "assistant",
        "content": result.reply,
        "created_at": _now().isoformat(),
        "rationale": result.rationale,
        "lookups": serialized_lookups,
    }
    messages.append(assistant_msg)

    draft.spec = json.dumps(spec, ensure_ascii=False)
    draft.messages = _store_messages(messages)
    draft.updated_at = _now()
    if not draft.title:
        draft.title = _derive_title(spec, messages)
    db.commit()
    db.refresh(draft)

    return {
        **_serialize(draft),
        "ready": result.ready,
        "rationale": result.rationale,
    }


@router.post("/drafts/{draft_id}/launch", status_code=status.HTTP_202_ACCEPTED)
async def launch_draft(
    payload: LaunchRequest,
    draft_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convert a fully-specced draft into an EvaluationTask."""
    draft = _get_owned_draft(db, draft_id, current_user)
    if draft.status != "draft":
        raise HTTPException(
            status_code=409,
            detail=f"Draft is {draft.status} and cannot be launched again",
        )

    spec: Dict[str, Any] = _load_json(draft.spec, {}) or {}
    missing = [s for s in REQUIRED_SLOTS if not spec.get(s)]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Spec is incomplete; still need: {', '.join(missing)}",
        )

    sample_scale = spec.get("sample_scale") or "medium"
    if not (
        sample_scale in SAMPLE_SCALES
        or (isinstance(sample_scale, str) and sample_scale.startswith("custom:"))
    ):
        raise HTTPException(status_code=400, detail="Invalid sample_scale")

    try:
        models = [
            ModelInfo(
                name=m.name,
                api_base=m.api_base,
                api_key=m.api_key,
                model_type=m.model_type,
            )
            for m in payload.models
        ]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid model config: {exc}")

    query = LeaderboardQuery(
        query=str(spec.get("query") or "Evaluation"),
        models=models,
        sample_scale=sample_scale,
        category_language=spec.get("category_language"),
        category_subject=spec.get("category_subject"),
        category_task_type=spec.get("category_task_type"),
    )

    orchestrator = EvaluationOrchestrator(db)
    result = orchestrator.generate_leaderboard(query, user_id=current_user.id)

    draft.status = "launched"
    draft.launched_task_id = result.task_id
    draft.updated_at = _now()
    db.commit()

    AuditService(db).log_action(
        action="evaluation.draft.launch",
        resource="evaluation_draft",
        resource_id=str(draft.id),
        user_id=current_user.id,
        metadata={"task_id": result.task_id, "model_count": len(models)},
    )

    return {
        "draft_id": draft.id,
        "task_id": result.task_id,
        "status": result.status,
        "message": result.message,
    }
