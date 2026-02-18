"""BenchHub Plus - Reflex Frontend Application.

Slim entry-point that wires together state, layout, and page modules.
"""

import reflex as rx

from .state import AppState
from .components.layout import header, navigation, footer
from .pages.evaluation import evaluation_page
from .pages.status import status_page
from .pages.leaderboard import leaderboard_page
from .pages.manager import manager_page


def index() -> rx.Component:
    """Main application layout."""
    return rx.box(
        rx.container(
            header(),
            navigation(),
            # Page router
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
            footer(),
            size="4",
            padding="2rem",
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
