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
    auth_checked: bool = False
    auth_error: str = ""
    dev_login_value: str = "dev@local"

    # -- Navigation -------------------------------------------------------
    current_page: str = "evaluation"

    # -- Task management --------------------------------------------------
    task_history: List[Dict[str, Any]] = []
    current_task_id: Optional[str] = None

    # -- Model / evaluation configuration ---------------------------------
    models: List[Dict[str, Any]] = []
    num_models: int = 2
    query: str = ""
    sample_scale: str = "medium"
    current_results: Optional[Dict[str, Any]] = None
    is_loading: bool = False
    is_submitting: bool = False

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
        self.current_page = page

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

    def set_sample_scale(self, value: str):
        self.sample_scale = value

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
                self.user_picture = data.get("picture", "")
                self.user_role = data.get("role") or ""
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
            payload = {
                "query": self.query,
                "models": [
                    {
                        "name": m["name"],
                        "api_base": m.get("api_base", ""),
                        "api_key": m["api_key"],
                        "model_type": m["model_type"],
                    }
                    for m in self.models
                ],
                "sample_scale": self.sample_scale,
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

                    new_task = {
                        "id": task_id,
                        "status": normalized_status,
                        "progress": 100 if normalized_status == "completed" else 0,
                        "model_name": ", ".join([m["name"] for m in self.models]),
                        "query": self.query,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "estimated_time": result.get("estimated_duration", "Unknown"),
                    }

                    self.task_history = [new_task] + self.task_history
                    self.current_task_id = task_id
                    self.current_page = "status"

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

                    for i, task in enumerate(self.task_history):
                        if task["id"] == task_id:
                            progress = task.get("progress", 0)
                            if normalized_status == "completed":
                                progress = 100
                            elif normalized_status == "pending":
                                progress = 0
                            elif normalized_status == "running" and progress == 0:
                                progress = 50

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
                response = await client.get(
                    f"{self.api_base_url}/api/v1/tasks",
                    params={"page_size": 50},
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
                        "query": ", ".join(t.get("policy_tags", [])) or "Evaluation task",
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
