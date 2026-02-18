"""Leaderboard browsing page — rankings table, AI search, manual filters."""

import reflex as rx

from ..state import AppState
from ..components.layout import login_required_card


# =========================================================================
# Table row
# =========================================================================

def _leaderboard_table_row(entry: rx.Var[dict]) -> rx.Component:
    rank_display = rx.cond(
        entry["rank"] == 1,
        rx.text("1st", weight="bold", size="2", color="var(--amber-9)"),
        rx.cond(
            entry["rank"] == 2,
            rx.text("2nd", weight="bold", size="2", color="var(--gray-9)"),
            rx.cond(
                entry["rank"] == 3,
                rx.text("3rd", weight="bold", size="2", color="var(--orange-9)"),
                rx.text(entry["rank"], size="2", color="var(--gray-9)"),
            ),
        ),
    )
    return rx.table.row(
        rx.table.cell(rank_display),
        rx.table.cell(rx.text(entry["model"], weight="medium", size="2")),
        rx.table.cell(rx.badge(entry["language"], variant="outline", size="1")),
        rx.table.cell(rx.text(entry["subject"], size="2")),
        rx.table.cell(rx.badge(entry["task_type"], variant="soft", size="1")),
        rx.table.cell(
            rx.badge(
                entry["score_label"],
                color_scheme="blue",
                variant="solid",
                size="2",
            )
        ),
        rx.table.cell(
            rx.text(entry["updated_at"], size="1", color="var(--gray-9)")
        ),
        _hover={"background": "var(--gray-2)"},
    )


# =========================================================================
# AI search section
# =========================================================================

def _ai_search_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("sparkles", size=20, color="var(--accent-9)"),
                rx.heading("AI Search", size="4"),
                rx.badge(
                    "Planning Agent",
                    variant="soft",
                    color_scheme="blue",
                    size="1",
                ),
                align="center",
                spacing="2",
            ),
            rx.text(
                "Describe what you're looking for in natural language. The AI planner will automatically set the best filters.",
                size="2",
                color="gray",
            ),
            rx.hstack(
                rx.input(
                    placeholder="e.g. Korean math reasoning, English code generation ...",
                    value=AppState.leaderboard_query,
                    on_change=AppState.set_leaderboard_query,
                    size="3",
                    width="100%",
                ),
                rx.button(
                    rx.icon("search", size=16),
                    "Search",
                    size="3",
                    color_scheme="blue",
                    on_click=AppState.suggest_leaderboard_filters,
                    loading=AppState.leaderboard_loading,
                ),
                width="100%",
                spacing="2",
                align="center",
            ),
            # Off-topic guide message
            rx.cond(
                (AppState.leaderboard_plan_summary != "") & AppState.leaderboard_is_off_topic,
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.icon(
                                "message_circle_question", size=16, color="var(--blue-9)"
                            ),
                            rx.text("BenchHub Plus Usage Guide", weight="bold", size="2"),
                            align="center",
                        ),
                        rx.text(
                            AppState.leaderboard_plan_summary,
                            size="2",
                            white_space="pre-wrap",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    padding="16px",
                    border_radius="8px",
                    background="var(--blue-2)",
                    border="1px solid var(--blue-6)",
                    width="100%",
                ),
                rx.fragment(),
            ),
            # Planner results (normal evaluation queries)
            rx.cond(
                (AppState.leaderboard_plan_summary != "") & ~AppState.leaderboard_is_off_topic,
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.icon(
                                "circle_check", size=14, color="var(--green-9)"
                            ),
                            rx.text("Planned Filters", weight="bold", size="2"),
                            rx.spacer(),
                            rx.hstack(
                                rx.badge(
                                    rx.cond(
                                        AppState.leaderboard_used_planner,
                                        "AI Planner",
                                        "Fallback",
                                    ),
                                    variant="soft",
                                    color_scheme=rx.cond(
                                        AppState.leaderboard_used_planner,
                                        "green",
                                        "orange",
                                    ),
                                    size="1",
                                ),
                                rx.badge(
                                    "Confidence: ",
                                    AppState.leaderboard_confidence,
                                    variant="outline",
                                    size="1",
                                ),
                                spacing="2",
                            ),
                            align="center",
                            width="100%",
                        ),
                        rx.text(AppState.leaderboard_plan_summary, size="2"),
                        rx.cond(
                            AppState.leaderboard_rationale != "",
                            rx.text(
                                AppState.leaderboard_rationale,
                                size="1",
                                color="gray",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    padding="12px",
                    border_radius="8px",
                    background="var(--green-2)",
                    border="1px solid var(--green-6)",
                    width="100%",
                ),
                rx.fragment(),
            ),
            # Error display
            rx.cond(
                AppState.leaderboard_suggest_error != "",
                rx.box(
                    rx.hstack(
                        rx.icon("circle_alert", size=14, color="var(--red-9)"),
                        rx.text(
                            AppState.leaderboard_suggest_error,
                            size="2",
                            color="var(--red-11)",
                        ),
                        align="center",
                        spacing="2",
                    ),
                    padding="8px 12px",
                    border_radius="8px",
                    background="var(--red-2)",
                    border="1px solid var(--red-6)",
                    width="100%",
                ),
                rx.fragment(),
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


# =========================================================================
# Manual filter section
# =========================================================================

def _filter_select(label: str, options, value, on_change) -> rx.Component:
    """Compact labeled filter select."""
    is_active = value != "All"
    return rx.box(
        rx.vstack(
            rx.text(
                label,
                size="1",
                weight="medium",
                color=rx.cond(is_active, "var(--accent-11)", "var(--gray-10)"),
                letter_spacing="0.05em",
                text_transform="uppercase",
            ),
            rx.select(
                options,
                value=value,
                on_change=on_change,
                size="2",
                width="100%",
                variant=rx.cond(is_active, "soft", "surface"),
                color_scheme=rx.cond(is_active, "indigo", "gray"),
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        flex="1",
        min_width="120px",
    )


def _manual_filter_section() -> rx.Component:
    active_count = (
        rx.cond(AppState.language_filter != "All", 1, 0)
        + rx.cond(AppState.subject_filter != "All", 1, 0)
        + rx.cond(AppState.task_type_filter != "All", 1, 0)
    )
    return rx.box(
        rx.vstack(
            # Header row
            rx.hstack(
                rx.hstack(
                    rx.icon("sliders_horizontal", size=15, color="var(--gray-9)"),
                    rx.text("Filters", size="2", weight="medium", color="var(--gray-11)"),
                    rx.cond(
                        active_count > 0,
                        rx.badge(
                            active_count,
                            color_scheme="indigo",
                            variant="solid",
                            size="1",
                            radius="full",
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.cond(
                    active_count > 0,
                    rx.button(
                        rx.icon("x", size=12),
                        "Reset",
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=[
                            AppState.set_language_filter("All"),
                            AppState.set_subject_filter("All"),
                            AppState.set_task_type_filter("All"),
                        ],
                        cursor="pointer",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                align="center",
            ),
            # Filter row
            rx.flex(
                _filter_select(
                    "Language",
                    AppState.leaderboard_language_options,
                    AppState.language_filter,
                    AppState.set_language_filter,
                ),
                _filter_select(
                    "Subject",
                    AppState.leaderboard_subject_options,
                    AppState.subject_filter,
                    AppState.set_subject_filter,
                ),
                _filter_select(
                    "Task Type",
                    AppState.leaderboard_task_type_options,
                    AppState.task_type_filter,
                    AppState.set_task_type_filter,
                ),
                # Max results compact
                rx.box(
                    rx.vstack(
                        rx.text(
                            "Max",
                            size="1",
                            weight="medium",
                            color="var(--gray-10)",
                            letter_spacing="0.05em",
                            text_transform="uppercase",
                        ),
                        rx.input(
                            value=AppState.max_results,
                            on_change=AppState.set_max_results,
                            type="number",
                            step=10,
                            size="2",
                            width="80px",
                        ),
                        spacing="1",
                        align="start",
                    ),
                    flex_shrink="0",
                ),
                # Load button
                rx.box(
                    rx.vstack(
                        rx.text(" ", size="1"),
                        rx.button(
                            rx.icon("search", size=14),
                            "Load",
                            size="2",
                            color_scheme="indigo",
                            variant="solid",
                            on_click=AppState.load_leaderboard_data,
                            loading=AppState.leaderboard_loading,
                            cursor="pointer",
                        ),
                        spacing="1",
                        align="start",
                    ),
                    flex_shrink="0",
                ),
                gap="3",
                wrap="wrap",
                align="end",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        padding="1rem 1.25rem",
        border_radius="var(--radius-4)",
        background="var(--gray-2)",
        border="1px solid var(--gray-4)",
        width="100%",
    )


# =========================================================================
# Page
# =========================================================================

def leaderboard_page() -> rx.Component:
    """Leaderboard browsing page."""
    return rx.cond(
        AppState.is_authenticated,
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("trophy", size=24, color="var(--accent-9)"),
                    rx.heading("Browse Leaderboards", size="6"),
                    spacing="3",
                    align="center",
                ),
                rx.spacer(),
                rx.text(
                    AppState.leaderboard_entries.length(),
                    " entries",
                    size="2",
                    color="var(--gray-9)",
                ),
                width="100%",
                align="center",
                margin_bottom="0.5rem",
            ),
            # Rankings table
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.hstack(
                            rx.icon(
                                "bar_chart_3", size=18, color="var(--accent-9)"
                            ),
                            rx.text(
                                "Model Performance Rankings",
                                weight="bold",
                                size="3",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("refresh_cw", size=14),
                            "Refresh",
                            size="2",
                            variant="soft",
                            on_click=AppState.load_leaderboard_data,
                            loading=AppState.leaderboard_loading,
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.cond(
                        AppState.leaderboard_query_description != "",
                        rx.box(
                            rx.hstack(
                                rx.icon(
                                    "info", size=14, color="var(--accent-9)"
                                ),
                                rx.text(
                                    AppState.leaderboard_query_description,
                                    size="2",
                                    color="var(--accent-11)",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            padding="8px 12px",
                            background="var(--accent-2)",
                            border_radius="var(--radius-2)",
                            border="1px solid var(--accent-5)",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        AppState.leaderboard_entries.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Rank"),
                                    rx.table.column_header_cell("Model"),
                                    rx.table.column_header_cell("Language"),
                                    rx.table.column_header_cell("Subject"),
                                    rx.table.column_header_cell("Task Type"),
                                    rx.table.column_header_cell("Score"),
                                    rx.table.column_header_cell("Updated"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    AppState.leaderboard_entries,
                                    _leaderboard_table_row,
                                )
                            ),
                            width="100%",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon(
                                    "table_2", size=32, color="var(--gray-6)"
                                ),
                                rx.text(
                                    "No leaderboard data yet",
                                    color="var(--gray-9)",
                                    size="3",
                                    weight="medium",
                                ),
                                rx.text(
                                    "Use AI Search or apply filters to load results.",
                                    color="var(--gray-8)",
                                    size="2",
                                ),
                                align="center",
                                spacing="2",
                            ),
                            padding="3rem",
                        ),
                    ),
                    align="start",
                    spacing="3",
                    width="100%",
                ),
                width="100%",
            ),
            _ai_search_section(),
            _manual_filter_section(),
            width="100%",
            align="start",
            spacing="4",
        ),
        login_required_card("Please log in to browse leaderboards."),
    )
