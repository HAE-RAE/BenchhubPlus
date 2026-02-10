"""BenchHub Plus - Reflex Frontend Application."""

import reflex as rx
from typing import List, Dict, Any, Optional
import httpx
import asyncio
import json
from datetime import datetime
import os

from rxconfig import config

# API Configuration
DEFAULT_API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
PUBLIC_API_BASE = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8001")
API_TIMEOUT = 30


class AppState(rx.State):
    """Main application state for BenchHub Plus."""
    
    # API Configuration
    api_base_url: str = DEFAULT_API_BASE
    access_token: str = os.getenv("MANAGER_TOKEN", "")
    dev_auth_bypass: bool = os.getenv("DEV_AUTH_BYPASS", "").lower() in {"1", "true", "yes"}

    # --- Auth state ---
    is_authenticated: bool = False
    user_email: str = ""
    user_name: str = ""
    user_picture: str = ""
    user_role: str = ""
    auth_checked: bool = False
    auth_error: str = ""
    dev_login_value: str = "dev@local"

    # Current page
    current_page: str = "evaluation"
    
    # Task management
    task_history: List[Dict[str, Any]] = [
        {
            "id": "task_001",
            "status": "running",
            "progress": 75,
            "model_name": "GPT-4",
            "query": "Korean math problems evaluation",
            "created_at": "2024-11-17 10:30:00",
            "estimated_time": "5 minutes"
        },
        {
            "id": "task_002", 
            "status": "completed",
            "progress": 100,
            "model_name": "Claude-3",
            "query": "Text summarization benchmark",
            "created_at": "2024-11-17 09:15:00",
            "estimated_time": "3 minutes"
        },
        {
            "id": "task_003",
            "status": "pending",
            "progress": 0,
            "model_name": "Llama-2",
            "query": "Code generation test",
            "created_at": "2024-11-17 11:00:00",
            "estimated_time": "8 minutes"
        }
    ]
    current_task_id: Optional[str] = None
    
    # Model configuration
    models: List[Dict[str, Any]] = []
    num_models: int = 2
    
    # Evaluation form
    query: str = ""
    
    # Results
    current_results: Optional[Dict[str, Any]] = None
    
    # Loading states
    is_loading: bool = False
    is_submitting: bool = False
    
    # Leaderboard filters
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
    leaderboard_suggest_error: str = ""
    leaderboard_last_suggested: Optional[str] = None
    leaderboard_language_options: List[str] = ["All"]
    leaderboard_subject_options: List[str] = ["All"]
    leaderboard_task_type_options: List[str] = ["All"]

    # Manager dashboard state (front-end only snapshot)
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
    
    def set_page(self, page: str):
        """Set the current page."""
        self.current_page = page
    
    def set_language_filter(self, value: str):
        """Set the language filter."""
        self.language_filter = value
    
    def set_subject_filter(self, value: str):
        """Set the subject filter."""
        self.subject_filter = value
    
    def set_task_type_filter(self, value: str):
        """Set the task type filter."""
        self.task_type_filter = value
    
    def set_max_results(self, value: str):
        """Set the max results."""
        try:
            self.max_results = int(value)
        except ValueError:
            self.max_results = 100

    def set_leaderboard_query(self, value: str):
        """Set the leaderboard natural language filter query."""
        self.leaderboard_query = value

    def set_access_token(self, value: str):
        """Set the auth token (e.g., from query param)."""
        self.access_token = value

    def set_dev_login_value(self, value: str):
        """Set dev login input value."""
        self.dev_login_value = value

    def _auth_headers(self) -> Dict[str, str]:
        """Build authorization headers if token is available."""
        headers: Dict[str, str] = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _handle_auth_failure(self, message: str):
        """Reset auth state and surface a message to the user."""
        self.is_authenticated = False
        self.access_token = ""
        self.user_email = ""
        self.user_name = ""
        self.user_picture = ""
        self.user_role = ""
        self.auth_error = message
        return rx.toast.error(message)

    def _format_duration(self, seconds: float) -> str:
        """Format duration seconds into label."""
        if seconds is None:
            return "-"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if minutes == 0:
            return f"{secs}s"
        return f"{minutes}m {secs}s"

    def _normalize_task_status(self, status: Optional[str]) -> str:
        """Normalize API status labels to UI-friendly values."""
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

    @rx.var
    def total_task_count(self) -> int:
        """Total number of tasks in history."""
        return len(self.task_history)

    @rx.var
    def running_task_count(self) -> int:
        """Count of running tasks."""
        return sum(1 for task in self.task_history if task.get("status") == "running")

    @rx.var
    def completed_task_count(self) -> int:
        """Count of completed tasks."""
        return sum(1 for task in self.task_history if task.get("status") == "completed")

    @rx.var
    def pending_task_count(self) -> int:
        """Count of pending tasks."""
        return sum(1 for task in self.task_history if task.get("status") == "pending")

    @rx.var
    def is_admin_user(self) -> bool:
        """Check if the current user is an admin."""
        return bool(self.is_authenticated and self.user_role == "admin")
        
    # ----- Auth / Session helpers -----
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
            return self._handle_auth_failure("Authentication failed. Please log in again.")

        self.auth_checked = True

    async def start_google_login(self):
        if self.dev_auth_bypass:
            return rx.toast.info("Use the dev login input to sign in.")
        return rx.redirect(f"{PUBLIC_API_BASE}/api/v1/auth/google/login")

    async def dev_login(self):
        """Development-only login using a simple input."""
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
        """Logout locally by clearing auth state and reloading the app."""
        self.access_token = ""
        self.is_authenticated = False
        self.user_email = ""
        self.user_name = ""
        self.user_picture = ""
        self.user_role = ""
        self.auth_error = ""

        return rx.redirect(path="/")

    # ----- Manager dashboard helpers -----
    async def refresh_manager_snapshot(self):
        """Fetch snapshot from backend manager API."""
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/manager/snapshot",
                    headers=self._auth_headers(),
                )
                if response.status_code != 200:
                    if response.status_code in (401, 403):
                        return self._handle_auth_failure("Please log in as an admin to access Manager.")
                    detail = response.json().get("detail", "Failed to load snapshot")
                    return rx.toast.error(detail)

                data = response.json()
                health_raw = data.get("health", {})
                self.manager_health = {k: v.get("status", "unknown") for k, v in health_raw.items()}
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
                self.manager_last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.manager_snapshot_loaded = True
                return rx.toast.success("Snapshot updated")
        except httpx.HTTPStatusError as e:
            return rx.toast.error(f"Snapshot error: {e.response.text}")
        except Exception as e:
            return rx.toast.error(f"Snapshot failed: {e}")

    def update_manager_task_status(self, task_id: str, status: str):
        """Update a task inside the mock queue."""
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
        """Delete a task from the mock queue."""
        self.manager_tasks = [task for task in self.manager_tasks if task["id"] != task_id]

    async def manager_patch_task(self, task_id: str, action: str):
        """Call backend to control a task."""
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.patch(
                    f"{self.api_base_url}/api/v1/tasks/{task_id}",
                    json={"action": action},
                    headers=self._auth_headers(),
                )
                if response.status_code >= 300:
                    if response.status_code in (401, 403):
                        return self._handle_auth_failure("Session expired. Please log in again.")
                    detail = response.json().get("detail", "Failed to update task")
                    return rx.toast.error(detail)
                await self.refresh_manager_snapshot()
                return rx.toast.success(f"Task {task_id} updated: {action}")
        except Exception as e:
            return rx.toast.error(f"Task update failed: {e}")

    def update_manager_new_entry(self, field: str, value: str):
        """Update leaderboard entry draft state."""
        updated = self.manager_new_entry.copy()
        updated[field] = value
        self.manager_new_entry = updated

    def _recalculate_leaderboard(self, entries: List[Dict[str, Any]]):
        """Sort entries and recalculate ranks."""
        sorted_entries = sorted(entries, key=lambda item: item["score"], reverse=True)
        for idx, entry in enumerate(sorted_entries, start=1):
            entry["rank"] = idx
        self.manager_leaderboard = sorted_entries

    async def add_manager_leaderboard_entry(self):
        """Add an entry to the backend leaderboard (admin)."""
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
                        return self._handle_auth_failure("Session expired. Please log in again.")
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
        """Remove an entry by ID via backend."""
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.delete(
                    f"{self.api_base_url}/api/v1/leaderboard/entries/{entry_id}",
                    headers=self._auth_headers(),
                )
                if response.status_code >= 300:
                    if response.status_code in (401, 403):
                        return self._handle_auth_failure("Session expired. Please log in again.")
                    detail = response.json().get("detail", "Failed to delete entry")
                    return rx.toast.error(detail)
                await self.refresh_manager_snapshot()
                return rx.toast.info("Entry removed")
        except Exception as e:
            return rx.toast.error(f"Failed to delete entry: {e}")

    def add_model(self):
        """Add a new model configuration."""
        self.models.append({
            "name": f"model_{len(self.models) + 1}",
            "api_base": "https://api.openai.com/v1",
            "api_key": "",
            "model_type": "openai"
        })
    
    def remove_model(self, index: int):
        """Remove a model configuration."""
        if 0 <= index < len(self.models):
            self.models.pop(index)
    
    def update_model(self, index: int, field: str, value: str):
        """Update a model configuration field."""
        if 0 <= index < len(self.models):
            self.models[index][field] = value
    
    def set_query(self, value: str):
        """Set the evaluation query."""
        self.query = value
    
    async def submit_evaluation(self):
        """Submit evaluation request to backend API."""
        if not self.is_authenticated:
            return rx.toast.error("Please log in to start an evaluation")
        if not self.query.strip():
            return rx.toast.error("Please enter a query")
        
        if not self.models:
            return rx.toast.error("Please add at least one model")
        
        # Validate models
        for model in self.models:
            if not model.get("name") or not model.get("api_key") or not model.get("api_base"):
                return rx.toast.error("Please fill in all model fields")
        
        self.is_submitting = True
        
        try:
            # Prepare API request
            payload = {
                "query": self.query,
                "models": [
                    {
                        "name": model["name"],
                        "api_base": model.get("api_base", ""),
                        "api_key": model["api_key"],
                        "model_type": model["model_type"],
                    }
                    for model in self.models
                ]
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
                    
                    # Add task to history
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
                        error_msg = error_payload.get("detail") or error_payload.get("message") or "Unknown error"
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
        """Refresh status of a specific task."""
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
                    
                    # Update task in history
                    for i, task in enumerate(self.task_history):
                        if task["id"] == task_id:
                            progress = task.get("progress", 0)
                            if normalized_status == "completed":
                                progress = 100
                            elif normalized_status == "pending":
                                progress = 0
                            elif normalized_status == "running" and progress == 0:
                                progress = 50

                            self.task_history[i].update({
                                "status": normalized_status,
                                "progress": progress,
                                "created_at": task_data.get("created_at", task.get("created_at")),
                            })
                            break
                            
        except Exception as e:
            print(f"Error refreshing task status: {e}")

    async def refresh_current_task(self):
        """Refresh status for the most recent task."""
        if not self.is_authenticated:
            return rx.toast.error("Please log in to view task status")
        if self.current_task_id:
            return await self.refresh_task_status(self.current_task_id)
        if self.task_history:
            return await self.refresh_task_status(self.task_history[0].get("id"))
        return rx.toast.info("No tasks to refresh.")

    def _normalize_option_list(self, values: List[Any]) -> List[str]:
        """Normalize category options into unique list with 'All'."""
        options: List[str] = ["All"]
        for value in values or []:
            if value is None:
                continue
            cleaned = str(value).strip()
            if cleaned and cleaned not in options:
                options.append(cleaned)
        return options

    def _ensure_option(self, options: List[str], value: Optional[str]) -> List[str]:
        """Ensure a suggested value exists in option list."""
        if value and value not in options:
            return options + [value]
        return options

    def _coerce_filter_value(self, value: str) -> Optional[str]:
        """Convert 'All' to None for API calls."""
        if not value or value == "All":
            return None
        return value

    def _clamp_limit(self, value: int) -> int:
        """Clamp leaderboard limit to API bounds."""
        if value < 1:
            return 1
        if value > 1000:
            return 1000
        return value

    async def load_leaderboard_categories(self):
        """Load distinct category options for filters."""
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
                self.leaderboard_subject_options = self._normalize_option_list(subject_options)

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
            self.leaderboard_suggest_error = ""
            self.leaderboard_last_suggested = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return await self.load_leaderboard_data()
        except Exception as e:
            self.leaderboard_suggest_error = str(e)
            return rx.toast.error(f"Planner request failed: {e}")
    
    async def load_leaderboard_data(self):
        """Load leaderboard data from backend using current filters."""
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
                            f"{score:.2f}" if isinstance(score, (int, float)) else str(score or "-")
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


def header() -> rx.Component:
    """Main header component."""
    user_info = rx.cond(
        AppState.is_authenticated,
        rx.popover.root(
            rx.popover.trigger(
                rx.avatar(
                    src=AppState.user_picture,
                    fallback=AppState.user_name,
                    size="2",
                    cursor="pointer",
                ),
                as_child=True, 
            ),
            rx.popover.content(
                rx.vstack(
                    rx.text(
                        rx.cond(AppState.user_name != "", AppState.user_name, "Logged in"),
                        weight="bold",
                        size="2",
                    ),
                    rx.cond(
                        AppState.user_email != "",
                        rx.text(AppState.user_email, size="1", color="gray"),
                        rx.fragment(),
                    ),
                    align="start",
                    spacing="1",
                ),
                side="bottom",
                align="end",
                padding="0.75rem",
                width="240px",
            ),
        ),
        rx.fragment(),
    )

    dev_login_controls = rx.hstack(
        rx.input(
            placeholder="dev email",
            value=AppState.dev_login_value,
            on_change=AppState.set_dev_login_value,
            width="200px",
            size="2",
        ),
        rx.button(
            "Dev Login",
            variant="solid",
            color_scheme="blue",
            size="2",
            on_click=AppState.dev_login,
        ),
        spacing="2",
        align="center",
    )

    auth_button = rx.cond(
        AppState.is_authenticated,
        rx.button(
            "Logout??",
            variant="outline",
            color_scheme="blue",
            size="2",
            on_click=AppState.logout,
        ),
        rx.cond(
            AppState.dev_auth_bypass,
            dev_login_controls,
            rx.button(
                "Login??",
                variant="solid",
                color_scheme="blue",
                size="2",
                on_click=AppState.start_google_login,
            ),
        ),
    )

    right_controls = rx.vstack(
        rx.hstack(
            rx.spacer(),
            rx.color_mode.button(),
            width="100%",
            justify="end",
            align="center",
        ),
        rx.hstack(
            user_info,
            auth_button,
            spacing="3",
            align="center",
            justify="end",
            width="100%",
        ),
        spacing="1",
        align="end",
        width="320px",
    )

    return rx.box(
        rx.hstack(
            rx.box(width="320px"),
            rx.spacer(),
            rx.heading(
                "🏆 BenchHub Plus",
                size="8",
                color="transparent",
                background="linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
                background_clip="text",
            ),
            rx.spacer(),
            right_controls,
            width="100%",
            align="center",
            padding="1rem",
        ),
        rx.text(
            "Interactive Leaderboard System for Dynamic LLM Evaluation",
            size="4",
            color="gray",
            text_align="center",
            margin_bottom="2rem",
        ),
        rx.cond(
            AppState.auth_error != "",
            rx.card(
                rx.text(AppState.auth_error, color="red", size="2"),
                background="rgba(254, 226, 226, 0.9)",
                border="1px solid rgba(248, 113, 113, 0.6)",
                padding="0.75rem",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.divider(),
        width="100%",
        margin_bottom="2rem",
    )


def navigation() -> rx.Component:
    """Navigation component."""
    return rx.hstack(
        rx.button(
            "📝 Evaluation",
            on_click=lambda: AppState.set_page("evaluation"),
            variant=rx.cond(AppState.current_page == "evaluation", "solid", "outline"),
            color_scheme="blue",
        ),
        rx.button(
            "📊 Status",
            on_click=lambda: AppState.set_page("status"),
            variant=rx.cond(AppState.current_page == "status", "solid", "outline"),
            color_scheme="blue",
        ),
        rx.button(
            "🏅 Leaderboard",
            on_click=lambda: AppState.set_page("leaderboard"),
            variant=rx.cond(AppState.current_page == "leaderboard", "solid", "outline"),
            color_scheme="blue",
        ),
        rx.button(
            "🛠 Manager (Admin)",
            on_click=lambda: AppState.set_page("manager"),
            variant=rx.cond(AppState.current_page == "manager", "solid", "outline"),
            color_scheme="blue",
            disabled=rx.cond(AppState.is_admin_user, False, True),
        ),
        spacing="4",
        justify="center",
        margin_bottom="2rem",
    )




def login_required_card(message: str) -> rx.Component:
    """Shared login required callout."""
    return rx.card(
        rx.vstack(
            rx.heading("Login required", size="5"),
            rx.text(message, color="gray"),
            rx.cond(
                AppState.dev_auth_bypass,
                rx.hstack(
                    rx.input(
                        placeholder="dev email",
                        value=AppState.dev_login_value,
                        on_change=AppState.set_dev_login_value,
                        width="220px",
                        size="2",
                    ),
                    rx.button(
                        "Dev Login",
                        on_click=AppState.dev_login,
                        color_scheme="blue",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.button(
                    "Login",
                    on_click=AppState.start_google_login,
                    color_scheme="blue",
                ),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        width="100%",
    )

def model_form(index: rx.Var[int]) -> rx.Component:
    """Individual model configuration form."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Model Configuration", size="4"),
                rx.spacer(),
                rx.button(
                    "Remove",
                    on_click=lambda: AppState.remove_model(index),
                    variant="outline",
                    color_scheme="red",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            
            rx.grid(
                rx.vstack(
                    rx.text("Model Name", weight="bold", size="2"),
                    rx.input(
                        placeholder="model_name",
                        value=AppState.models[index]["name"],
                        on_change=lambda value: AppState.update_model(index, "name", value),
                        width="100%",
                    ),
                    align="start",
                    width="100%",
                ),
                
                rx.vstack(
                    rx.text("Model Type", weight="bold", size="2"),
                    rx.select(
                        ["openai", "anthropic", "huggingface", "custom"],
                        value=AppState.models[index]["model_type"],
                        on_change=lambda value: AppState.update_model(index, "model_type", value),
                        width="100%",
                    ),
                    align="start",
                    width="100%",
                ),
                
                rx.vstack(
                    rx.text("API Base URL", weight="bold", size="2"),
                    rx.input(
                        placeholder="https://api.openai.com/v1",
                        value=AppState.models[index]["api_base"],
                        on_change=lambda value: AppState.update_model(index, "api_base", value),
                        width="100%",
                    ),
                    align="start",
                    width="100%",
                ),
                
                rx.vstack(
                    rx.text("API Key", weight="bold", size="2"),
                    rx.input(
                        placeholder="Enter API key",
                        type="password",
                        value=AppState.models[index]["api_key"],
                        on_change=lambda value: AppState.update_model(index, "api_key", value),
                        width="100%",
                    ),
                    align="start",
                    width="100%",
                ),
                
                columns="2",
                spacing="4",
                width="100%",
            ),
            
            align="start",
            spacing="3",
            width="100%",
        ),
        width="100%",
        margin_bottom="1rem",
    )


def evaluation_page() -> rx.Component:
    """Evaluation request page."""
    return rx.cond(
        AppState.is_authenticated,
        rx.vstack(
        rx.heading("📝 Evaluation Request", size="6", margin_bottom="1rem"),
        
        # Query input
        rx.vstack(
            rx.text("Natural Language Query", weight="bold"),
            rx.text_area(
                placeholder="Compare these models on Korean math problems for high school students",
                value=AppState.query,
                on_change=AppState.set_query,
                height="100px",
                width="100%",
            ),
            rx.text(
                "Describe what you want to evaluate in natural language",
                size="2",
                color="gray",
            ),
            width="100%",
            align="start",
            margin_bottom="2rem",
        ),
        
        # Model configuration section
        rx.vstack(
            rx.hstack(
                rx.heading("🤖 Model Configuration", size="5"),
                rx.spacer(),
                rx.button(
                    "Add Model",
                    on_click=AppState.add_model,
                    variant="outline",
                    size="2",
                    disabled=rx.cond(AppState.models.length() >= 10, True, False),
                ),
                width="100%",
                align="center",
            ),
            
            # Model forms
            rx.cond(
                AppState.models.length() > 0,
                rx.vstack(
                    rx.foreach(
                        rx.Var.range(AppState.models.length()),
                        model_form,
                    ),
                    width="100%",
                    spacing="2",
                ),
                rx.text(
                    "No models configured. Click 'Add Model' to get started.",
                    color="gray",
                    text_align="center",
                    padding="2rem",
                ),
            ),
            
            width="100%",
            align="start",
            margin_bottom="2rem",
        ),
        
        # Submit button
        rx.center(
            rx.button(
                "🚀 Start Evaluation",
                size="4",
                color_scheme="blue",
                loading=AppState.is_submitting,
                width="300px",
                disabled=rx.cond(
                    AppState.models.length() == 0,
                    True,
                    False,
                ),
                on_click=AppState.submit_evaluation,
            ),
            width="100%",
        ),
        
        width="100%",
        align="start",
        spacing="4",
    )

,
        login_required_card("Please log in to create a new evaluation."),
    )
def task_status_card(task: rx.Var[dict]) -> rx.Component:
    """Individual task status card."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    task["status"],
                    color_scheme=rx.cond(
                        task["status"] == "completed",
                        "green",
                        rx.cond(
                            task["status"] == "running",
                            "blue",
                            rx.cond(
                                task["status"] == "pending",
                                "orange",
                                "red"
                            )
                        )
                    ),
                    variant="solid",
                ),
                rx.spacer(),
                rx.text(task["created_at"], size="2", color="gray"),
                width="100%",
                align="center",
            ),
            
            rx.vstack(
                rx.text(task["query"], weight="bold", size="3"),
                rx.text(rx.text("Model: ", task["model_name"]), size="2", color="gray"),
                rx.text(rx.text("Task ID: ", task["id"]), size="1", color="gray"),
                align="start",
                spacing="1",
                width="100%",
            ),
            
            rx.cond(
                task["status"] == "running",
                rx.vstack(
                    rx.hstack(
                        rx.text("Progress", size="2"),
                        rx.spacer(),
                        rx.text(rx.text(task["progress"], "%"), size="2", weight="bold"),
                        width="100%",
                        align="center",
                    ),
                    rx.progress(
                        value=task["progress"],
                        width="100%",
                        color_scheme="blue",
                    ),
                    rx.text(rx.text("Estimated time: ", task["estimated_time"]), size="1", color="gray"),
                    width="100%",
                    spacing="2",
                ),
                rx.cond(
                    task["status"] == "completed",
                    rx.hstack(
                        rx.icon("check", color="green"),
                        rx.text("Evaluation completed successfully", size="2", color="green"),
                        align="center",
                    ),
                    rx.cond(
                        task["status"] == "pending",
                        rx.hstack(
                            rx.icon("clock", color="orange"),
                            rx.text("Waiting in queue", size="2", color="orange"),
                            align="center",
                        ),
                        rx.hstack(
                            rx.icon("x", color="red"),
                            rx.text("Task failed", size="2", color="red"),
                            align="center",
                        ),
                    ),
                ),
            ),
            
            align="start",
            spacing="3",
            width="100%",
        ),
        width="100%",
        margin_bottom="1rem",
    )


def status_page() -> rx.Component:
    """Task status monitoring page."""
    return rx.cond(
        AppState.is_authenticated,
        rx.vstack(
        rx.hstack(
            rx.heading("📊 Task Status", size="6"),
            rx.spacer(),
            rx.button(
                "Refresh Status",
                variant="outline",
                size="2",
                on_click=AppState.refresh_current_task,
                disabled=rx.cond(AppState.total_task_count == 0, True, False),
            ),
            width="100%",
            align="center",
            margin_bottom="1rem",
        ),
        
        # Summary stats
        rx.grid(
            rx.card(
                rx.vstack(
                    rx.text("Total Tasks", size="2", color="gray"),
                    rx.text(AppState.total_task_count, size="6", weight="bold"),
                    align="center",
                    spacing="1",
                ),
                width="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.text("Running", size="2", color="gray"),
                    rx.text(AppState.running_task_count, size="6", weight="bold", color="blue"),
                    align="center",
                    spacing="1",
                ),
                width="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.text("Completed", size="2", color="gray"),
                    rx.text(AppState.completed_task_count, size="6", weight="bold", color="green"),
                    align="center",
                    spacing="1",
                ),
                width="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.text("Pending", size="2", color="gray"),
                    rx.text(AppState.pending_task_count, size="6", weight="bold", color="orange"),
                    align="center",
                    spacing="1",
                ),
                width="100%",
            ),
            columns="4",
            spacing="4",
            width="100%",
            margin_bottom="2rem",
        ),
        
        # Task list
        rx.vstack(
            rx.heading("Recent Tasks", size="5", margin_bottom="1rem"),
            rx.cond(
                AppState.task_history.length() > 0,
                rx.vstack(
                    rx.foreach(
                        AppState.task_history,
                        task_status_card,
                    ),
                    width="100%",
                    spacing="2",
                ),
                rx.text(
                    "No tasks found. Start an evaluation to see task status here.",
                    color="gray",
                    text_align="center",
                    padding="2rem",
                ),
            ),
            width="100%",
            align="start",
        ),
        
        width="100%",
        align="start",
        spacing="4",
    )

,
        login_required_card("Please log in to view task status."),
    )
def leaderboard_table_row(entry: rx.Var[dict]) -> rx.Component:
    """Leaderboard row for browse table."""
    return rx.table.row(
        rx.table.cell(entry["rank"]),
        rx.table.cell(entry["model"]),
        rx.table.cell(entry["language"]),
        rx.table.cell(entry["subject"]),
        rx.table.cell(entry["task_type"]),
        rx.table.cell(
            rx.badge(entry["score_label"], color_scheme="blue", variant="solid")
        ),
        rx.table.cell(entry["updated_at"]),
    )


def leaderboard_page() -> rx.Component:
    """Leaderboard browsing page."""
    return rx.cond(
        AppState.is_authenticated,
        rx.vstack(
        rx.heading("?? Browse Leaderboards", size="6", margin_bottom="1rem"),
        
        # Leaderboard table
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading("Model Performance Rankings", size="4"),
                    rx.spacer(),
                    rx.button(
                        "Refresh",
                        size="2",
                        variant="outline",
                        on_click=AppState.load_leaderboard_data,
                        loading=AppState.leaderboard_loading,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    AppState.leaderboard_query_description != "",
                    rx.text(
                        AppState.leaderboard_query_description,
                        size="2",
                        color="gray",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AppState.leaderboard_entries.length() > 0,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Rank"),
                                rx.table.column_header_cell("Model"),
                                rx.table.column_header_cell("Language"),
                                rx.table.column_header_cell("Subject"),
                                rx.table.column_header_cell("Task Type"),
                                rx.table.column_header_cell("Score"),
                                rx.table.column_header_cell("Updated"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                AppState.leaderboard_entries,
                                leaderboard_table_row,
                            )
                        ),
                        width="100%",
                    ),
                    rx.center(
                        rx.text(
                            "No leaderboard data yet. Apply filters to load results.",
                            color="gray",
                        ),
                        padding="2rem",
                    ),
                ),
                
                align="start",
                spacing="3",
                width="100%",
            ),
            width="100%",
        ),
        
        # Filter and search section
        rx.card(
            rx.vstack(
                rx.heading("Filter Results", size="4", margin_bottom="1rem"),
                rx.vstack(
                    rx.text("Natural Language Filter", weight="bold", size="2"),
                    rx.text_area(
                        placeholder="Find models strong at Korean math reasoning",
                        value=AppState.leaderboard_query,
                        on_change=AppState.set_leaderboard_query,
                        height="90px",
                        width="100%",
                    ),
                    rx.text(
                        "Use the planning agent to suggest filters from your query.",
                        size="2",
                        color="gray",
                    ),
                    width="100%",
                    align="start",
                ),
                rx.hstack(
                    rx.button(
                        "Plan Filters",
                        size="3",
                        color_scheme="blue",
                        on_click=AppState.suggest_leaderboard_filters,
                        loading=AppState.leaderboard_loading,
                    ),
                    rx.button(
                        "Apply Filters",
                        size="3",
                        variant="outline",
                        on_click=AppState.load_leaderboard_data,
                        loading=AppState.leaderboard_loading,
                    ),
                    spacing="3",
                ),
                rx.cond(
                    AppState.leaderboard_plan_summary != "",
                    rx.vstack(
                        rx.text("Planned Filters", weight="bold", size="2"),
                        rx.text(AppState.leaderboard_plan_summary, size="2", color="gray"),
                        rx.text(
                            rx.text(
                                "Planner: ",
                                rx.cond(AppState.leaderboard_used_planner, "used", "fallback"),
                                " | Confidence: ",
                                AppState.leaderboard_confidence,
                            ),
                            size="1",
                            color="gray",
                        ),
                        rx.cond(
                            AppState.leaderboard_rationale != "",
                            rx.text(AppState.leaderboard_rationale, size="1", color="gray"),
                            rx.fragment(),
                        ),
                        width="100%",
                        align="start",
                        spacing="1",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AppState.leaderboard_suggest_error != "",
                    rx.text(AppState.leaderboard_suggest_error, size="1", color="red"),
                    rx.fragment(),
                ),
                
                rx.grid(
                    rx.vstack(
                        rx.text("Language", weight="bold", size="2"),
                        rx.select(
                            AppState.leaderboard_language_options,
                            value=AppState.language_filter,
                            on_change=AppState.set_language_filter,
                            width="100%",
                        ),
                        align="start",
                        width="100%",
                    ),
                    
                    rx.vstack(
                        rx.text("Subject", weight="bold", size="2"),
                        rx.select(
                            AppState.leaderboard_subject_options,
                            value=AppState.subject_filter,
                            on_change=AppState.set_subject_filter,
                            width="100%",
                        ),
                        align="start",
                        width="100%",
                    ),
                    
                    rx.vstack(
                        rx.text("Task Type", weight="bold", size="2"),
                        rx.select(
                            AppState.leaderboard_task_type_options,
                            value=AppState.task_type_filter,
                            on_change=AppState.set_task_type_filter,
                            width="100%",
                        ),
                        align="start",
                        width="100%",
                    ),
                    
                    rx.vstack(
                        rx.text("Max Results", weight="bold", size="2"),
                        rx.input(
                            value=AppState.max_results,
                            on_change=AppState.set_max_results,
                            type="number",
                            step=10,
                            width="100%",
                        ),
                        align="start",
                        width="100%",
                    ),
                    
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                
                align="start",
                spacing="3",
                width="100%",
            ),
            width="100%",
            margin_top="2rem",
        ),
        
        width="100%",
        align="start",
        spacing="4",
    )

,
        login_required_card("Please log in to browse leaderboards."),
    )
def manager_status_card(title: str, value: rx.Var[str], description: str = "") -> rx.Component:
    """Render subsystem status badges."""
    return rx.card(
        rx.vstack(
            rx.text(title, size="2", color="gray"),
            rx.badge(value, variant="solid", color_scheme="blue"),
            rx.cond(
                description != "",
                rx.text(description, size="1", color="gray"),
                rx.fragment()
            ),
            spacing="1",
            align="start",
        ),
        width="100%",
    )


def manager_capacity_card(title: str, value: rx.Var[Any], color: str) -> rx.Component:
    """Render KPI cards."""
    return rx.card(
        rx.vstack(
            rx.text(title, size="2", color="gray"),
            rx.text(value, size="6", weight="bold", color=color),
            spacing="1",
            align="start",
        ),
        width="100%",
    )


def manager_task_card(task: rx.Var[dict]) -> rx.Component:
    """Single task row with actions."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    task["status"],
                    color_scheme=rx.cond(
                        task["status"] == "SUCCESS",
                        "green",
                        rx.cond(
                            task["status"] == "FAILURE",
                            "red",
                            rx.cond(task["status"] == "STARTED", "blue", "orange")
                        )
                    ),
                    variant="solid",
                ),
                rx.spacer(),
                rx.text(task["submitted_at"], size="2", color="gray"),
                width="100%",
                align="center",
            ),
            rx.text(task["query"], weight="bold", size="3"),
            rx.text(task["models_label"], size="2", color="gray"),
            rx.text(task["duration_label"], size="2", color="gray"),
            rx.hstack(
                rx.button(
                    "Restart",
                    size="1",
                    variant="soft",
                    color_scheme="green",
                    on_click=lambda: AppState.manager_patch_task(task["id"], "restart"),
                ),
                rx.button(
                    "Hold",
                    size="1",
                    variant="soft",
                    color_scheme="orange",
                    on_click=lambda: AppState.manager_patch_task(task["id"], "hold"),
                ),
                rx.button(
                    "Cancel",
                    size="1",
                    variant="outline",
                    color_scheme="red",
                    on_click=lambda: AppState.manager_patch_task(task["id"], "cancel"),
                ),
                spacing="2",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def manager_health_section() -> rx.Component:
    """Health snapshot."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("🛡 Health & Capacity Snapshot", size="5"),
                rx.spacer(),
                rx.button(
                    "Refresh Snapshot",
                    variant="outline",
                    size="2",
                    on_click=AppState.refresh_manager_snapshot,
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                AppState.manager_last_updated != None,
                rx.text("Last updated: ", AppState.manager_last_updated, size="2", color="gray"),
                rx.text("Click refresh to load sample data", size="2", color="gray"),
            ),
            rx.cond(
                AppState.manager_snapshot_loaded,
                rx.vstack(
                    rx.grid(
                        manager_status_card("Database", AppState.manager_health["database"], "FastAPI ↔ PostgreSQL"),
                        manager_status_card("Redis", AppState.manager_health["redis"], "Celery broker/cache"),
                        manager_status_card("Planner", AppState.manager_health["planner"], "LLM plan agent"),
                        manager_status_card("HRET", AppState.manager_health["hret"], "Toolkit availability"),
                        columns="4",
                        spacing="4",
                        width="100%",
                    ),
                    rx.grid(
                        manager_capacity_card("Pending", AppState.manager_capacity["pending"], "orange"),
                        manager_capacity_card("Running", AppState.manager_capacity["running"], "blue"),
                        manager_capacity_card("Success", AppState.manager_capacity["success"], "green"),
                        manager_capacity_card("Failure", AppState.manager_capacity["failure"], "red"),
                        manager_capacity_card("Cache Entries", AppState.manager_capacity["cache_entries"], "purple"),
                        columns="5",
                        spacing="4",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.center(
                    rx.text("No snapshot loaded yet.", color="gray"),
                    padding="2rem",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def manager_tasks_section() -> rx.Component:
    """Task moderation."""
    return rx.card(
        rx.vstack(
            rx.heading("📋 Task Pipeline Control", size="5"),
            rx.text("Mark, remove, or inspect suspicious jobs.", size="2", color="gray"),
            rx.cond(
                AppState.manager_tasks.length() > 0,
                rx.vstack(
                    rx.foreach(
                        AppState.manager_tasks,
                        manager_task_card,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.center(
                    rx.text("No task data. Run the snapshot refresh.", color="gray"),
                    padding="2rem",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def manager_leaderboard_table_row(entry: rx.Var[dict]) -> rx.Component:
    """Leaderboard row with actions."""
    return rx.table.row(
        rx.table.cell(entry["rank"]),
        rx.table.cell(entry["model"]),
        rx.table.cell(entry["language"]),
        rx.table.cell(entry["subject"]),
        rx.table.cell(entry["task_type"]),
        rx.table.cell(entry["score"]),
        rx.table.cell(
            rx.button(
                "Delete",
                size="1",
                variant="outline",
                color_scheme="red",
                on_click=lambda: AppState.remove_manager_leaderboard_entry(entry["id"]),
            )
        ),
    )


def manager_leaderboard_form() -> rx.Component:
    """Form for manual leaderboard edits."""
    return rx.card(
        rx.vstack(
            rx.heading("Add Leaderboard Entry", size="4"),
            rx.grid(
                rx.vstack(
                    rx.text("Model", weight="bold", size="2"),
                    rx.input(
                        placeholder="Model name",
                        value=AppState.manager_new_entry["model"],
                        on_change=lambda value: AppState.update_manager_new_entry("model", value),
                    ),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Language", weight="bold", size="2"),
                    rx.input(
                        placeholder="e.g. Korean",
                        value=AppState.manager_new_entry["language"],
                        on_change=lambda value: AppState.update_manager_new_entry("language", value),
                    ),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Subject", weight="bold", size="2"),
                    rx.input(
                        placeholder="e.g. Math",
                        value=AppState.manager_new_entry["subject"],
                        on_change=lambda value: AppState.update_manager_new_entry("subject", value),
                    ),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Task Type", weight="bold", size="2"),
                    rx.input(
                        placeholder="e.g. Reasoning",
                        value=AppState.manager_new_entry["task_type"],
                        on_change=lambda value: AppState.update_manager_new_entry("task_type", value),
                    ),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Score", weight="bold", size="2"),
                    rx.input(
                        placeholder="0 - 100",
                        value=AppState.manager_new_entry["score"],
                        on_change=lambda value: AppState.update_manager_new_entry("score", value),
                        type="number",
                        step="0.1",
                    ),
                    align="start",
                ),
                columns="5",
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.spacer(),
                rx.button(
                    "Save to Local Leaderboard",
                    size="3",
                    color_scheme="blue",
                    on_click=AppState.add_manager_leaderboard_entry,
                ),
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def manager_coverage_section() -> rx.Component:
    """Coverage controls and manual editing."""
    return rx.card(
        rx.vstack(
            rx.heading("📈 Coverage Insights", size="5"),
            rx.text("Inspect leaderboard payloads, delete outliers, or insert manual entries.", size="2", color="gray"),
            rx.cond(
                AppState.manager_leaderboard.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Rank"),
                            rx.table.column_header_cell("Model"),
                            rx.table.column_header_cell("Language"),
                            rx.table.column_header_cell("Subject"),
                            rx.table.column_header_cell("Task Type"),
                            rx.table.column_header_cell("Score"),
                            rx.table.column_header_cell("Actions"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            AppState.manager_leaderboard,
                            manager_leaderboard_table_row,
                        )
                    ),
                ),
                rx.center(
                    rx.text("No leaderboard rows yet. Add one below.", color="gray"),
                    padding="2rem",
                ),
            ),
            manager_leaderboard_form(),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def manager_page() -> rx.Component:
    """Main manager dashboard layout."""
    return rx.cond(
        AppState.is_authenticated,
        rx.cond(
            AppState.is_admin_user,
            rx.vstack(
                rx.heading("🛠 Manager Console", size="6", margin_bottom="1rem"),
                manager_health_section(),
                manager_tasks_section(),
                manager_coverage_section(),
                spacing="4",
                width="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.heading("Admin access required", size="5"),
                    rx.text(
                        "Log in with an admin account to access the Manager console.",
                        color="gray",
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                ),
                width="100%",
            ),
        ),
        login_required_card("Please log in to access the Manager console."),
    )


def index() -> rx.Component:
    """Main application layout."""
    return rx.container(
        header(),
        navigation(),
        
        # Page content
        rx.cond(
            AppState.current_page == "evaluation",
            evaluation_page(),
            rx.cond(
                AppState.current_page == "status",
                status_page(),
                rx.cond(
                    AppState.current_page == "leaderboard",
                    leaderboard_page(),
                    manager_page(),
                ),
            ),
        ),
        
        size="4",
        padding="2rem",
    )


app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="blue",
    )
)
app.add_page(index, title="BenchHub Plus", on_load=AppState.initialize_auth,)
