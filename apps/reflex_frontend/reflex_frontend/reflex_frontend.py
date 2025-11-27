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
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = 30


class AppState(rx.State):
    """Main application state for BenchHub Plus."""
    
    # API Configuration
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:12000")
    
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
    

    # ----- Manager dashboard helpers -----
    def refresh_manager_snapshot(self):
        """Populate mock manager data until backend wiring is ready."""
        snapshot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.manager_health = {
            "database": "connected",
            "redis": "connected",
            "planner": "healthy",
            "hret": "available",
        }
        self.manager_capacity = {
            "pending": 3,
            "running": 1,
            "success": 14,
            "failure": 2,
            "cache_entries": 42,
        }
        self.manager_tasks = [
            {
                "id": "task_local_001",
                "status": "PENDING",
                "query": "Compare GPT-4 vs Claude-3 on KR history",
                "models_label": "Models: gpt-4, claude-3",
                "submitted_at": "2024-11-17 11:45",
                "duration": "-",
                "duration_label": "Duration: -",
            },
            {
                "id": "task_local_002",
                "status": "STARTED",
                "query": "Evaluate codellama on bug fixing",
                "models_label": "Models: codellama, gpt-4",
                "submitted_at": "2024-11-17 11:10",
                "duration": "12m",
                "duration_label": "Duration: 12m",
            },
            {
                "id": "task_local_003",
                "status": "FAILURE",
                "query": "Massive multi-model request",
                "models_label": "Models: model_a, model_b, model_c, model_d",
                "submitted_at": "2024-11-17 10:55",
                "duration": "2m",
                "duration_label": "Duration: 2m",
            },
        ]
        self.manager_leaderboard = [
            {
                "id": "lb_1",
                "rank": 1,
                "model": "GPT-4",
                "language": "Korean",
                "subject": "Math",
                "task_type": "Reasoning",
                "score": 91.4,
            },
            {
                "id": "lb_2",
                "rank": 2,
                "model": "Claude-3",
                "language": "Korean",
                "subject": "Math",
                "task_type": "Reasoning",
                "score": 89.1,
            },
            {
                "id": "lb_3",
                "rank": 3,
                "model": "Llama-2",
                "language": "English",
                "subject": "Coding",
                "task_type": "Bug Fixing",
                "score": 74.8,
            },
        ]
        self.manager_last_updated = snapshot_time
        self.manager_snapshot_loaded = True

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

    def add_manager_leaderboard_entry(self):
        """Add an entry to the mock leaderboard."""
        payload = self.manager_new_entry
        if not payload["model"] or not payload["score"]:
            return rx.toast.error("Model name and score are required")
        try:
            score_value = float(payload["score"])
        except ValueError:
            return rx.toast.error("Score must be numeric")
        new_entry = {
            "id": f"lb_custom_{len(self.manager_leaderboard) + 1}",
            "rank": 0,
            "model": payload["model"],
            "language": payload.get("language", ""),
            "subject": payload.get("subject", ""),
            "task_type": payload.get("task_type", ""),
            "score": score_value,
        }
        self._recalculate_leaderboard(self.manager_leaderboard + [new_entry])
        self.manager_new_entry = {
            "model": "",
            "language": "",
            "subject": "",
            "task_type": "",
            "score": "",
        }
        return rx.toast.success("Entry saved locally")

    def remove_manager_leaderboard_entry(self, entry_id: str):
        """Remove an entry by ID."""
        entries = [entry for entry in self.manager_leaderboard if entry["id"] != entry_id]
        if len(entries) == len(self.manager_leaderboard):
            return
        self._recalculate_leaderboard(entries)
        return rx.toast.info("Entry removed")

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
        if not self.query.strip():
            return rx.toast.error("Please enter a query")
        
        if not self.models:
            return rx.toast.error("Please add at least one model")
        
        # Validate models
        for model in self.models:
            if not model.get("name") or not model.get("api_key"):
                return rx.toast.error("Please fill in all model fields")
        
        self.is_submitting = True
        
        try:
            # Prepare API request
            payload = {
                "query": self.query,
                "models": [
                    {
                        "name": model["name"],
                        "type": model["model_type"],
                        "base_url": model.get("api_base", ""),
                        "api_key": model["api_key"]
                    }
                    for model in self.models
                ]
            }
            
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.post(
                    f"{API_BASE_URL}/hret/evaluate",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = result.get("task_id")
                    
                    # Add task to history
                    new_task = {
                        "id": task_id,
                        "status": "pending",
                        "progress": 0,
                        "model_name": ", ".join([m["name"] for m in self.models]),
                        "query": self.query,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "estimated_time": result.get("estimated_duration", "Unknown")
                    }
                    
                    self.task_history = [new_task] + self.task_history
                    self.current_task_id = task_id
                    
                    return rx.toast.success(f"Evaluation started! Task ID: {task_id}")
                else:
                    error_msg = response.json().get("detail", "Unknown error")
                    return rx.toast.error(f"Failed to start evaluation: {error_msg}")
                    
        except httpx.TimeoutException:
            return rx.toast.error("Request timeout. Please try again.")
        except Exception as e:
            return rx.toast.error(f"Error: {str(e)}")
        finally:
            self.is_submitting = False
    
    async def refresh_task_status(self, task_id: str):
        """Refresh status of a specific task."""
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.get(f"{API_BASE_URL}/hret/evaluate/{task_id}")
                
                if response.status_code == 200:
                    task_data = response.json()
                    
                    # Update task in history
                    for i, task in enumerate(self.task_history):
                        if task["id"] == task_id:
                            self.task_history[i].update({
                                "status": task_data.get("status", "unknown"),
                                "progress": task_data.get("progress", {}).get("percentage", 0),
                            })
                            break
                            
        except Exception as e:
            print(f"Error refreshing task status: {e}")
    
    async def load_leaderboard_data(self):
        """Load leaderboard data from backend."""
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.get(f"{API_BASE_URL}/api/v1/leaderboard/browse")
                
                if response.status_code == 200:
                    data = response.json()
                    # Process leaderboard data
                    return data
                    
        except Exception as e:
            print(f"Error loading leaderboard: {e}")
            return None


def header() -> rx.Component:
    """Main header component."""
    return rx.box(
        rx.hstack(
            rx.heading(
                "🏆 BenchHub Plus",
                size="8",
                color="transparent",
                background="linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
                background_clip="text",
            ),
            rx.spacer(),
            rx.color_mode.button(),
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
            "🛠 Manager",
            on_click=lambda: AppState.set_page("manager"),
            variant=rx.cond(AppState.current_page == "manager", "solid", "outline"),
            color_scheme="blue",
        ),
        spacing="4",
        justify="center",
        margin_bottom="2rem",
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
    return rx.vstack(
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
    return rx.vstack(
        rx.heading("📊 Task Status", size="6", margin_bottom="1rem"),
        
        # Summary stats
        rx.grid(
            rx.card(
                rx.vstack(
                    rx.text("Total Tasks", size="2", color="gray"),
                    rx.text(AppState.task_history.length(), size="6", weight="bold"),
                    align="center",
                    spacing="1",
                ),
                width="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.text("Running", size="2", color="gray"),
                    rx.text("1", size="6", weight="bold", color="blue"),
                    align="center",
                    spacing="1",
                ),
                width="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.text("Completed", size="2", color="gray"),
                    rx.text("1", size="6", weight="bold", color="green"),
                    align="center",
                    spacing="1",
                ),
                width="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.text("Pending", size="2", color="gray"),
                    rx.text("1", size="6", weight="bold", color="orange"),
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


def leaderboard_page() -> rx.Component:
    """Leaderboard browsing page."""
    return rx.vstack(
        rx.heading("🏅 Browse Leaderboards", size="6", margin_bottom="1rem"),
        
        # Leaderboard table
        rx.card(
            rx.vstack(
                rx.heading("Model Performance Rankings", size="4", margin_bottom="1rem"),
                
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Rank"),
                            rx.table.column_header_cell("Model"),
                            rx.table.column_header_cell("Score"),
                            rx.table.column_header_cell("Task Type"),
                            rx.table.column_header_cell("Date"),
                        ),
                    ),
                    rx.table.body(
                        rx.table.row(
                            rx.table.row_header_cell("1"),
                            rx.table.cell("GPT-4"),
                            rx.table.cell(
                                rx.badge("95.2", color_scheme="green", variant="solid")
                            ),
                            rx.table.cell("Korean Math"),
                            rx.table.cell("2024-11-17"),
                        ),
                        rx.table.row(
                            rx.table.row_header_cell("2"),
                            rx.table.cell("Claude-3"),
                            rx.table.cell(
                                rx.badge("92.8", color_scheme="blue", variant="solid")
                            ),
                            rx.table.cell("Text Summary"),
                            rx.table.cell("2024-11-17"),
                        ),
                        rx.table.row(
                            rx.table.row_header_cell("3"),
                            rx.table.cell("Llama-2"),
                            rx.table.cell(
                                rx.badge("88.5", color_scheme="orange", variant="solid")
                            ),
                            rx.table.cell("Code Generation"),
                            rx.table.cell("2024-11-17"),
                        ),
                        rx.table.row(
                            rx.table.row_header_cell("4"),
                            rx.table.cell("Gemini Pro"),
                            rx.table.cell(
                                rx.badge("85.3", color_scheme="purple", variant="solid")
                            ),
                            rx.table.cell("Korean Math"),
                            rx.table.cell("2024-11-16"),
                        ),
                    ),
                    width="100%",
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
                
                rx.grid(
                    rx.vstack(
                        rx.text("Language", weight="bold", size="2"),
                        rx.select(
                            ["All", "Korean", "English", "Japanese", "Chinese"],
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
                            ["All", "Math", "Science", "Language", "History", "Programming"],
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
                            ["All", "Korean Math", "Text Summary", "Code Generation", "Translation", "QA"],
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
                
                rx.center(
                    rx.button(
                        "Apply Filters",
                        size="3",
                        color_scheme="blue",
                        width="200px",
                    ),
                    width="100%",
                    margin_top="1rem",
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
                    "Mark Success",
                    size="1",
                    variant="soft",
                    color_scheme="green",
                    on_click=lambda: AppState.update_manager_task_status(task["id"], "SUCCESS"),
                ),
                rx.button(
                    "Mark Failure",
                    size="1",
                    variant="soft",
                    color_scheme="red",
                    on_click=lambda: AppState.update_manager_task_status(task["id"], "FAILURE"),
                ),
                rx.button(
                    "Remove",
                    size="1",
                    variant="outline",
                    color_scheme="gray",
                    on_click=lambda: AppState.remove_manager_task(task["id"]),
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
                AppState.manager_last_updated,
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
    return rx.vstack(
        rx.heading("🛠 Manager Console", size="6", margin_bottom="1rem"),
        manager_health_section(),
        manager_tasks_section(),
        manager_coverage_section(),
        spacing="4",
        width="100%",
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
        
        max_width="1200px",
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
app.add_page(index, title="BenchHub Plus")
