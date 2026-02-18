"""Manager console page — admin dashboard with health, tasks, and coverage."""

from typing import Any
import reflex as rx

from ..state import AppState
from ..components.layout import login_required_card


# =========================================================================
# Sub-components
# =========================================================================

def _status_card(title: str, value: rx.Var[str], description: str = "") -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(title, size="2", weight="medium", color="var(--gray-11)"),
            rx.badge(
                value,
                variant="soft",
                color_scheme=rx.cond(
                    value == "healthy",
                    "green",
                    rx.cond(value == "unknown", "gray", "red"),
                ),
                size="2",
            ),
            rx.cond(
                description != "",
                rx.text(description, size="1", color="var(--gray-8)"),
                rx.fragment(),
            ),
            spacing="2",
            align="start",
        ),
        padding="1rem",
        border="1px solid var(--gray-4)",
        border_radius="var(--radius-3)",
        width="100%",
    )


def _capacity_card(title: str, value: rx.Var[Any], color: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(title, size="2", color="var(--gray-9)"),
            rx.text(value, size="6", weight="bold", color=f"var(--{color}-11)"),
            spacing="1",
            align="start",
        ),
        padding="1rem",
        border="1px solid var(--gray-4)",
        border_radius="var(--radius-3)",
        width="100%",
    )


def _task_card(task: rx.Var[dict]) -> rx.Component:
    status_color = rx.cond(
        task["status"] == "SUCCESS",
        "green",
        rx.cond(
            task["status"] == "FAILURE",
            "red",
            rx.cond(task["status"] == "STARTED", "blue", "orange"),
        ),
    )
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge(task["status"], color_scheme=status_color, variant="soft", size="1"),
                rx.spacer(),
                rx.hstack(
                    rx.icon("clock", size=12, color="var(--gray-8)"),
                    rx.text(task["submitted_at"], size="1", color="var(--gray-9)"),
                    spacing="1",
                    align="center",
                ),
                width="100%",
                align="center",
            ),
            rx.text(task["query"], weight="bold", size="3"),
            rx.hstack(
                rx.badge(task["models_label"], variant="outline", size="1"),
                rx.text(task["duration_label"], size="1", color="var(--gray-8)"),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.button(
                    rx.icon("rotate_ccw", size=12), "Restart",
                    size="1", variant="soft", color_scheme="green",
                    on_click=lambda: AppState.manager_patch_task(task["id"], "restart"),
                ),
                rx.button(
                    rx.icon("pause", size=12), "Hold",
                    size="1", variant="soft", color_scheme="orange",
                    on_click=lambda: AppState.manager_patch_task(task["id"], "hold"),
                ),
                rx.button(
                    rx.icon("x", size=12), "Cancel",
                    size="1", variant="ghost", color_scheme="red",
                    on_click=lambda: AppState.manager_patch_task(task["id"], "cancel"),
                ),
                spacing="2",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        padding="1rem",
        border="1px solid var(--gray-4)",
        border_radius="var(--radius-3)",
        width="100%",
        _hover={"border_color": "var(--gray-6)"},
        transition="border-color 0.15s ease",
    )


# =========================================================================
# Sections
# =========================================================================

def _health_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("shield_check", size=18, color="var(--accent-9)"),
                    rx.text("Health & Capacity Snapshot", weight="bold", size="3"),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("refresh_cw", size=14), "Refresh",
                    variant="soft", size="2",
                    on_click=AppState.refresh_manager_snapshot,
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                AppState.manager_last_updated != None,
                rx.hstack(
                    rx.icon("clock", size=12, color="var(--gray-8)"),
                    rx.text("Last updated: ", AppState.manager_last_updated, size="2", color="var(--gray-9)"),
                    spacing="1", align="center",
                ),
                rx.text("Click refresh to load system status", size="2", color="var(--gray-8)"),
            ),
            rx.cond(
                AppState.manager_snapshot_loaded,
                rx.vstack(
                    rx.text("System Status", size="2", weight="medium", color="var(--gray-9)"),
                    rx.grid(
                        _status_card("Database", AppState.manager_health["database"], "FastAPI / PostgreSQL"),
                        _status_card("Redis", AppState.manager_health["redis"], "Celery broker/cache"),
                        _status_card("Planner", AppState.manager_health["planner"], "LLM plan agent"),
                        _status_card("HRET", AppState.manager_health["hret"], "Toolkit availability"),
                        columns="4", spacing="3", width="100%",
                    ),
                    rx.text("Pipeline Capacity", size="2", weight="medium", color="var(--gray-9)"),
                    rx.grid(
                        _capacity_card("Pending", AppState.manager_capacity["pending"], "orange"),
                        _capacity_card("Running", AppState.manager_capacity["running"], "blue"),
                        _capacity_card("Success", AppState.manager_capacity["success"], "green"),
                        _capacity_card("Failure", AppState.manager_capacity["failure"], "red"),
                        _capacity_card("Cache Entries", AppState.manager_capacity["cache_entries"], "purple"),
                        columns="5", spacing="3", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("server", size=28, color="var(--gray-6)"),
                        rx.text("No snapshot loaded yet", color="var(--gray-9)", size="2"),
                        align="center", spacing="2",
                    ),
                    padding="2rem",
                ),
            ),
            spacing="4", width="100%",
        ),
        width="100%",
    )


def _tasks_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("list_checks", size=18, color="var(--accent-9)"),
                rx.text("Task Pipeline Control", weight="bold", size="3"),
                spacing="2", align="center",
            ),
            rx.text("Mark, remove, or inspect suspicious jobs.", size="2", color="var(--gray-9)"),
            rx.cond(
                AppState.manager_tasks.length() > 0,
                rx.vstack(
                    rx.foreach(AppState.manager_tasks, _task_card),
                    spacing="2", width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("inbox", size=28, color="var(--gray-6)"),
                        rx.text("No task data", color="var(--gray-9)", size="2"),
                        rx.text("Run the snapshot refresh to load tasks.", color="var(--gray-8)", size="1"),
                        align="center", spacing="2",
                    ),
                    padding="2rem",
                ),
            ),
            spacing="4", width="100%",
        ),
        width="100%",
    )


def _leaderboard_row(entry: rx.Var[dict]) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(entry["rank"], size="2", color="var(--gray-9)")),
        rx.table.cell(rx.text(entry["model"], weight="medium", size="2")),
        rx.table.cell(rx.badge(entry["language"], variant="outline", size="1")),
        rx.table.cell(rx.text(entry["subject"], size="2")),
        rx.table.cell(rx.badge(entry["task_type"], variant="soft", size="1")),
        rx.table.cell(rx.badge(entry["score"], color_scheme="blue", variant="solid", size="1")),
        rx.table.cell(
            rx.button(
                rx.icon("trash_2", size=12), "Delete",
                size="1", variant="ghost", color_scheme="red",
                on_click=lambda: AppState.remove_manager_leaderboard_entry(entry["id"]),
            )
        ),
        _hover={"background": "var(--gray-2)"},
    )


def _leaderboard_form() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("circle_plus", size=16, color="var(--accent-9)"),
                rx.text("Add Leaderboard Entry", weight="bold", size="3"),
                spacing="2", align="center",
            ),
            rx.grid(
                rx.vstack(
                    rx.text("Model", weight="bold", size="2"),
                    rx.input(
                        placeholder="Model name",
                        value=AppState.manager_new_entry["model"],
                        on_change=lambda v: AppState.update_manager_new_entry("model", v),
                    ),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Language", weight="bold", size="2"),
                    rx.input(
                        placeholder="e.g. Korean",
                        value=AppState.manager_new_entry["language"],
                        on_change=lambda v: AppState.update_manager_new_entry("language", v),
                    ),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Subject", weight="bold", size="2"),
                    rx.input(
                        placeholder="e.g. Math",
                        value=AppState.manager_new_entry["subject"],
                        on_change=lambda v: AppState.update_manager_new_entry("subject", v),
                    ),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Task Type", weight="bold", size="2"),
                    rx.input(
                        placeholder="e.g. Reasoning",
                        value=AppState.manager_new_entry["task_type"],
                        on_change=lambda v: AppState.update_manager_new_entry("task_type", v),
                    ),
                    align="start",
                ),
                rx.vstack(
                    rx.text("Score", weight="bold", size="2"),
                    rx.input(
                        placeholder="0 - 100",
                        value=AppState.manager_new_entry["score"],
                        on_change=lambda v: AppState.update_manager_new_entry("score", v),
                        type="number", step="0.1",
                    ),
                    align="start",
                ),
                columns="5", spacing="4", width="100%",
            ),
            rx.hstack(
                rx.spacer(),
                rx.button(
                    rx.icon("save", size=14), "Save Entry",
                    size="3", color_scheme="blue",
                    on_click=AppState.add_manager_leaderboard_entry,
                ),
            ),
            spacing="3", width="100%",
        ),
        padding="1rem",
        border="1px dashed var(--gray-5)",
        border_radius="var(--radius-3)",
        background="var(--gray-1)",
        width="100%",
    )


def _coverage_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("bar_chart_2", size=18, color="var(--accent-9)"),
                rx.text("Coverage Insights", weight="bold", size="3"),
                spacing="2", align="center",
            ),
            rx.text(
                "Inspect leaderboard payloads, delete outliers, or insert manual entries.",
                size="2", color="var(--gray-9)",
            ),
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
                        rx.foreach(AppState.manager_leaderboard, _leaderboard_row)
                    ),
                ),
                rx.center(
                    rx.text("No leaderboard rows yet. Add one below.", color="gray"),
                    padding="2rem",
                ),
            ),
            _leaderboard_form(),
            spacing="3", width="100%",
        ),
        width="100%",
    )


# =========================================================================
# Page
# =========================================================================

def manager_page() -> rx.Component:
    return rx.cond(
        AppState.is_authenticated,
        rx.cond(
            AppState.is_admin_user,
            rx.vstack(
                rx.hstack(
                    rx.icon("settings", size=24, color="var(--accent-9)"),
                    rx.heading("Manager Console", size="6"),
                    rx.badge("Admin", variant="soft", color_scheme="orange", size="1"),
                    spacing="3", align="center", margin_bottom="0.5rem",
                ),
                _health_section(),
                _tasks_section(),
                _coverage_section(),
                spacing="4", width="100%",
            ),
            rx.center(
                rx.card(
                    rx.vstack(
                        rx.center(
                            rx.box(
                                rx.icon("shield_alert", size=32, color="var(--orange-9)"),
                                padding="16px", border_radius="50%", background="var(--orange-3)",
                            ),
                        ),
                        rx.heading("Admin Access Required", size="5", text_align="center"),
                        rx.text(
                            "Log in with an admin account to access the Manager console.",
                            color="var(--gray-9)", size="3", text_align="center",
                        ),
                        spacing="3", align="center", width="100%",
                    ),
                    max_width="420px", width="100%", padding="2rem",
                ),
                width="100%", padding_top="3rem",
            ),
        ),
        login_required_card("Please log in to access the Manager console."),
    )
