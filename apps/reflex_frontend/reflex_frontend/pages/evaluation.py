"""Evaluation request page — query input + model configuration."""

import reflex as rx

from ..state import AppState
from ..components.layout import login_required_card


# =========================================================================
# Model form (sub-component)
# =========================================================================

def _model_form(index: rx.Var[int]) -> rx.Component:
    """Individual model configuration form."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("bot", size=16, color="var(--accent-9)"),
                    rx.text("Model ", index + 1, weight="bold", size="3"),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("trash_2", size=12),
                    "Remove",
                    on_click=lambda: AppState.remove_model(index),
                    variant="ghost",
                    color_scheme="red",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            rx.grid(
                rx.vstack(
                    rx.text(
                        "Model Name",
                        weight="medium",
                        size="2",
                        color="var(--gray-11)",
                    ),
                    rx.input(
                        placeholder="e.g. gpt-4o, claude-3.5-sonnet",
                        value=AppState.models[index]["name"],
                        on_change=lambda value: AppState.update_model(
                            index, "name", value
                        ),
                        width="100%",
                        size="2",
                    ),
                    align="start",
                    width="100%",
                    spacing="1",
                ),
                rx.vstack(
                    rx.text(
                        "Model Type",
                        weight="medium",
                        size="2",
                        color="var(--gray-11)",
                    ),
                    rx.select(
                        ["openai", "anthropic", "huggingface", "custom"],
                        value=AppState.models[index]["model_type"],
                        on_change=lambda value: AppState.update_model(
                            index, "model_type", value
                        ),
                        width="100%",
                        size="2",
                    ),
                    align="start",
                    width="100%",
                    spacing="1",
                ),
                rx.vstack(
                    rx.text(
                        "API Base URL",
                        weight="medium",
                        size="2",
                        color="var(--gray-11)",
                    ),
                    rx.input(
                        placeholder="https://api.openai.com/v1",
                        value=AppState.models[index]["api_base"],
                        on_change=lambda value: AppState.update_model(
                            index, "api_base", value
                        ),
                        width="100%",
                        size="2",
                    ),
                    align="start",
                    width="100%",
                    spacing="1",
                ),
                rx.vstack(
                    rx.text(
                        "API Key", weight="medium", size="2", color="var(--gray-11)"
                    ),
                    rx.input(
                        placeholder="sk-...",
                        type="password",
                        value=AppState.models[index]["api_key"],
                        on_change=lambda value: AppState.update_model(
                            index, "api_key", value
                        ),
                        width="100%",
                        size="2",
                    ),
                    align="start",
                    width="100%",
                    spacing="1",
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
        padding="1rem",
        border_radius="var(--radius-3)",
        border="1px solid var(--gray-4)",
        background="var(--gray-1)",
        margin_bottom="0.75rem",
    )


# =========================================================================
# Page
# =========================================================================

def evaluation_page() -> rx.Component:
    """Evaluation request page."""
    return rx.cond(
        AppState.is_authenticated,
        rx.vstack(
            rx.hstack(
                rx.icon("file_pen_line", size=24, color="var(--accent-9)"),
                rx.heading("Evaluation Request", size="6"),
                spacing="3",
                align="center",
                margin_bottom="0.5rem",
            ),
            rx.text(
                "Configure your evaluation by describing the task and selecting models to benchmark.",
                size="3",
                color="var(--gray-9)",
                margin_bottom="1rem",
            ),
            # Query input card
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.icon("sparkles", size=18, color="var(--accent-9)"),
                        rx.text("Evaluation Query", weight="bold", size="3"),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "Describe what you want to evaluate in natural language. The AI planner will interpret your request.",
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.text_area(
                        placeholder="e.g. Compare these models on Korean math problems for high school students",
                        value=AppState.query,
                        on_change=AppState.set_query,
                        height="100px",
                        width="100%",
                        size="3",
                    ),
                    spacing="3",
                    width="100%",
                    align="start",
                ),
                width="100%",
            ),
            # Model configuration section
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.hstack(
                            rx.icon("cpu", size=18, color="var(--accent-9)"),
                            rx.text("Model Configuration", weight="bold", size="3"),
                            spacing="2",
                            align="center",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("plus", size=14),
                            "Add Model",
                            on_click=AppState.add_model,
                            variant="soft",
                            size="2",
                            disabled=rx.cond(
                                AppState.models.length() >= 10, True, False
                            ),
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.cond(
                        AppState.models.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                rx.Var.range(AppState.models.length()),
                                _model_form,
                            ),
                            width="100%",
                            spacing="2",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("cpu", size=32, color="var(--gray-6)"),
                                rx.text(
                                    "No models configured yet",
                                    color="var(--gray-9)",
                                    size="3",
                                    weight="medium",
                                ),
                                rx.text(
                                    "Click 'Add Model' to get started.",
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
            # Data scale configuration
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.icon("gauge", size=18, color="var(--accent-9)"),
                        rx.text("Data Scale", weight="bold", size="3"),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "Choose the number of evaluation samples. Larger scales yield more reliable results but cost more.",
                        size="2",
                        color="var(--gray-9)",
                    ),
                    rx.radio_group(
                        rx.hstack(
                            rx.radio_group_item(value="small"),
                            rx.vstack(
                                rx.text("Small", size="2", weight="medium"),
                                rx.text("50 samples · Fast & economical", size="1", color="var(--gray-9)"),
                                spacing="0",
                                align="start",
                            ),
                            rx.spacer(),
                            rx.radio_group_item(value="medium"),
                            rx.vstack(
                                rx.text("Medium", size="2", weight="medium"),
                                rx.text("100 samples · Balanced", size="1", color="var(--gray-9)"),
                                spacing="0",
                                align="start",
                            ),
                            rx.spacer(),
                            rx.radio_group_item(value="large"),
                            rx.vstack(
                                rx.text("Large", size="2", weight="medium"),
                                rx.text("250 samples · Thorough", size="1", color="var(--gray-9)"),
                                spacing="0",
                                align="start",
                            ),
                            rx.spacer(),
                            rx.radio_group_item(value="full"),
                            rx.vstack(
                                rx.text("Full", size="2", weight="medium"),
                                rx.text("500 samples · Comprehensive", size="1", color="var(--gray-9)"),
                                spacing="0",
                                align="start",
                            ),
                            spacing="4",
                            width="100%",
                            flex_wrap="wrap",
                        ),
                        value=AppState.sample_scale,
                        on_change=AppState.set_sample_scale,
                        size="2",
                    ),
                    spacing="3",
                    width="100%",
                    align="start",
                ),
                width="100%",
            ),
            # Submit button
            rx.center(
                rx.button(
                    rx.icon("rocket", size=18),
                    "Start Evaluation",
                    size="4",
                    color_scheme="blue",
                    loading=AppState.is_submitting,
                    width="300px",
                    disabled=rx.cond(
                        AppState.models.length() == 0, True, False
                    ),
                    on_click=AppState.submit_evaluation,
                ),
                width="100%",
                padding_top="0.5rem",
            ),
            width="100%",
            align="start",
            spacing="4",
        ),
        login_required_card("Please log in to create a new evaluation."),
    )
