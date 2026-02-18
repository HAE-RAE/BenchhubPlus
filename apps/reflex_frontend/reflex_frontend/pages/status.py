"""Task status monitoring page."""

import reflex as rx

from ..state import AppState
from ..components.layout import login_required_card
from ..components.shared import stat_card


# =========================================================================
# Task status card (sub-component)
# =========================================================================

def _task_status_card(task: rx.Var[dict]) -> rx.Component:
    """Individual task status card."""
    status_color = rx.cond(
        task["status"] == "completed",
        "green",
        rx.cond(
            task["status"] == "running",
            "blue",
            rx.cond(task["status"] == "pending", "orange", "red"),
        ),
    )
    status_icon = rx.cond(
        task["status"] == "completed",
        rx.icon("circle_check", size=16, color="var(--green-9)"),
        rx.cond(
            task["status"] == "running",
            rx.icon("loader", size=16, color="var(--blue-9)"),
            rx.cond(
                task["status"] == "pending",
                rx.icon("clock", size=16, color="var(--orange-9)"),
                rx.icon("circle_x", size=16, color="var(--red-9)"),
            ),
        ),
    )
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    status_icon,
                    rx.badge(
                        task["status"],
                        color_scheme=status_color,
                        variant="soft",
                        size="1",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.icon("clock", size=12, color="var(--gray-8)"),
                    rx.text(task["created_at"], size="1", color="var(--gray-9)"),
                    spacing="1",
                    align="center",
                ),
                width="100%",
                align="center",
            ),
            rx.vstack(
                rx.text(task["query"], weight="bold", size="3"),
                rx.hstack(
                    rx.badge(task["model_name"], variant="outline", size="1"),
                    rx.text("ID: ", task["id"], size="1", color="var(--gray-8)"),
                    spacing="2",
                    align="center",
                ),
                align="start",
                spacing="1",
                width="100%",
            ),
            rx.cond(
                task["status"] == "running",
                rx.vstack(
                    rx.hstack(
                        rx.text("Progress", size="2", color="var(--gray-9)"),
                        rx.spacer(),
                        rx.text(
                            task["progress"],
                            "%",
                            size="2",
                            weight="bold",
                            color="var(--blue-11)",
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.progress(
                        value=task["progress"], width="100%", color_scheme="blue"
                    ),
                    rx.hstack(
                        rx.icon("timer", size=12, color="var(--gray-8)"),
                        rx.text(
                            "Est. ",
                            task["estimated_time"],
                            size="1",
                            color="var(--gray-8)",
                        ),
                        spacing="1",
                        align="center",
                    ),
                    width="100%",
                    spacing="2",
                ),
                rx.cond(
                    task["status"] == "completed",
                    rx.box(
                        rx.hstack(
                            rx.icon(
                                "circle_check", size=14, color="var(--green-9)"
                            ),
                            rx.text(
                                "Evaluation completed successfully",
                                size="2",
                                color="var(--green-11)",
                            ),
                            align="center",
                            spacing="2",
                        ),
                        padding="8px 12px",
                        background="var(--green-2)",
                        border_radius="var(--radius-2)",
                        width="100%",
                    ),
                    rx.cond(
                        task["status"] == "pending",
                        rx.box(
                            rx.hstack(
                                rx.icon("clock", size=14, color="var(--orange-9)"),
                                rx.text(
                                    "Waiting in queue",
                                    size="2",
                                    color="var(--orange-11)",
                                ),
                                align="center",
                                spacing="2",
                            ),
                            padding="8px 12px",
                            background="var(--orange-2)",
                            border_radius="var(--radius-2)",
                            width="100%",
                        ),
                        rx.box(
                            rx.hstack(
                                rx.icon("circle_x", size=14, color="var(--red-9)"),
                                rx.text(
                                    "Task failed",
                                    size="2",
                                    color="var(--red-11)",
                                ),
                                align="center",
                                spacing="2",
                            ),
                            padding="8px 12px",
                            background="var(--red-2)",
                            border_radius="var(--radius-2)",
                            width="100%",
                        ),
                    ),
                ),
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        padding="1rem",
        border="1px solid var(--gray-4)",
        border_radius="var(--radius-3)",
        width="100%",
        margin_bottom="0.75rem",
        _hover={
            "border_color": "var(--gray-6)",
            "box_shadow": "0 2px 8px var(--gray-a3)",
        },
        transition="all 0.15s ease",
    )


# =========================================================================
# Page
# =========================================================================

def status_page() -> rx.Component:
    """Task status monitoring page."""
    return rx.cond(
        AppState.is_authenticated,
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("activity", size=24, color="var(--accent-9)"),
                    rx.heading("Task Status", size="6"),
                    spacing="3",
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("refresh_cw", size=14),
                    "Refresh",
                    variant="soft",
                    size="2",
                    on_click=AppState.refresh_current_task,
                    disabled=rx.cond(AppState.total_task_count == 0, True, False),
                ),
                width="100%",
                align="center",
            ),
            # Summary stats
            rx.grid(
                stat_card("layers", "Total Tasks", AppState.total_task_count, "gray"),
                stat_card("loader", "Running", AppState.running_task_count, "blue"),
                stat_card(
                    "circle_check",
                    "Completed",
                    AppState.completed_task_count,
                    "green",
                ),
                stat_card("clock", "Pending", AppState.pending_task_count, "orange"),
                columns="4",
                spacing="3",
                width="100%",
            ),
            # Task list
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.icon("list", size=18, color="var(--gray-9)"),
                        rx.text("Recent Tasks", weight="bold", size="3"),
                        spacing="2",
                        align="center",
                    ),
                    rx.cond(
                        AppState.task_history.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                AppState.task_history, _task_status_card
                            ),
                            width="100%",
                            spacing="2",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("inbox", size=32, color="var(--gray-6)"),
                                rx.text(
                                    "No tasks found",
                                    color="var(--gray-9)",
                                    size="3",
                                    weight="medium",
                                ),
                                rx.text(
                                    "Start an evaluation to see task status here.",
                                    color="var(--gray-8)",
                                    size="2",
                                ),
                                align="center",
                                spacing="2",
                            ),
                            padding="3rem",
                        ),
                    ),
                    spacing="4",
                    width="100%",
                    align="start",
                ),
                width="100%",
            ),
            width="100%",
            align="start",
            spacing="4",
        ),
        login_required_card("Please log in to view task status."),
    )
