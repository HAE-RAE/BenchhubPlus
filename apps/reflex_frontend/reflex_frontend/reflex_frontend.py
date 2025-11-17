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
                leaderboard_page(),
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
