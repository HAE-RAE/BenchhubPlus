"""Layout-level components: header, navigation bar, footer, login card."""

import reflex as rx
from ..state import AppState
from .shared import nav_item


# =========================================================================
# Header
# =========================================================================

def header() -> rx.Component:
    """Main header component."""
    user_info = rx.cond(
        AppState.is_authenticated,
        rx.popover.root(
            rx.popover.trigger(
                rx.hstack(
                    rx.avatar(
                        src=AppState.user_picture,
                        fallback=AppState.user_name,
                        size="3",
                        cursor="pointer",
                        border="2px solid var(--accent-6)",
                    ),
                    rx.vstack(
                        rx.text(
                            rx.cond(
                                AppState.user_name != "", AppState.user_name, "User"
                            ),
                            weight="bold",
                            size="2",
                        ),
                        rx.text(AppState.user_role, size="1", color="var(--gray-9)"),
                        spacing="0",
                        align="start",
                    ),
                    spacing="2",
                    align="center",
                    cursor="pointer",
                    padding="6px 12px",
                    border_radius="var(--radius-3)",
                    _hover={"background": "var(--gray-3)"},
                ),
                as_child=True,
            ),
            rx.popover.content(
                rx.vstack(
                    rx.hstack(
                        rx.avatar(
                            src=AppState.user_picture,
                            fallback=AppState.user_name,
                            size="4",
                        ),
                        rx.vstack(
                            rx.text(
                                rx.cond(
                                    AppState.user_name != "",
                                    AppState.user_name,
                                    "Logged in",
                                ),
                                weight="bold",
                                size="3",
                            ),
                            rx.cond(
                                AppState.user_email != "",
                                rx.text(
                                    AppState.user_email,
                                    size="1",
                                    color="var(--gray-9)",
                                ),
                                rx.fragment(),
                            ),
                            spacing="1",
                            align="start",
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                    ),
                    rx.separator(size="4"),
                    rx.button(
                        rx.icon("log_out", size=14),
                        "Sign out",
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                        width="100%",
                        on_click=AppState.logout,
                    ),
                    align="start",
                    spacing="3",
                    width="100%",
                ),
                side="bottom",
                align="end",
                padding="1rem",
                width="280px",
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
            rx.icon("log_in", size=14),
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
        rx.fragment(),
        rx.cond(
            AppState.dev_auth_bypass,
            dev_login_controls,
            rx.button(
                rx.icon("log_in", size=14),
                "Sign in",
                variant="solid",
                color_scheme="blue",
                size="2",
                on_click=AppState.start_google_login,
            ),
        ),
    )

    right_controls = rx.hstack(
        user_info,
        auth_button,
        rx.color_mode.button(size="2"),
        spacing="3",
        align="center",
        justify="end",
    )

    return rx.box(
        rx.box(
            rx.hstack(
                rx.hstack(
                    rx.icon("trophy", size=28, color="var(--accent-9)"),
                    rx.heading(
                        "BenchHub Plus",
                        size="7",
                        weight="bold",
                        color="transparent",
                        background="linear-gradient(135deg, var(--accent-9) 0%, var(--purple-9) 100%)",
                        background_clip="text",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                right_controls,
                width="100%",
                align="center",
            ),
            padding="1rem 0",
        ),
        rx.text(
            "Interactive Leaderboard System for Dynamic LLM Evaluation",
            size="3",
            color="var(--gray-9)",
            text_align="center",
            padding_bottom="1.5rem",
        ),
        rx.cond(
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
        ),
        width="100%",
        margin_bottom="1.5rem",
        border_bottom="1px solid var(--gray-4)",
        padding_bottom="1rem",
    )


# =========================================================================
# Navigation
# =========================================================================

def navigation() -> rx.Component:
    """Navigation component with tab-style design."""
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
