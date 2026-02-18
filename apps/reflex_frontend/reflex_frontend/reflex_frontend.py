"""BenchHub Plus - Reflex Frontend Application.

Slim entry-point that wires together state, layout, and page modules.
"""

import reflex as rx

from .state import AppState
from .components.layout import header, sidebar, footer
from .pages.evaluation import evaluation_page
from .pages.leaderboard import leaderboard_page
from .pages.manager import manager_page


def index() -> rx.Component:
    """Main application layout with left sidebar (Arena-style)."""
    return rx.box(
        rx.flex(
            # Left sidebar (fixed)
            sidebar(),
            # Main content area (with left margin for sidebar)
            rx.box(
                rx.container(
                    header(),
                    # Page router
                    rx.cond(
                        AppState.current_page == "evaluation",
                        evaluation_page(),
                        rx.cond(
                            AppState.current_page == "leaderboard",
                            leaderboard_page(),
                            manager_page(),
                        ),
                    ),
                    footer(),
                    size="4",
                    padding="2rem",
                    width="100%",
                ),
                flex="1",
                min_height="100vh",
                background="var(--color-background)",
                margin_left=rx.cond(AppState.sidebar_collapsed, "60px", "240px"),
                transition="margin-left 0.2s ease",
            ),
            width="100%",
            align="start",
        ),
        min_height="100vh",
        background="var(--color-background)",
    )


app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="indigo",
        scaling="100%",
    ),
    style={
        "::selection": {"background": "var(--accent-5)"},
    },
)
app.add_page(index, title="BenchHub Plus", on_load=AppState.initialize_auth)
