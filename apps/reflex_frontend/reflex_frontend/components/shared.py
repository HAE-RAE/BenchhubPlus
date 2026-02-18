"""Reusable helper components used across multiple pages."""

import reflex as rx
from ..state import AppState


def nav_item(
    label: str, icon_name: str, page: str, disabled: bool = False
) -> rx.Component:
    """Single navigation tab item."""
    is_active = AppState.current_page == page
    return rx.box(
        rx.hstack(
            rx.icon(icon_name, size=16),
            rx.text(label, size="2", weight="medium"),
            spacing="2",
            align="center",
        ),
        on_click=lambda: AppState.set_page(page),
        padding="8px 20px",
        border_radius="var(--radius-3)",
        cursor=rx.cond(disabled, "not-allowed", "pointer"),
        opacity=rx.cond(disabled, "0.4", "1"),
        background=rx.cond(is_active, "var(--accent-9)", "transparent"),
        color=rx.cond(is_active, "white", "var(--gray-11)"),
        _hover=rx.cond(
            is_active,
            {"background": "var(--accent-10)"},
            {"background": "var(--gray-3)"},
        ),
        transition="all 0.15s ease",
    )


def stat_card(
    icon_name: str, label: str, value: rx.Var, color: str
) -> rx.Component:
    """Stat card with icon — used on the Status page and elsewhere."""
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(icon_name, size=20, color=f"var(--{color}-9)"),
                padding="10px",
                border_radius="var(--radius-3)",
                background=f"var(--{color}-3)",
            ),
            rx.vstack(
                rx.text(label, size="2", color="var(--gray-9)"),
                rx.text(value, size="5", weight="bold", color=f"var(--{color}-11)"),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        padding="1rem",
        border="1px solid var(--gray-4)",
        border_radius="var(--radius-3)",
        width="100%",
    )
