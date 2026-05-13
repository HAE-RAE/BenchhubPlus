"""Conversational planner — multi-turn spec building + existing-result lookup.

The Evaluation chat exposes two tools to the LLM:

* ``update_evaluation_spec`` — patch slots on the live draft.
* ``search_existing_leaderboard`` — look up rows that may already answer
  the user's question, so we can avoid re-running an evaluation.

The agent loop runs until the model produces a final assistant message
(no further tool calls) or we exhaust ``MAX_TOOL_ITERATIONS``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI

from ..categories import BENCHHUB_COARSE_CATEGORIES, BENCHHUB_FINE_CATEGORIES
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


SAMPLE_SCALES = ("small", "medium", "large", "full")
ALLOWED_MODEL_TYPES = ("openai", "anthropic", "huggingface", "custom")
REQUIRED_SLOTS = (
    "query",
    "category_language",
    "category_subject",
    "category_task_type",
    "sample_scale",
)
MAX_TOOL_ITERATIONS = 4


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant" | "system"
    content: str

    def to_openai(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class LeaderboardLookup:
    """Search result returned to the SPA for inline rendering."""

    filters: Dict[str, Any]
    entries: List[Dict[str, Any]]


@dataclass
class ChatTurnResult:
    reply: str
    spec_patch: Dict[str, Any] = field(default_factory=dict)
    ready: bool = False
    rationale: Optional[str] = None
    used_llm: bool = True
    lookups: List[LeaderboardLookup] = field(default_factory=list)


def _categories_text() -> str:
    lines: List[str] = []
    for coarse in BENCHHUB_COARSE_CATEGORIES:
        lines.append(f"- {coarse}")
        for fine in BENCHHUB_FINE_CATEGORIES.get(coarse, []):
            lines.append(f"  - {fine}")
    return "\n".join(lines)


def _sanitize_patch(patch: Any) -> Dict[str, Any]:
    if not isinstance(patch, dict):
        return {}

    clean: Dict[str, Any] = {}

    if isinstance(patch.get("query"), str) and patch["query"].strip():
        clean["query"] = patch["query"].strip()[:2000]

    for key in ("category_language", "category_subject", "category_task_type"):
        value = patch.get(key)
        if isinstance(value, str) and value.strip():
            clean[key] = value.strip()[:200]

    scale = patch.get("sample_scale")
    if isinstance(scale, str):
        scale = scale.strip().lower()
        if scale in SAMPLE_SCALES:
            clean["sample_scale"] = scale
        elif scale.startswith("custom:"):
            try:
                n = int(scale.split(":", 1)[1])
                if 1 <= n <= 1000:
                    clean["sample_scale"] = f"custom:{n}"
            except ValueError:
                pass

    suggested = patch.get("suggested_models")
    if isinstance(suggested, list):
        norm: List[Dict[str, str]] = []
        for entry in suggested:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name") or "").strip()
            if not name:
                continue
            mt = str(entry.get("model_type") or "openai").strip().lower()
            if mt not in ALLOWED_MODEL_TYPES:
                mt = "openai"
            norm.append({
                "name": name[:120],
                "model_type": mt,
                "api_base": str(entry.get("api_base") or "").strip()[:255],
                "note": str(entry.get("note") or "").strip()[:255],
            })
            if len(norm) >= 5:
                break
        if norm:
            clean["suggested_models"] = norm

    return clean


def _missing_slots(spec: Dict[str, Any]) -> List[str]:
    return [slot for slot in REQUIRED_SLOTS if not spec.get(slot)]


def _heuristic_reply(spec: Dict[str, Any], user_text: str) -> ChatTurnResult:
    """Deterministic fallback when no OpenAI key is configured."""
    patch: Dict[str, Any] = {}
    if user_text and not spec.get("query"):
        patch["query"] = user_text.strip()[:2000]
    merged = {**spec, **patch}
    missing = _missing_slots(merged)

    prompts = {
        "query": "What are you trying to evaluate? A short sentence works.",
        "category_language": "Which language should the benchmark be in — Korean or English?",
        "category_subject": "What subject area? E.g. Science, Tech., Culture.",
        "category_task_type": "Knowledge, Reasoning, or Value/alignment?",
        "sample_scale": "How big should the run be — small (50), medium (100), large (250), or full (500)?",
    }
    if missing:
        reply = prompts[missing[0]]
        ready = False
    else:
        reply = (
            "Spec looks complete. Add at least one model on the right and hit RUN whenever you're ready."
        )
        ready = True

    return ChatTurnResult(
        reply=reply,
        spec_patch=patch,
        ready=ready,
        rationale="heuristic-fallback (no OpenAI key)",
        used_llm=False,
    )


SYSTEM_PROMPT = """You are an evaluation planning assistant for the BenchHub Plus SaaS.
You help users design LLM benchmark runs through a short, terse conversation.

You have two tools:

1. update_evaluation_spec(patch) — write to the draft spec. Include ONLY the
   fields you are changing this turn. Required slots are: query,
   category_language, category_subject, category_task_type, sample_scale.
   API keys are NOT collected in chat — the SPA has its own input panel.

2. search_existing_leaderboard(language, subject_type, task_type, limit) — query
   the leaderboard for already-completed runs. ALWAYS try this before
   recommending a fresh run when the user's question can plausibly be
   answered from existing data. Surface the rows in your reply if useful.

Rules:
- Be terse. 1-3 sentences. Ask the next missing slot, or summarise findings.
- Categories MUST come from the BenchHub list below. Don't invent categories.
- sample_scale must be small/medium/large/full or "custom:N" (1 ≤ N ≤ 1000).
- Suggest at most 3 models, with one-line notes.
- If the user is off-topic, reply briefly without calling any tool.
- After tools return, send a final plain message to the user — that ends the turn.

Allowed BenchHub subject categories:
{categories}
""".replace("{categories}", _categories_text())


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "update_evaluation_spec",
            "description": (
                "Update the evaluation draft spec. Pass only the fields that are "
                "changing this turn — do not repeat already-set fields."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "User-facing description of the run."},
                    "category_language": {"type": "string", "enum": ["Korean", "English"]},
                    "category_subject": {
                        "type": "string",
                        "description": "BenchHub coarse or fine subject category.",
                    },
                    "category_task_type": {
                        "type": "string",
                        "enum": ["Knowledge", "Reasoning", "Value/alignment"],
                    },
                    "sample_scale": {
                        "type": "string",
                        "description": "small | medium | large | full | custom:N (1-1000)",
                    },
                    "suggested_models": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "model_type": {
                                    "type": "string",
                                    "enum": list(ALLOWED_MODEL_TYPES),
                                },
                                "api_base": {"type": "string"},
                                "note": {"type": "string"},
                            },
                            "required": ["name"],
                        },
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_existing_leaderboard",
            "description": (
                "Search already-published leaderboard rows so we can avoid running "
                "a new evaluation when prior results answer the user's question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {"type": "string", "enum": ["Korean", "English"]},
                    "subject_type": {"type": "string"},
                    "task_type": {
                        "type": "string",
                        "enum": ["Knowledge", "Reasoning", "Value/alignment"],
                    },
                    "limit": {"type": "integer", "minimum": 1, "maximum": 25, "default": 10},
                },
                "additionalProperties": False,
            },
        },
    },
]


# Type alias for the leaderboard lookup function injected by the route layer.
# Signature: (filters dict) -> list of {model_name, language, subject_type, task_type, score, last_updated}
LeaderboardSearchFn = Callable[[Dict[str, Any]], List[Dict[str, Any]]]


class EvaluationChatPlanner:
    """Multi-turn slot-filling planner with leaderboard lookup tool."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key
        self.model = settings.planner_model
        self.temperature = settings.planner_temperature
        self._client: Optional[OpenAI] = None
        if self.api_key and not self.api_key.startswith("sk-placeholder"):
            try:
                self._client = OpenAI(api_key=self.api_key)
            except Exception as exc:  # pragma: no cover
                logger.warning("OpenAI client init failed: %s", exc)
                self._client = None

    def respond(
        self,
        spec: Dict[str, Any],
        history: List[ChatMessage],
        user_message: str,
        leaderboard_search: Optional[LeaderboardSearchFn] = None,
    ) -> ChatTurnResult:
        """Process a user turn. May trigger one or more tool calls internally."""
        if not user_message.strip():
            return ChatTurnResult(
                reply="What would you like to evaluate?", used_llm=False
            )

        if self._client is None:
            return _heuristic_reply(spec, user_message)

        accumulated_patch: Dict[str, Any] = {}
        lookups: List[LeaderboardLookup] = []

        spec_summary = json.dumps(spec or {}, ensure_ascii=False)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"Current draft spec (JSON): {spec_summary}"},
        ]
        for msg in history[-16:]:
            if msg.role in ("user", "assistant"):
                messages.append(msg.to_openai())
        messages.append({"role": "user", "content": user_message})

        final_reply = ""
        for _ in range(MAX_TOOL_ITERATIONS):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                    temperature=self.temperature,
                    max_completion_tokens=700,
                )
            except Exception as exc:
                logger.exception("Chat planner LLM call failed: %s", exc)
                return _heuristic_reply(spec, user_message)

            choice = response.choices[0]
            msg = choice.message

            if not msg.tool_calls:
                final_reply = (msg.content or "").strip()
                break

            # Append the assistant turn (with tool calls) so the next iteration
            # has the full context required by the OpenAI tool protocol.
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments or "{}",
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                if name == "update_evaluation_spec":
                    sanitized = _sanitize_patch(args)
                    accumulated_patch.update(sanitized)
                    tool_result = {"ok": True, "applied": sanitized}
                elif name == "search_existing_leaderboard":
                    if leaderboard_search is None:
                        tool_result = {"error": "leaderboard search unavailable"}
                    else:
                        try:
                            rows = leaderboard_search(args) or []
                        except Exception as exc:
                            logger.exception("leaderboard search failed: %s", exc)
                            rows = []
                        lookups.append(LeaderboardLookup(filters=args, entries=rows))
                        tool_result = {"entries": rows[:25]}
                else:
                    tool_result = {"error": f"unknown tool: {name}"}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })
        else:
            # Hit the iteration cap — force a final reply.
            final_reply = (
                "I've gathered some context — could you confirm what you'd like to do next?"
            )

        if not final_reply:
            final_reply = "Could you give me a bit more detail?"

        merged = {**(spec or {}), **accumulated_patch}
        ready = not _missing_slots(merged)

        return ChatTurnResult(
            reply=final_reply,
            spec_patch=accumulated_patch,
            ready=ready,
            lookups=lookups,
        )
