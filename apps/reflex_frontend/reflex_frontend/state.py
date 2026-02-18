"""BenchHub Plus - Application State.

Centralises all reactive state, computed properties, and backend API
interactions for the Reflex frontend.
"""

import reflex as rx
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime
import os

# ---------------------------------------------------------------------------
# API configuration
# ---------------------------------------------------------------------------
DEFAULT_API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
PUBLIC_API_BASE = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8001")
API_TIMEOUT = 30


class AppState(rx.State):
    """Main application state for BenchHub Plus."""

    # -- API / env --------------------------------------------------------
    api_base_url: str = DEFAULT_API_BASE
    access_token: str = os.getenv("MANAGER_TOKEN", "")
    dev_auth_bypass: bool = os.getenv("DEV_AUTH_BYPASS", "").lower() in {
        "1",
        "true",
        "yes",
    }

    # -- Auth -------------------------------------------------------------
    is_authenticated: bool = False
    user_email: str = ""
    user_name: str = ""
    user_picture: str = ""
    user_role: str = ""
    user_id: int = 0
    auth_checked: bool = False
    auth_error: str = ""
    dev_login_value: str = "dev@local"

    # -- Navigation -------------------------------------------------------
    current_page: str = "evaluation"
    sidebar_collapsed: bool = False

    # -- Task management --------------------------------------------------
    task_history: List[Dict[str, Any]] = []
    current_task_id: Optional[str] = None

    # -- Model / evaluation configuration ---------------------------------
    models: List[Dict[str, Any]] = []
    num_models: int = 2
    query: str = ""
    current_results: Optional[Dict[str, Any]] = None
    is_loading: bool = False
    is_submitting: bool = False

    # -- Evaluation wizard step -------------------------------------------
    # "input"     → initial centered query input screen
    # "configure" → model / data / cost config tabs shown after query submit
    # "detail"    → task detail view (clicked from sidebar history)
    eval_step: str = "input"
    eval_config_tab: str = "model"  # "model" | "data" | "cost"
    eval_is_off_topic: bool = False
    eval_off_topic_message: str = ""
    selected_task_id: str = ""
    selected_task_result_rows: list[dict] = []
    selected_task_error_msg: str = ""
    selected_task_completed_at: str = ""
    selected_task_stage: str = ""        # current stage label while running
    selected_task_stage_pct: int = 0     # 0-100 progress within the stage
    selected_task_models: List[Dict[str, Any]] = []   # [{name, api_base, model_type}]
    selected_task_sample_scale: str = "" # e.g. "medium", "custom:300"
    selected_task_labels: List[str] = [] # benchmark categories / dataset names used

    @rx.var
    def selected_task_sample_label(self) -> str:
        """Human-readable label for the selected task's sample scale."""
        scale = self.selected_task_sample_scale
        labels = {"small": "Small (50)", "medium": "Medium (100)", "large": "Large (250)", "full": "Full (500)"}
        if scale in labels:
            return labels[scale]
        if scale.startswith("custom:"):
            n = scale.split(":", 1)[1]
            return f"Custom ({n})"
        return scale or "—"

    @rx.var
    def selected_task_stage_index(self) -> int:
        """Return 0-4 index of the current pipeline step."""
        s = self.selected_task_stage.lower()
        if "initializ" in s:
            return 0
        if "validat" in s:
            return 1
        if "running" in s or "benchmark" in s:
            return 2
        if "mapping" in s or "map" in s:
            return 3
        if "storing" in s or "store" in s:
            return 4
        return -1
    sample_scale: str = "medium"  # "small"|"medium"|"large"|"full"|"custom"
    custom_sample_count: str = ""  # used when sample_scale == "custom"

    # -- Recent models (for Model Name autocomplete) ----------------------
    recent_model_names: List[str] = []

    # -- Data Review (suggested filters from query) -----------------------
    eval_suggested_language: str = ""
    eval_suggested_subject: str = ""
    eval_suggested_task_type: str = ""
    eval_data_expanded: bool = False   # whether sample panel is open
    eval_data_entries: List[Dict[str, Any]] = []
    eval_data_loading: bool = False

    # -- Leaderboard filters ----------------------------------------------
    language_filter: str = "All"
    subject_filter: str = "All"
    task_type_filter: str = "All"
    max_results: int = 100
    leaderboard_query: str = ""
    leaderboard_query_description: str = ""
    leaderboard_entries: List[Dict[str, Any]] = []
    leaderboard_loading: bool = False
    leaderboard_plan_summary: str = ""
    leaderboard_used_planner: bool = False
    leaderboard_confidence: float = 0.0
    leaderboard_rationale: str = ""
    leaderboard_is_off_topic: bool = False
    leaderboard_suggest_error: str = ""
    leaderboard_last_suggested: Optional[str] = None
    leaderboard_language_options: List[str] = ["All"]
    leaderboard_subject_options: List[str] = ["All"]
    leaderboard_task_type_options: List[str] = ["All"]

    # -- Manager dashboard ------------------------------------------------
    manager_snapshot_loaded: bool = False
    manager_last_updated: Optional[str] = None
    manager_health: Dict[str, Any] = {
        "database": "unknown",
        "redis": "unknown",
        "planner": "unknown",
        "hret": "unknown",
    }
    manager_capacity: Dict[str, Any] = {
        "pending": 0,
        "running": 0,
        "success": 0,
        "failure": 0,
        "cache_entries": 0,
    }
    manager_tasks: List[Dict[str, Any]] = []
    manager_leaderboard: List[Dict[str, Any]] = []
    manager_new_entry: Dict[str, Any] = {
        "model": "",
        "language": "",
        "subject": "",
        "task_type": "",
        "score": "",
    }

    # =====================================================================
    # Simple setters
    # =====================================================================

    def set_page(self, page: str):
        # Redirect "status" to "evaluation" (merged pages)
        if page == "status":
            self.current_page = "evaluation"
        else:
            self.current_page = page

    def toggle_sidebar(self):
        self.sidebar_collapsed = not self.sidebar_collapsed

    def new_evaluation(self):
        """Reset evaluation form and navigate to evaluation page."""
        self.query = ""
        self.models = []
        self.current_task_id = None
        self.current_results = None
        self.current_page = "evaluation"
        self.eval_step = "input"
        self.eval_config_tab = "model"

    async def submit_query(self):
        """Validate query via suggest API, then advance to configure step if on-topic."""
        if not self.query.strip():
            yield rx.toast.error("Please describe what you want to evaluate.")
            return

        self.eval_is_off_topic = False
        self.eval_off_topic_message = ""
        self.is_submitting = True
        yield  # immediately send loading state to browser

        is_off_topic = False
        plan_summary = ""
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/leaderboard/suggest",
                    json={"query": self.query},
                    headers=self._auth_headers(),
                )

            if response.status_code == 200:
                data = response.json()
                metadata = data.get("metadata") or {}
                is_off_topic = metadata.get("reason") == "off_topic"
                plan_summary = data.get("plan_summary") or ""
                # Save suggested filters for Data Review tab
                self.eval_suggested_language = data.get("language") or ""
                self.eval_suggested_subject = data.get("subject_type") or ""
                self.eval_suggested_task_type = data.get("task_type") or ""
                self.eval_data_expanded = False
                self.eval_data_entries = []
        except Exception:
            pass

        self.is_submitting = False

        if is_off_topic:
            self.eval_is_off_topic = True
            self.eval_off_topic_message = plan_summary
            yield
            return

        # Create a local pending entry immediately so the sidebar shows it right away.
        # The real task_id is assigned once Start Evaluation is clicked.
        pending_id = f"pending-{datetime.now().strftime('%H%M%S%f')}"
        pending_task = {
            "id": pending_id,
            "status": "pending",
            "progress": 0,
            "model_name": "configuring...",
            "query": self.query,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_time": "-",
        }
        self.task_history = [pending_task] + self.task_history
        self.current_task_id = pending_id
        self.eval_step = "configure"
        self.eval_config_tab = "model"
        # Load recent models in background for autocomplete
        yield AppState.load_recent_models

    def set_eval_tab(self, tab: str):
        self.eval_config_tab = tab

    def set_eval_step(self, step: str):
        self.eval_step = step

    def set_sample_scale(self, value: str):
        if value in ("small", "medium", "large", "full"):
            self.sample_scale = value
            self.custom_sample_count = ""

    def set_custom_sample_count(self, value: str):
        """Accept only numeric input; switch scale to custom."""
        digits = "".join(c for c in value if c.isdigit())
        self.custom_sample_count = digits
        if digits:
            self.sample_scale = "custom"

    async def load_recent_models(self):
        """Fetch recently used model names from backend."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/dataset/models/recent",
                    headers=self._auth_headers(),
                )
            if response.status_code == 200:
                self.recent_model_names = response.json().get("models") or []
        except Exception:
            pass

    async def load_data_review_samples(self):
        """Toggle the Data Review sample panel — fetch samples for the full suggested combo."""
        if self.eval_data_expanded:
            self.eval_data_expanded = False
            self.eval_data_entries = []
            return

        self.eval_data_expanded = True
        self.eval_data_loading = True
        self.eval_data_entries = []
        yield

        params: dict = {"limit": 5}
        if self.eval_suggested_language:
            params["language"] = self.eval_suggested_language
        if self.eval_suggested_subject:
            params["subject_type"] = self.eval_suggested_subject
        if self.eval_suggested_task_type:
            params["task_type"] = self.eval_suggested_task_type

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/dataset/sample",
                    params=params,
                    headers=self._auth_headers(),
                )
            if response.status_code == 200:
                data = response.json()
                samples = data.get("samples") or []
                self.eval_data_entries = [
                    {
                        "benchmark_name": s.get("benchmark_name", ""),
                        "subject_type": s.get("subject_type", ""),
                        "task_type": s.get("task_type", ""),
                        "problem_type": s.get("problem_type", ""),
                        "prompt": s.get("prompt", "")[:300],
                        "options": s.get("options", ""),
                        "answer_str": s.get("answer_str", ""),
                    }
                    for s in (samples[:5] if isinstance(samples, list) else [])
                ]
        except Exception:
            self.eval_data_entries = []
        finally:
            self.eval_data_loading = False

    def back_to_query(self):
        """Go back to the input step, removing the local pending placeholder."""
        self.task_history = [
            t for t in self.task_history
            if not (t.get("id", "").startswith("pending-") and t.get("query") == self.query)
        ]
        self.current_task_id = None
        self.eval_step = "input"

    async def remove_task_from_history(self, task_id: str):
        """Delete a task from the backend and remove it from the sidebar."""
        # Remove locally first for instant UI response
        self.task_history = [t for t in self.task_history if t.get("id") != task_id]
        if self.selected_task_id == task_id:
            self.selected_task_id = ""
            self.eval_step = "input"
        # Skip pending placeholders (no backend entry yet)
        if task_id.startswith("pending-"):
            return
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.delete(
                    f"{self.api_base_url}/api/v1/tasks/{task_id}/hard",
                    headers=self._auth_headers(),
                )
        except Exception:
            pass

    def clear_suggested_combo(self):
        """Remove the suggested category combo from Data Review."""
        self.eval_suggested_language = ""
        self.eval_suggested_subject = ""
        self.eval_suggested_task_type = ""
        self.eval_data_expanded = False
        self.eval_data_entries = []

    async def select_task(self, task_id: str):
        """Open detail view for a task from the sidebar history."""
        self.selected_task_id = task_id
        self.selected_task_result_rows = []
        self.selected_task_error_msg = ""
        self.selected_task_completed_at = ""
        self.selected_task_stage = ""
        self.selected_task_stage_pct = 0
        self.selected_task_models = []
        self.selected_task_sample_scale = ""
        self.selected_task_labels = []
        self.current_page = "evaluation"
        self.eval_step = "detail"
        # Fetch latest status & result from backend
        await self.refresh_task_status(task_id)

    async def cancel_selected_task(self):
        """Cancel the currently selected task via the API."""
        if not self.selected_task_id or self.selected_task_id.startswith("pending-"):
            # Local pending entry — just remove it
            self.task_history = [
                t for t in self.task_history
                if t.get("id") != self.selected_task_id
            ]
            self.selected_task_id = ""
            self.eval_step = "input"
            return rx.toast.info("Pending evaluation cancelled.")

        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.delete(
                    f"{self.api_base_url}/api/v1/tasks/{self.selected_task_id}",
                    headers=self._auth_headers(),
                )
            if response.status_code == 200:
                for i, t in enumerate(self.task_history):
                    if t.get("id") == self.selected_task_id:
                        self.task_history[i] = {**t, "status": "cancelled"}
                        break
                return rx.toast.success("Evaluation cancelled.")
            else:
                return rx.toast.error("Failed to cancel evaluation.")
        except Exception as e:
            return rx.toast.error(f"Error: {str(e)}")

    def rerun_task(self, task_id: str):
        """Pre-fill query from a past task and go to the configure step."""
        for t in self.task_history:
            if t.get("id") == task_id:
                self.query = t.get("query", "")
                break
        self.models = []
        self.selected_task_id = ""
        self.eval_step = "input"
        self.current_page = "evaluation"

    @rx.var
    def selected_task(self) -> dict:
        """Return the currently selected task dict, or empty dict."""
        for t in self.task_history:
            if t.get("id") == self.selected_task_id:
                return t
        return {}

    def set_language_filter(self, value: str):
        self.language_filter = value

    def set_subject_filter(self, value: str):
        self.subject_filter = value

    def set_task_type_filter(self, value: str):
        self.task_type_filter = value

    def set_max_results(self, value: str):
        try:
            self.max_results = int(value)
        except ValueError:
            self.max_results = 100

    def set_leaderboard_query(self, value: str):
        self.leaderboard_query = value

    def set_access_token(self, value: str):
        self.access_token = value

    def set_dev_login_value(self, value: str):
        self.dev_login_value = value

    def set_query(self, value: str):
        self.query = value
        if self.eval_is_off_topic:
            self.eval_is_off_topic = False
            self.eval_off_topic_message = ""

    # =====================================================================
    # Computed properties
    # =====================================================================

    @rx.var
    def total_task_count(self) -> int:
        return len(self.task_history)

    @rx.var
    def running_task_count(self) -> int:
        return sum(1 for t in self.task_history if t.get("status") == "running")

    @rx.var
    def completed_task_count(self) -> int:
        return sum(1 for t in self.task_history if t.get("status") == "completed")

    @rx.var
    def pending_task_count(self) -> int:
        return sum(1 for t in self.task_history if t.get("status") == "pending")

    @rx.var
    def is_admin_user(self) -> bool:
        return bool(self.is_authenticated and self.user_role == "admin")

    # =====================================================================
    # Private helpers
    # =====================================================================

    def _auth_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _handle_auth_failure(self, message: str):
        self.is_authenticated = False
        self.access_token = ""
        self.user_email = ""
        self.user_name = ""
        self.user_picture = ""
        self.user_role = ""
        self.auth_error = message
        return rx.toast.error(message)

    def _format_duration(self, seconds: float) -> str:
        if seconds is None:
            return "-"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if minutes == 0:
            return f"{secs}s"
        return f"{minutes}m {secs}s"

    def _normalize_task_status(self, status: Optional[str]) -> str:
        if not status:
            return "pending"
        normalized = str(status).strip().upper()
        mapping = {
            "PENDING": "pending",
            "STARTED": "running",
            "SUCCESS": "completed",
            "FAILURE": "failed",
            "CANCELLED": "failed",
            "CANCELED": "failed",
            "HOLD": "pending",
        }
        if normalized in mapping:
            return mapping[normalized]
        lowered = str(status).strip().lower()
        if lowered in {"pending", "running", "completed", "failed"}:
            return lowered
        return "pending"

    def _normalize_option_list(self, values: List[Any]) -> List[str]:
        options: List[str] = ["All"]
        for value in values or []:
            if value is None:
                continue
            cleaned = str(value).strip()
            if cleaned and cleaned not in options:
                options.append(cleaned)
        return options

    def _ensure_option(self, options: List[str], value: Optional[str]) -> List[str]:
        if value and value not in options:
            return options + [value]
        return options

    def _coerce_filter_value(self, value: str) -> Optional[str]:
        if not value or value == "All":
            return None
        return value

    def _clamp_limit(self, value: int) -> int:
        if value < 1:
            return 1
        if value > 1000:
            return 1000
        return value

    # =====================================================================
    # Auth / session
    # =====================================================================

    async def initialize_auth(self):
        """Read token from URL query and fetch current user info."""
        # Reset transient UI states on page load to avoid stale spinner states
        self.is_submitting = False

        try:
            params = self.router.page.params or {}
        except Exception:
            params = {}

        url_token = params.get("token", "")
        if isinstance(url_token, (list, tuple)):
            url_token = url_token[0] if url_token else ""
        url_token = str(url_token).strip().strip('"').strip("'")

        if url_token:
            self.access_token = url_token

        if not self.access_token:
            self.is_authenticated = False
            self.user_email = ""
            self.user_name = ""
            self.user_picture = ""
            self.user_role = ""
            self.auth_error = ""
            self.auth_checked = True
            return

        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                resp = await client.get(
                    f"{self.api_base_url}/api/v1/auth/me",
                    headers=self._auth_headers(),
                )

            if resp.status_code == 200:
                data = resp.json()
                self.is_authenticated = True
                self.user_email = data.get("email", "")
                self.user_name = data.get("name", "")
                self.user_picture = data.get("picture") or ""
                self.user_role = data.get("role") or ""
                self.user_id = int(data.get("id") or 0)
                self.auth_error = ""
                await self._load_tasks_from_backend()
            else:
                detail = ""
                try:
                    detail = resp.json().get("detail", "")
                except Exception:
                    detail = resp.text or ""
                return self._handle_auth_failure(
                    detail or "Session expired. Please log in again."
                )
        except Exception as e:
            print(f"initialize_auth error: {e}")
            return self._handle_auth_failure(
                "Authentication failed. Please log in again."
            )

        self.auth_checked = True

    async def start_google_login(self):
        if self.dev_auth_bypass:
            return rx.toast.info("Use the dev login input to sign in.")
        return rx.redirect(f"{PUBLIC_API_BASE}/api/v1/auth/google/login")

    async def dev_login(self):
        if not self.dev_auth_bypass:
            return rx.toast.error("Dev login is disabled")
        email = (self.dev_login_value or "").strip()
        if not email:
            return rx.toast.error("Please enter an email (any value is accepted)")
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/auth/dev-login",
                    json={"email": email, "name": email},
                )
            if response.status_code != 200:
                detail = response.json().get("detail", "Dev login failed")
                return rx.toast.error(detail)
            data = response.json()
            token = data.get("access_token")
            if not token:
                return rx.toast.error("Dev login failed: missing token")
            self.access_token = token
            self.auth_error = ""
            return await self.initialize_auth()
        except Exception as e:
            return rx.toast.error(f"Dev login failed: {e}")

    async def logout(self):
        self.access_token = ""
        self.is_authenticated = False
        self.user_email = ""
        self.user_name = ""
        self.user_picture = ""
        self.user_role = ""
        self.auth_error = ""
        return rx.redirect(path="/")

    # =====================================================================
    # Evaluation / task management
    # =====================================================================

    def add_model(self):
        self.models.append(
            {
                "name": f"model_{len(self.models) + 1}",
                "api_base": "https://api.openai.com/v1",
                "api_key": "",
                "model_type": "openai",
            }
        )

    def remove_model(self, index: int):
        if 0 <= index < len(self.models):
            self.models.pop(index)

    def update_model(self, index: int, field: str, value: str):
        if 0 <= index < len(self.models):
            self.models[index][field] = value

    async def submit_evaluation(self):
        """Submit evaluation request to backend API."""
        if not self.is_authenticated:
            return rx.toast.error("Please log in to start an evaluation")
        if not self.query.strip():
            return rx.toast.error("Please enter a query")
        if not self.models:
            return rx.toast.error("Please add at least one model")

        for model in self.models:
            if not model.get("name") or not model.get("api_key") or not model.get("api_base"):
                return rx.toast.error("Please fill in all model fields")

        self.is_submitting = True
        try:
            actual_scale = self.sample_scale
            if self.sample_scale == "custom" and self.custom_sample_count:
                actual_scale = f"custom:{self.custom_sample_count}"
            payload = {
                "query": self.query,
                "sample_scale": actual_scale,
                "models": [
                    {
                        "name": m["name"],
                        "api_base": m.get("api_base", ""),
                        "api_key": m["api_key"],
                        "model_type": m["model_type"],
                    }
                    for m in self.models
                ],
                "category_language": self.eval_suggested_language or None,
                "category_subject": self.eval_suggested_subject or None,
                "category_task_type": self.eval_suggested_task_type or None,
            }

            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/leaderboard/generate",
                    json=payload,
                    headers=self._auth_headers(),
                )

                if response.status_code in (200, 202):
                    try:
                        result = response.json() if response.content else {}
                    except Exception:
                        result = {}
                    task_id = result.get("task_id")
                    if not task_id:
                        return rx.toast.error("Failed to start evaluation: missing task ID")
                    normalized_status = self._normalize_task_status(result.get("status"))

                    real_task = {
                        "id": task_id,
                        "status": normalized_status,
                        "progress": 100 if normalized_status == "completed" else 0,
                        "model_name": ", ".join([m["name"] for m in self.models]),
                        "query": self.query,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "estimated_time": result.get("estimated_duration", "Unknown"),
                    }

                    # Replace the local pending placeholder with the real task entry.
                    replaced = False
                    new_history = []
                    for t in self.task_history:
                        if not replaced and t.get("id", "").startswith("pending-") and t.get("query") == self.query:
                            new_history.append(real_task)
                            replaced = True
                        else:
                            new_history.append(t)
                    if not replaced:
                        new_history = [real_task] + new_history
                    self.task_history = new_history

                    self.current_task_id = task_id
                    self.current_page = "evaluation"
                    self.eval_step = "input"  # reset to input for next evaluation
                    # Pre-populate selected task detail state
                    self.selected_task_id = task_id
                    self.selected_task_models = [
                        {"name": m["name"], "api_base": m.get("api_base", ""), "model_type": m.get("model_type", "")}
                        for m in self.models
                    ]
                    self.selected_task_sample_scale = actual_scale
                    self.selected_task_labels = [
                        c for c in [
                            self.eval_suggested_language,
                            self.eval_suggested_subject,
                            self.eval_suggested_task_type,
                        ] if c
                    ]

                    toast_message = (
                        f"Evaluation completed! Task ID: {task_id}"
                        if normalized_status == "completed"
                        else f"Evaluation started! Task ID: {task_id}"
                    )
                    return rx.toast.success(toast_message)
                else:
                    try:
                        error_payload = response.json()
                        error_msg = (
                            error_payload.get("detail")
                            or error_payload.get("message")
                            or "Unknown error"
                        )
                    except Exception:
                        error_msg = response.text or "Unknown error"
                    return rx.toast.error(f"Failed to start evaluation: {error_msg}")

        except httpx.TimeoutException:
            return rx.toast.error("Request timeout. Please try again.")
        except Exception as e:
            return rx.toast.error(f"Error: {str(e)}")
        finally:
            self.is_submitting = False

    async def refresh_task_status(self, task_id: str):
        if not self.is_authenticated:
            return rx.toast.error("Please log in to view task status")
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/tasks/{task_id}",
                    headers=self._auth_headers(),
                )
                if response.status_code == 200:
                    task_data = response.json()
                    normalized_status = self._normalize_task_status(task_data.get("status"))

                    # Extract result fields
                    result = task_data.get("result") or {}
                    model_results = result.get("model_results") or []
                    storage_stats = result.get("storage_stats") or {}
                    result_rows = []
                    for mr in model_results:
                        acc = mr.get("accuracy")
                        result_rows.append({
                            "model_name": mr.get("model_name", ""),
                            "accuracy": f"{acc:.1%}" if isinstance(acc, float) else "-",
                            "samples": str(storage_stats.get("samples_stored", mr.get("total_samples", "-"))),
                            "exec_time": f"{mr.get('execution_time', 0):.0f}s" if mr.get("execution_time") else "-",
                        })
                    storage_errors = storage_stats.get("errors") or []

                    # Parse request_payload for model configs, sample scale, category labels
                    rp = task_data.get("request_payload") or {}
                    if task_id == self.selected_task_id and rp:
                        rp_models = rp.get("models") or []
                        self.selected_task_models = [
                            {
                                "name": m.get("name", ""),
                                "api_base": m.get("api_base", ""),
                                "model_type": m.get("model_type", ""),
                            }
                            for m in rp_models
                        ]
                        self.selected_task_sample_scale = rp.get("sample_scale", "")
                        # Build category labels from the three suggest fields
                        cats = [
                            rp.get("category_language") or "",
                            rp.get("category_subject") or "",
                            rp.get("category_task_type") or "",
                        ]
                        self.selected_task_labels = [c for c in cats if c]

                    # Stage info from Celery PROGRESS meta
                    stage_label = task_data.get("stage", "")
                    stage_current = int(task_data.get("stage_current", 0))
                    stage_total = int(task_data.get("stage_total", 1) or 1)
                    stage_pct = int(stage_current / stage_total * 100) if stage_total else 0

                    # Store result details in dedicated state vars (for the selected task)
                    if task_id == self.selected_task_id:
                        self.selected_task_result_rows = result_rows
                        self.selected_task_error_msg = task_data.get("error_message") or ""
                        self.selected_task_completed_at = str(task_data.get("completed_at", "") or "")[:19].replace("T", " ")
                        if stage_label:
                            self.selected_task_stage = stage_label
                            self.selected_task_stage_pct = stage_pct
                        elif normalized_status == "completed":
                            self.selected_task_stage = "Evaluation complete"
                            self.selected_task_stage_pct = 100
                        elif normalized_status == "failed":
                            self.selected_task_stage = "Evaluation failed"
                            self.selected_task_stage_pct = 0

                    for i, task in enumerate(self.task_history):
                        if task["id"] == task_id:
                            if normalized_status == "completed":
                                progress = 100
                            elif normalized_status == "pending":
                                progress = 5
                            elif normalized_status == "running":
                                progress = max(10, stage_pct) if stage_pct else max(10, task.get("progress", 10))
                            else:
                                progress = task.get("progress", 0)

                            self.task_history[i].update(
                                {
                                    "status": normalized_status,
                                    "progress": progress,
                                    "created_at": task_data.get(
                                        "created_at", task.get("created_at")
                                    ),
                                }
                            )
                            break
        except Exception as e:
            print(f"Error refreshing task status: {e}")

    async def refresh_current_task(self):
        if not self.is_authenticated:
            return rx.toast.error("Please log in to view task status")
        if self.current_task_id:
            return await self.refresh_task_status(self.current_task_id)
        if self.task_history:
            return await self.refresh_task_status(self.task_history[0].get("id"))
        return rx.toast.info("No tasks to refresh.")

    async def _load_tasks_from_backend(self):
        """Load task history from backend API."""
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                params: dict = {"page_size": 10}
                if self.user_id:
                    params["user_id"] = self.user_id
                response = await client.get(
                    f"{self.api_base_url}/api/v1/tasks",
                    params=params,
                    headers=self._auth_headers(),
                )
            if response.status_code == 200:
                data = response.json()
                tasks = data.get("tasks", [])
                self.task_history = [
                    {
                        "id": t.get("task_id", ""),
                        "status": self._normalize_task_status(t.get("status")),
                        "progress": 100 if self._normalize_task_status(t.get("status")) == "completed" else 0,
                        "model_name": f"{t.get('model_count', 0)} model(s)",
                        "query": (
                            t.get("query")
                            or ", ".join(t.get("policy_tags", []))
                            or "Evaluation task"
                        ),
                        "created_at": str(t.get("created_at", ""))[:19].replace("T", " "),
                        "estimated_time": "-",
                    }
                    for t in tasks
                ]
        except Exception as e:
            print(f"Failed to load tasks from backend: {e}")

    # =====================================================================
    # Leaderboard
    # =====================================================================

    async def load_leaderboard_categories(self):
        if not self.is_authenticated:
            return rx.toast.error("Please log in to browse leaderboards")
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/leaderboard/categories",
                    headers=self._auth_headers(),
                )
            if response.status_code == 200:
                data = response.json()
                self.leaderboard_language_options = self._normalize_option_list(
                    data.get("languages", [])
                )
                self.leaderboard_subject_options = self._normalize_option_list(
                    data.get("subject_types", [])
                )
                self.leaderboard_task_type_options = self._normalize_option_list(
                    data.get("task_types", [])
                )
                return
            detail = response.json().get("detail", "Failed to load categories")
            return rx.toast.error(detail)
        except Exception as e:
            return rx.toast.error(f"Failed to load categories: {e}")

    async def suggest_leaderboard_filters(self):
        """Use planner agent to suggest filters from natural language query."""
        if not self.is_authenticated:
            return rx.toast.error("Please log in to use planner filters")
        if not self.leaderboard_query.strip():
            return rx.toast.error("Please enter a query")

        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/leaderboard/suggest",
                    json={"query": self.leaderboard_query},
                    headers=self._auth_headers(),
                )

            if response.status_code != 200:
                try:
                    detail = response.json().get("detail", "Failed to suggest filters")
                except Exception:
                    detail = response.text or "Failed to suggest filters"
                self.leaderboard_suggest_error = detail
                return rx.toast.error(detail)

            data = response.json()
            language = data.get("language") or "All"
            subject_type = data.get("subject_type") or "All"
            task_type = data.get("task_type") or "All"

            subject_options = data.get("subject_type_options") or []
            if subject_options:
                self.leaderboard_subject_options = self._normalize_option_list(
                    subject_options
                )

            self.leaderboard_language_options = self._ensure_option(
                self.leaderboard_language_options,
                language if language != "All" else None,
            )
            self.leaderboard_subject_options = self._ensure_option(
                self.leaderboard_subject_options,
                subject_type if subject_type != "All" else None,
            )
            self.leaderboard_task_type_options = self._ensure_option(
                self.leaderboard_task_type_options,
                task_type if task_type != "All" else None,
            )

            self.language_filter = language
            self.subject_filter = subject_type
            self.task_type_filter = task_type

            self.leaderboard_plan_summary = data.get("plan_summary") or ""
            self.leaderboard_used_planner = bool(data.get("used_planner"))
            self.leaderboard_confidence = float(data.get("confidence") or 0.0)
            self.leaderboard_rationale = data.get("rationale") or ""
            metadata = data.get("metadata") or {}
            self.leaderboard_is_off_topic = metadata.get("reason") == "off_topic"
            self.leaderboard_suggest_error = ""
            self.leaderboard_last_suggested = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            if self.leaderboard_is_off_topic:
                return
            return await self.load_leaderboard_data()
        except Exception as e:
            self.leaderboard_suggest_error = str(e)
            return rx.toast.error(f"Planner request failed: {e}")

    async def load_leaderboard_data(self):
        if not self.is_authenticated:
            return rx.toast.error("Please log in to browse leaderboards")
        self.leaderboard_loading = True
        try:
            if (
                len(self.leaderboard_language_options) <= 1
                or len(self.leaderboard_subject_options) <= 1
                or len(self.leaderboard_task_type_options) <= 1
            ):
                await self.load_leaderboard_categories()

            limit = self._clamp_limit(self.max_results)
            params = {
                "language": self._coerce_filter_value(self.language_filter),
                "subject_type": self._coerce_filter_value(self.subject_filter),
                "task_type": self._coerce_filter_value(self.task_type_filter),
                "limit": limit,
            }
            params = {k: v for k, v in params.items() if v is not None}

            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/leaderboard/browse",
                    params=params,
                    headers=self._auth_headers(),
                )

                if response.status_code == 200:
                    data = response.json()
                    entries = data.get("entries", [])
                    rows = []
                    for idx, entry in enumerate(entries, start=1):
                        score = entry.get("score")
                        score_label = (
                            f"{score:.2f}"
                            if isinstance(score, (int, float))
                            else str(score or "-")
                        )
                        rows.append(
                            {
                                "rank": idx,
                                "model": entry.get("model_name") or "-",
                                "score": score,
                                "score_label": score_label,
                                "language": entry.get("language") or "-",
                                "subject": entry.get("subject_type") or "-",
                                "task_type": entry.get("task_type") or "-",
                                "updated_at": entry.get("last_updated") or "-",
                            }
                        )

                    self.leaderboard_entries = rows
                    self.leaderboard_query_description = data.get("query") or ""
                    if not rows:
                        return rx.toast.info("No leaderboard entries for those filters")
                    return rx.toast.success("Leaderboard updated")
                try:
                    detail = response.json().get("detail", "Failed to load leaderboard")
                except Exception:
                    detail = response.text or "Failed to load leaderboard"
                return rx.toast.error(detail)

        except Exception as e:
            print(f"Error loading leaderboard: {e}")
            return rx.toast.error(f"Error loading leaderboard: {e}")
        finally:
            self.leaderboard_loading = False

    # =====================================================================
    # Manager dashboard
    # =====================================================================

    async def refresh_manager_snapshot(self):
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/manager/snapshot",
                    headers=self._auth_headers(),
                )
                if response.status_code != 200:
                    if response.status_code in (401, 403):
                        return self._handle_auth_failure(
                            "Please log in as an admin to access Manager."
                        )
                    detail = response.json().get("detail", "Failed to load snapshot")
                    return rx.toast.error(detail)

                data = response.json()
                health_raw = data.get("health", {})
                self.manager_health = {
                    k: v.get("status", "unknown") for k, v in health_raw.items()
                }
                self.manager_capacity = data.get("capacity", {})

                tasks = []
                for item in data.get("tasks", []):
                    duration_label = self._format_duration(item.get("duration_seconds"))
                    tasks.append(
                        {
                            "id": item.get("task_id"),
                            "status": item.get("status"),
                            "query": item.get("query") or "N/A",
                            "models_label": f"Models: {item.get('model_count') or '-'}",
                            "submitted_at": str(item.get("submitted_at")),
                            "duration": duration_label,
                            "duration_label": f"Duration: {duration_label}",
                        }
                    )
                self.manager_tasks = tasks

                leaderboard = []
                for idx, entry in enumerate(data.get("leaderboard", []), start=1):
                    leaderboard.append(
                        {
                            "id": entry.get("id"),
                            "rank": idx,
                            "model": entry.get("model_name"),
                            "language": entry.get("language"),
                            "subject": entry.get("subject_type"),
                            "task_type": entry.get("task_type"),
                            "score": entry.get("score"),
                        }
                    )
                self.manager_leaderboard = leaderboard
                self.manager_last_updated = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                self.manager_snapshot_loaded = True
                return rx.toast.success("Snapshot updated")
        except httpx.HTTPStatusError as e:
            return rx.toast.error(f"Snapshot error: {e.response.text}")
        except Exception as e:
            return rx.toast.error(f"Snapshot failed: {e}")

    def update_manager_task_status(self, task_id: str, status: str):
        updated_tasks = []
        for task in self.manager_tasks:
            if task["id"] == task_id:
                updated = task.copy()
                updated["status"] = status
                updated_tasks.append(updated)
            else:
                updated_tasks.append(task)
        self.manager_tasks = updated_tasks

    def remove_manager_task(self, task_id: str):
        self.manager_tasks = [t for t in self.manager_tasks if t["id"] != task_id]

    async def manager_patch_task(self, task_id: str, action: str):
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.patch(
                    f"{self.api_base_url}/api/v1/tasks/{task_id}",
                    json={"action": action},
                    headers=self._auth_headers(),
                )
                if response.status_code >= 300:
                    if response.status_code in (401, 403):
                        return self._handle_auth_failure(
                            "Session expired. Please log in again."
                        )
                    detail = response.json().get("detail", "Failed to update task")
                    return rx.toast.error(detail)
                await self.refresh_manager_snapshot()
                return rx.toast.success(f"Task {task_id} updated: {action}")
        except Exception as e:
            return rx.toast.error(f"Task update failed: {e}")

    def update_manager_new_entry(self, field: str, value: str):
        updated = self.manager_new_entry.copy()
        updated[field] = value
        self.manager_new_entry = updated

    def _recalculate_leaderboard(self, entries: List[Dict[str, Any]]):
        sorted_entries = sorted(entries, key=lambda item: item["score"], reverse=True)
        for idx, entry in enumerate(sorted_entries, start=1):
            entry["rank"] = idx
        self.manager_leaderboard = sorted_entries

    async def add_manager_leaderboard_entry(self):
        payload = self.manager_new_entry
        if not payload["model"] or not payload["score"]:
            return rx.toast.error("Model name and score are required")
        try:
            score_value = float(payload["score"])
        except ValueError:
            return rx.toast.error("Score must be numeric")

        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/leaderboard/entries",
                    json={
                        "model_name": payload["model"],
                        "language": payload.get("language", ""),
                        "subject_type": payload.get("subject", ""),
                        "task_type": payload.get("task_type", ""),
                        "score": score_value,
                    },
                    headers=self._auth_headers(),
                )
                if response.status_code >= 300:
                    if response.status_code in (401, 403):
                        return self._handle_auth_failure(
                            "Session expired. Please log in again."
                        )
                    detail = response.json().get("detail", "Failed to save entry")
                    return rx.toast.error(detail)

                self.manager_new_entry = {
                    "model": "",
                    "language": "",
                    "subject": "",
                    "task_type": "",
                    "score": "",
                }
                await self.refresh_manager_snapshot()
                return rx.toast.success("Entry saved")
        except Exception as e:
            return rx.toast.error(f"Failed to save entry: {e}")

    async def remove_manager_leaderboard_entry(self, entry_id: str):
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.delete(
                    f"{self.api_base_url}/api/v1/leaderboard/entries/{entry_id}",
                    headers=self._auth_headers(),
                )
                if response.status_code >= 300:
                    if response.status_code in (401, 403):
                        return self._handle_auth_failure(
                            "Session expired. Please log in again."
                        )
                    detail = response.json().get("detail", "Failed to delete entry")
                    return rx.toast.error(detail)
                await self.refresh_manager_snapshot()
                return rx.toast.info("Entry removed")
        except Exception as e:
            return rx.toast.error(f"Failed to delete entry: {e}")
