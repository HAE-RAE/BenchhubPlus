"""Layout-level components: header, navigation bar, footer, login card."""

import reflex as rx
from ..state import AppState
from .shared import nav_item, sidebar_nav_item


# =========================================================================
# Header
# =========================================================================

def header() -> rx.Component:
    """Minimal top bar — just auth error if any."""
    return rx.cond(
        AppState.auth_error != "",
        rx.box(
            rx.hstack(
                rx.icon("triangle_alert", size=16, color="var(--red-9)"),
                rx.text(AppState.auth_error, color="var(--red-11)", size="2"),
                align="center",
                spacing="2",
            ),
            padding="10px 16px",
            border_radius="var(--radius-3)",
            background="var(--red-2)",
            border="1px solid var(--red-6)",
            width="100%",
            margin_bottom="1rem",
        ),
        rx.fragment(),
    )


# =========================================================================
# Navigation
# =========================================================================

def navigation() -> rx.Component:
    """Navigation component with tab-style design (legacy horizontal)."""
    return rx.center(
        rx.hstack(
            nav_item("Evaluation", "file_pen_line", "evaluation"),
            nav_item("Status", "activity", "status"),
            nav_item("Leaderboard", "trophy", "leaderboard"),
            rx.cond(
                AppState.is_admin_user,
                nav_item("Manager", "settings", "manager"),
                nav_item("Manager", "settings", "manager", disabled=True),
            ),
            spacing="2",
            padding="4px",
            background="var(--gray-2)",
            border_radius="var(--radius-4)",
            border="1px solid var(--gray-4)",
        ),
        width="100%",
        margin_bottom="2rem",
    )


def _sidebar_task_item(task: rx.Var[dict]) -> rx.Component:
    """Single task history item in sidebar."""
    status_color = rx.cond(
        task["status"] == "completed", "var(--green-9)",
        rx.cond(
            task["status"] == "running", "var(--blue-9)",
            rx.cond(task["status"] == "pending", "var(--orange-9)", "var(--red-9)"),
        ),
    )
    return rx.box(
        rx.hstack(
            # Main clickable area
            rx.vstack(
                rx.text(
                    task["query"],
                    size="2",
                    weight="medium",
                    color="var(--gray-12)",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                    width="100%",
                ),
                rx.hstack(
                    rx.box(
                        width="6px",
                        height="6px",
                        border_radius="50%",
                        background=status_color,
                        flex_shrink="0",
                    ),
                    rx.text(
                        task["created_at"],
                        size="1",
                        color="var(--gray-9)",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                    ),
                    rx.text("·", size="1", color="var(--gray-7)"),
                    rx.text(
                        task["model_name"],
                        size="1",
                        color="var(--gray-9)",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                        max_width="80px",
                    ),
                    spacing="1",
                    align="center",
                    width="100%",
                    overflow="hidden",
                ),
                spacing="1",
                align="start",
                width="100%",
                on_click=AppState.select_task(task["id"]),
                cursor="pointer",
            ),
            # Delete button (always visible, subtle)
            rx.icon_button(
                rx.icon("x", size=12),
                on_click=AppState.remove_task_from_history(task["id"]),
                variant="ghost",
                color_scheme="gray",
                size="1",
                flex_shrink="0",
                opacity="0.4",
                _hover={"opacity": "1", "color": "var(--red-9)"},
            ),
            spacing="1",
            align="center",
            width="100%",
        ),
        padding="8px 12px",
        border_radius="var(--radius-3)",
        width="100%",
        background=rx.cond(
            AppState.selected_task_id == task["id"],
            "var(--accent-3)",
            "transparent",
        ),
        _hover={"background": rx.cond(
            AppState.selected_task_id == task["id"],
            "var(--accent-4)",
            "var(--gray-3)",
        )},
        transition="background 0.1s ease",
    )


def sidebar() -> rx.Component:
    """Left vertical sidebar — chat-app style with history."""
    # ── collapsed view ────────────────────────────────────────────────
    collapsed_view = rx.vstack(
        rx.icon_button(
            rx.icon("panel_left_open", size=16),
            on_click=AppState.toggle_sidebar,
            variant="ghost", color_scheme="gray", size="2", cursor="pointer",
        ),
        rx.separator(size="4"),
        rx.tooltip(
            rx.icon_button(
                rx.icon("trophy", size=16),
                on_click=AppState.set_page("leaderboard"),
                variant="ghost", color_scheme="gray", size="2", cursor="pointer",
            ),
            content="Leaderboard", side="right",
        ),
        rx.tooltip(
            rx.icon_button(
                rx.icon("square_pen", size=16),
                on_click=AppState.new_evaluation,
                variant="ghost", color_scheme="indigo", size="2", cursor="pointer",
            ),
            content="New Evaluation", side="right",
        ),
        rx.cond(
            AppState.is_admin_user,
            rx.tooltip(
                rx.icon_button(
                    rx.icon("settings", size=16),
                    on_click=AppState.set_page("manager"),
                    variant="ghost", color_scheme="gray", size="2", cursor="pointer",
                ),
                content="Manager", side="right",
            ),
            rx.fragment(),
        ),
        spacing="2",
        align="center",
        padding="1rem 0.5rem",
        width="100%",
    )

    # ── expanded view ─────────────────────────────────────────────────
    expanded_view = rx.vstack(
        # Header row
        rx.hstack(
            rx.hstack(
                rx.icon("trophy", size=18, color="var(--accent-9)"),
                rx.text("BenchHub Plus", size="2", weight="bold", color="var(--gray-12)"),
                spacing="2", align="center",
            ),
            rx.icon_button(
                rx.icon("panel_left_close", size=16),
                on_click=AppState.toggle_sidebar,
                variant="ghost", color_scheme="gray", size="2", cursor="pointer",
            ),
            width="100%", align="center", justify="between",
            padding="1rem 0.75rem 0.5rem",
        ),
        # Top nav items
        rx.vstack(
            sidebar_nav_item("Leaderboard", "trophy", "leaderboard"),
            spacing="1",
            width="100%",
            padding="0 0.5rem",
        ),
        rx.separator(size="4"),
        # New Evaluation button
        rx.box(
            rx.button(
                rx.icon("square_pen", size=15),
                "New Evaluation",
                on_click=AppState.new_evaluation,
                variant="solid",
                color_scheme="indigo",
                size="2",
                width="100%",
                cursor="pointer",
            ),
            padding="0 0.75rem 0.75rem",
            width="100%",
        ),
        rx.separator(size="4"),
        # Task history list (scrollable)
        rx.cond(
            AppState.task_history.length() > 0,
            rx.box(
                rx.vstack(
                    rx.foreach(AppState.task_history, _sidebar_task_item),
                    spacing="0",
                    width="100%",
                ),
                padding="0.5rem",
                width="100%",
                overflow_y="auto",
                max_height="calc(100vh - 280px)",
            ),
            rx.box(
                rx.text(
                    "No evaluations yet",
                    size="1",
                    color="var(--gray-8)",
                    text_align="center",
                ),
                padding="1rem 0.75rem",
                width="100%",
            ),
        ),
        rx.spacer(),
        rx.separator(size="4"),
        # Bottom nav
        rx.vstack(
            rx.cond(
                AppState.is_admin_user,
                sidebar_nav_item("Manager", "settings", "manager"),
                rx.fragment(),
            ),
            spacing="1",
            width="100%",
            padding="0.5rem",
        ),
        # User info / Login
        rx.cond(
            AppState.is_authenticated,
            # Logged in: avatar + name + logout + dark mode
            rx.hstack(
                rx.avatar(
                    src=AppState.user_picture,
                    fallback=AppState.user_name[:1],
                    size="2",
                ),
                rx.vstack(
                    rx.text(
                        rx.cond(AppState.user_name != "", AppState.user_name, "User"),
                        size="1", weight="medium", color="var(--gray-12)",
                        overflow="hidden", text_overflow="ellipsis", white_space="nowrap",
                        max_width="100px",
                    ),
                    rx.text(AppState.user_role, size="1", color="var(--gray-9)"),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.color_mode.button(size="1"),
                rx.icon_button(
                    rx.icon("log_out", size=14),
                    on_click=AppState.logout,
                    variant="ghost", color_scheme="gray", size="1", cursor="pointer",
                    title="Sign out",
                ),
                width="100%", align="center", spacing="2",
                padding="0.5rem 0.75rem 1rem",
            ),
            # Not logged in: login + dark mode
            rx.vstack(
                rx.cond(
                    AppState.dev_auth_bypass,
                    rx.vstack(
                        rx.input(
                            placeholder="dev email",
                            value=AppState.dev_login_value,
                            on_change=AppState.set_dev_login_value,
                            size="2",
                            width="100%",
                        ),
                        rx.button(
                            rx.icon("log_in", size=14),
                            "Dev Login",
                            on_click=AppState.dev_login,
                            color_scheme="blue",
                            size="2",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.button(
                        rx.icon("log_in", size=14),
                        "Sign in with Google",
                        on_click=AppState.start_google_login,
                        color_scheme="blue",
                        size="2",
                        width="100%",
                    ),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.color_mode.button(size="1"),
                    width="100%",
                ),
                spacing="2",
                width="100%",
                padding="0.5rem 0.75rem 1rem",
            ),
        ),
        height="100%",
        width="100%",
        align="start",
        spacing="0",
    )

    return rx.box(
        rx.cond(AppState.sidebar_collapsed, collapsed_view, expanded_view),
        width=rx.cond(AppState.sidebar_collapsed, "60px", "240px"),
        min_height="100vh",
        height="100vh",
        background="var(--gray-1)",
        border_right="1px solid var(--gray-4)",
        position="fixed",
        top="0",
        left="0",
        z_index="10",
        transition="width 0.2s ease",
        overflow="hidden",
        display="flex",
        flex_direction="column",
    )


# =========================================================================
# Login required card
# =========================================================================

def login_required_card(message: str) -> rx.Component:
    """Shared login-required callout."""
    return rx.center(
        rx.card(
            rx.vstack(
                rx.center(
                    rx.box(
                        rx.icon("lock", size=32, color="var(--accent-9)"),
                        padding="16px",
                        border_radius="50%",
                        background="var(--accent-3)",
                    ),
                ),
                rx.vstack(
                    rx.heading(
                        "Authentication Required", size="5", text_align="center"
                    ),
                    rx.text(
                        message,
                        color="var(--gray-9)",
                        size="3",
                        text_align="center",
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.cond(
                    AppState.dev_auth_bypass,
                    rx.vstack(
                        rx.separator(size="4"),
                        rx.hstack(
                            rx.input(
                                placeholder="dev email",
                                value=AppState.dev_login_value,
                                on_change=AppState.set_dev_login_value,
                                width="100%",
                                size="3",
                            ),
                            rx.button(
                                rx.icon("log_in", size=16),
                                "Dev Login",
                                on_click=AppState.dev_login,
                                color_scheme="blue",
                                size="3",
                            ),
                            spacing="2",
                            align="center",
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    rx.center(
                        rx.button(
                            rx.icon("log_in", size=16),
                            "Sign in with Google",
                            on_click=AppState.start_google_login,
                            color_scheme="blue",
                            size="3",
                        ),
                        width="100%",
                    ),
                ),
                spacing="4",
                align="center",
                width="100%",
            ),
            max_width="420px",
            width="100%",
            padding="2rem",
        ),
        width="100%",
        padding_top="3rem",
    )


# =========================================================================
# Footer
# =========================================================================

def footer() -> rx.Component:
    """Application footer."""
    return rx.box(
        rx.separator(size="4"),
        rx.hstack(
            rx.hstack(
                rx.icon("trophy", size=14, color="var(--gray-8)"),
                rx.text(
                    "BenchHub Plus", size="1", color="var(--gray-8)", weight="medium"
                ),
                spacing="1",
                align="center",
            ),
            rx.spacer(),
            rx.text(
                "Interactive Leaderboard System for Dynamic LLM Evaluation",
                size="1",
                color="var(--gray-7)",
            ),
            width="100%",
            align="center",
            padding="1rem 0",
        ),
        width="100%",
        margin_top="3rem",
    )
