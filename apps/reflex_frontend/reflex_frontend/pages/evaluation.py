"""Evaluation page — 2-step wizard: (1) query input, (2) configure & submit."""

import reflex as rx

from ..state import AppState
from ..components.layout import login_required_card


# =========================================================================
# Step 1 — Centered query input  (Arena-style)
# =========================================================================

_EXAMPLES = [
    "Best model for Korean math reasoning",
    "English coding knowledge benchmark",
    "Which model excels at science reasoning?",
    "Korean culture knowledge evaluation results",
]


def _example_chip(text: str) -> rx.Component:
    return rx.button(
        rx.icon("arrow_up_right", size=11),
        text,
        on_click=AppState.set_query(text),
        variant="ghost",
        size="1",
        color_scheme="gray",
        cursor="pointer",
        border_radius="full",
        border="1px solid var(--gray-4)",
        color="var(--gray-10)",
        padding="0.3rem 0.75rem",
        _hover={"background": "var(--gray-3)", "color": "var(--gray-12)", "border_color": "var(--gray-6)"},
        transition="all 0.15s ease",
    )


def _eval_input_step() -> rx.Component:
    """Full-height centered query screen."""
    return rx.center(
        rx.vstack(
            # Icon
            rx.box(
                rx.icon("sparkles", size=32, color="var(--accent-9)"),
                padding="0.75rem",
                border_radius="var(--radius-4)",
                background="var(--accent-3)",
            ),
            # Heading
            rx.vstack(
                rx.heading(
                    "Describe what you want to evaluate",
                    size="7",
                    weight="bold",
                    text_align="center",
                    color="var(--gray-12)",
                    line_height="1.15",
                ),
                rx.text(
                    "in natural language.",
                    size="7",
                    weight="bold",
                    text_align="center",
                    color="var(--accent-10)",
                    line_height="1.15",
                ),
                spacing="0",
                align="center",
            ),
            rx.text(
                "BenchHub Plus will automatically select benchmarks, plan data, and estimate costs.",
                size="3",
                color="var(--gray-9)",
                text_align="center",
                max_width="480px",
            ),
            # Input card
            rx.box(
                rx.vstack(
                    rx.text_area(
                        placeholder="e.g. Best model for Korean math reasoning",
                        value=AppState.query,
                        on_change=AppState.set_query,
                        width="100%",
                        size="3",
                        min_height="110px",
                        border="none",
                        outline="none",
                        resize="none",
                        background="transparent",
                        _focus={"outline": "none", "box_shadow": "none"},
                        font_size="1rem",
                        line_height="1.6",
                        padding="1rem 1.25rem 0.75rem",
                    ),
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            rx.icon("arrow_right", size=16),
                            on_click=AppState.submit_query,
                            loading=AppState.is_submitting,
                            color_scheme="blue",
                            size="2",
                            border_radius="var(--radius-3)",
                        ),
                        padding="0 1rem 0.75rem",
                        width="100%",
                        align="center",
                    ),
                    spacing="0",
                    width="100%",
                ),
                class_name="eval-input-box",
                border="1.5px solid var(--gray-5)",
                border_radius="var(--radius-4)",
                background="var(--color-surface)",
                width="100%",
                box_shadow="0 2px 12px var(--gray-a3)",
                transition="box-shadow 0.2s ease",
                _hover={"box_shadow": "0 4px 20px var(--gray-a4)"},
            ),
            # Off-topic / invalid query error
            rx.cond(
                AppState.eval_is_off_topic,
                rx.box(
                    rx.hstack(
                        rx.icon("message_circle_question", size=16, color="var(--orange-9)"),
                        rx.vstack(
                            rx.text("This doesn't look like an evaluation query", weight="bold", size="2", color="var(--orange-11)"),
                            rx.text(AppState.eval_off_topic_message, size="2", color="var(--orange-11)", white_space="pre-wrap"),
                            spacing="1",
                            align="start",
                        ),
                        spacing="3",
                        align="start",
                        width="100%",
                    ),
                    padding="0.875rem 1rem",
                    border_radius="var(--radius-3)",
                    background="var(--orange-2)",
                    border="1px solid var(--orange-6)",
                    width="100%",
                ),
                rx.fragment(),
            ),
            # Example prompts below the box
            rx.vstack(
                rx.text("Try an example:", size="1", color="var(--gray-8)"),
                rx.vstack(
                    *[_example_chip(e) for e in _EXAMPLES],
                    spacing="1",
                    width="100%",
                    align="center",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            max_width="660px",
            width="100%",
            spacing="5",
            align="center",
        ),
        min_height="72vh",
        width="100%",
        padding_top="2rem",
    )


# =========================================================================
# Step 2 — Configure tabs
# =========================================================================

def _config_tab_btn(tab_id: str, icon_name: str, label: str, color: str) -> rx.Component:
    """One of the three configuration tab cards."""
    is_active = AppState.eval_config_tab == tab_id
    return rx.box(
        rx.vstack(
            rx.box(
                rx.icon(
                    icon_name,
                    size=22,
                    color=rx.cond(is_active, f"var(--{color}-9)", "var(--gray-8)"),
                ),
                padding="0.6rem",
                border_radius="var(--radius-3)",
                background=rx.cond(is_active, f"var(--{color}-3)", "var(--gray-3)"),
            ),
            rx.text(
                label,
                size="2",
                weight=rx.cond(is_active, "bold", "medium"),
                color=rx.cond(is_active, f"var(--{color}-11)", "var(--gray-10)"),
                text_align="center",
            ),
            spacing="2",
            align="center",
        ),
        on_click=AppState.set_eval_tab(tab_id),
        flex="1",
        padding="1rem 0.75rem",
        border_radius="var(--radius-3)",
        border=rx.cond(
            is_active,
            f"2px solid var(--{color}-7)",
            "2px solid var(--gray-4)",
        ),
        background=rx.cond(is_active, f"var(--{color}-2)", "var(--gray-1)"),
        cursor="pointer",
        text_align="center",
        class_name="tab-appear",
        transition="all 0.2s ease",
        _hover=rx.cond(
            is_active,
            {"background": f"var(--{color}-3)"},
            {"background": "var(--gray-2)", "border_color": "var(--gray-6)"},
        ),
    )


# ---- Model config panel -------------------------------------------------

def _model_form(index: rx.Var[int]) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("bot", size=15, color="var(--accent-9)"),
                    rx.text("Model ", index + 1, weight="bold", size="2"),
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
                    rx.text("Model Name", weight="medium", size="1", color="var(--gray-10)"),
                    rx.input(
                        placeholder="e.g. gpt-4o, claude-3.5-sonnet",
                        value=AppState.models[index]["name"],
                        on_change=lambda v: AppState.update_model(index, "name", v),
                        width="100%",
                        size="2",
                    ),
                    rx.cond(
                        AppState.recent_model_names.length() > 0,
                        rx.flex(
                            rx.foreach(
                                AppState.recent_model_names,
                                lambda name: rx.badge(
                                    name,
                                    on_click=AppState.update_model(index, "name", name),
                                    variant="outline",
                                    color_scheme="gray",
                                    size="1",
                                    cursor="pointer",
                                    _hover={"background": "var(--accent-3)", "color": "var(--accent-11)"},
                                ),
                            ),
                            gap="1",
                            wrap="wrap",
                        ),
                        rx.fragment(),
                    ),
                    align="start", width="100%", spacing="1",
                ),
                rx.vstack(
                    rx.text("Model Type", weight="medium", size="1", color="var(--gray-10)"),
                    rx.select(
                        ["openai", "anthropic", "huggingface", "custom"],
                        value=AppState.models[index]["model_type"],
                        on_change=lambda v: AppState.update_model(index, "model_type", v),
                        width="100%",
                        size="2",
                    ),
                    align="start", width="100%", spacing="1",
                ),
                rx.vstack(
                    rx.text("API Base URL", weight="medium", size="1", color="var(--gray-10)"),
                    rx.input(
                        placeholder="https://api.openai.com/v1",
                        value=AppState.models[index]["api_base"],
                        on_change=lambda v: AppState.update_model(index, "api_base", v),
                        width="100%",
                        size="2",
                    ),
                    align="start", width="100%", spacing="1",
                ),
                rx.vstack(
                    rx.text("API Key", weight="medium", size="1", color="var(--gray-10)"),
                    rx.input(
                        placeholder="sk-...",
                        type="password",
                        value=AppState.models[index]["api_key"],
                        on_change=lambda v: AppState.update_model(index, "api_key", v),
                        width="100%",
                        size="2",
                    ),
                    align="start", width="100%", spacing="1",
                ),
                columns="2",
                spacing="3",
                width="100%",
            ),
            align="start", spacing="3", width="100%",
        ),
        width="100%",
        padding="0.875rem 1rem",
        border_radius="var(--radius-3)",
        border="1px solid var(--gray-4)",
        background="var(--gray-1)",
    )


def _model_config_panel() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Configure the models you want to compare.", size="2", color="var(--gray-9)"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                "Add Model",
                on_click=AppState.add_model,
                variant="soft",
                size="2",
                disabled=rx.cond(AppState.models.length() >= 10, True, False),
            ),
            width="100%",
            align="center",
        ),
        rx.cond(
            AppState.models.length() > 0,
            rx.vstack(
                rx.foreach(rx.Var.range(AppState.models.length()), _model_form),
                width="100%",
                spacing="3",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("bot", size=28, color="var(--gray-6)"),
                    rx.text("No models yet", color="var(--gray-9)", size="2", weight="medium", text_align="center"),
                    rx.text("Click 'Add Model' to get started.", color="var(--gray-8)", size="2", text_align="center"),
                    align="center", spacing="2",
                ),
                padding="2.5rem",
                width="100%",
            ),
        ),
        width="100%",
        spacing="3",
        align="start",
    )


# ---- Data review panel --------------------------------------------------

def _data_review_panel() -> rx.Component:
    has_suggestion = (
        (AppState.eval_suggested_language != "")
        | (AppState.eval_suggested_subject != "")
        | (AppState.eval_suggested_task_type != "")
    )

    combo_chip = rx.button(
        rx.cond(
            AppState.eval_suggested_language != "",
            rx.hstack(rx.icon("globe", size=13), rx.text(AppState.eval_suggested_language, size="2"), spacing="1"),
            rx.fragment(),
        ),
        rx.cond(
            AppState.eval_suggested_subject != "",
            rx.hstack(rx.icon("book_open", size=13), rx.text(AppState.eval_suggested_subject, size="2"), spacing="1"),
            rx.fragment(),
        ),
        rx.cond(
            AppState.eval_suggested_task_type != "",
            rx.hstack(rx.icon("layers", size=13), rx.text(AppState.eval_suggested_task_type, size="2"), spacing="1"),
            rx.fragment(),
        ),
        rx.cond(
            AppState.eval_data_expanded,
            rx.icon("chevron_up", size=13),
            rx.icon("chevron_down", size=13),
        ),
        on_click=AppState.load_data_review_samples,
        variant=rx.cond(AppState.eval_data_expanded, "solid", "soft"),
        color_scheme="indigo",
        size="2",
        cursor="pointer",
        gap="2",
    )

    return rx.vstack(
        rx.text(
            "Benchmark categories suggested based on your query. Click to preview sample questions.",
            size="2",
            color="var(--gray-9)",
        ),
        # Single combo chip + remove button (or placeholder)
        rx.cond(
            has_suggestion,
            rx.hstack(
                combo_chip,
                rx.icon_button(
                    rx.icon("x", size=13),
                    on_click=AppState.clear_suggested_combo,
                    variant="ghost",
                    color_scheme="gray",
                    size="1",
                    tooltip="Remove suggestion",
                    opacity="0.5",
                    _hover={"opacity": "1", "color": "var(--red-9)"},
                ),
                spacing="1",
                align="center",
            ),
            rx.badge(
                rx.icon("loader", size=13),
                "Categories will appear after query analysis",
                variant="outline",
                color_scheme="gray",
                size="2",
            ),
        ),
        # Expandable sample panel
        rx.cond(
            AppState.eval_data_expanded,
            rx.box(
                rx.cond(
                    AppState.eval_data_loading,
                    rx.hstack(
                        rx.spinner(size="2"),
                        rx.text("Loading sample questions...", size="2", color="var(--gray-9)"),
                        spacing="2", align="center", padding="1rem",
                    ),
                    rx.cond(
                        AppState.eval_data_entries.length() > 0,
                        rx.vstack(
                            rx.hstack(
                                rx.icon("file_text", size=14, color="var(--gray-9)"),
                                rx.text("Sample questions (up to 5)", size="1", weight="medium", color="var(--gray-9)"),
                                spacing="1", align="center",
                            ),
                            rx.foreach(
                                AppState.eval_data_entries,
                                lambda e: rx.box(
                                    rx.vstack(
                                        rx.hstack(
                                            rx.badge(e["subject_type"], variant="soft", color_scheme="blue", size="1"),
                                            rx.badge(e["task_type"], variant="soft", color_scheme="purple", size="1"),
                                            rx.badge(e["problem_type"], variant="soft", color_scheme="gray", size="1"),
                                            rx.spacer(),
                                            rx.text(e["benchmark_name"], size="1", color="var(--gray-7)"),
                                            spacing="1", align="center", width="100%", wrap="wrap",
                                        ),
                                        rx.text(
                                            e["prompt"],
                                            size="2",
                                            color="var(--gray-12)",
                                            line_clamp="3",
                                        ),
                                        spacing="2", align="start", width="100%",
                                    ),
                                    padding="0.75rem",
                                    border="1px solid var(--gray-4)",
                                    border_radius="var(--radius-2)",
                                    background="var(--color-surface)",
                                    width="100%",
                                ),
                            ),
                            spacing="2", width="100%", align="start",
                        ),
                        rx.hstack(
                            rx.icon("inbox", size=16, color="var(--gray-7)"),
                            rx.text(
                                "No sample questions found for this combination.",
                                size="2", color="var(--gray-8)",
                            ),
                            spacing="2", align="center", padding="1rem",
                        ),
                    ),
                ),
                border="1px solid var(--gray-4)",
                border_radius="var(--radius-3)",
                background="var(--gray-1)",
                width="100%",
                padding="0.75rem",
            ),
            rx.fragment(),
        ),
        # Info note
        rx.box(
            rx.hstack(
                rx.icon("info", size=13, color="var(--blue-9)"),
                rx.text(
                    "Final benchmarks are determined after submission. You can also adjust filters directly on the Leaderboard page.",
                    size="1", color="var(--blue-11)",
                ),
                spacing="2", align="start",
            ),
            padding="0.625rem 0.875rem",
            background="var(--blue-2)",
            border_radius="var(--radius-2)",
            border="1px solid var(--blue-4)",
            width="100%",
        ),
        width="100%",
        spacing="3",
        align="start",
    )


# ---- Cost planning panel ------------------------------------------------

def _cost_planning_panel() -> rx.Component:
    model_count = AppState.models.length()

    def _scale_btn(val: str, label: str, desc: str) -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.text(label, size="2", weight="bold"),
                rx.text(desc, size="1", color="var(--gray-9)"),
                spacing="0", align="start",
            ),
            padding="0.75rem 1rem",
            border=rx.cond(
                AppState.sample_scale == val,
                "1.5px solid var(--accent-7)",
                "1px solid var(--gray-4)",
            ),
            border_radius="var(--radius-3)",
            background=rx.cond(
                AppState.sample_scale == val,
                "var(--accent-2)",
                "var(--color-surface)",
            ),
            cursor="pointer",
            on_click=AppState.set_sample_scale(val),
            flex="1",
            min_width="120px",
            _hover={"border_color": "var(--accent-6)"},
            transition="all 0.15s ease",
        )

    # Dynamic sample count display
    sample_display = rx.cond(
        AppState.sample_scale == "small",  "50",
        rx.cond(AppState.sample_scale == "medium", "100",
        rx.cond(AppState.sample_scale == "large",  "250",
        rx.cond(AppState.sample_scale == "full",   "500",
        rx.cond(AppState.custom_sample_count != "", AppState.custom_sample_count,
        "—")))))

    return rx.vstack(
        # Data Scale picker
        rx.vstack(
            rx.hstack(
                rx.icon("gauge", size=15, color="var(--accent-9)"),
                rx.text("Data Scale", weight="bold", size="2"),
                spacing="2", align="center",
            ),
            rx.text(
                "More samples improve accuracy but increase cost and time.",
                size="1", color="var(--gray-9)",
            ),
            rx.flex(
                _scale_btn("small",  "Small",  "50 · Fast"),
                _scale_btn("medium", "Medium", "100 · Balanced"),
                _scale_btn("large",  "Large",  "250 · Thorough"),
                _scale_btn("full",   "Full",   "500 · Comprehensive"),
                # Custom number input
                rx.box(
                    rx.vstack(
                        rx.text("Custom", size="2", weight="bold"),
                        rx.input(
                            placeholder="e.g. 150",
                            value=AppState.custom_sample_count,
                            on_change=AppState.set_custom_sample_count,
                            size="1",
                            width="80px",
                            type="number",
                            min="1",
                            max="10000",
                        ),
                        spacing="0", align="start",
                    ),
                    padding="0.75rem 1rem",
                    border=rx.cond(
                        AppState.sample_scale == "custom",
                        "1.5px solid var(--accent-7)",
                        "1px solid var(--gray-4)",
                    ),
                    border_radius="var(--radius-3)",
                    background=rx.cond(
                        AppState.sample_scale == "custom",
                        "var(--accent-2)",
                        "var(--color-surface)",
                    ),
                    min_width="100px",
                    _hover={"border_color": "var(--accent-6)"},
                    transition="all 0.15s ease",
                ),
                spacing="2",
                width="100%",
                flex_wrap="wrap",
            ),
            spacing="2", align="start", width="100%",
        ),
        rx.separator(width="100%"),
        rx.text(
            "Estimated resource usage for this evaluation run.",
            size="2",
            color="var(--gray-9)",
        ),
        rx.grid(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("bot", size=16, color="var(--blue-9)"),
                        rx.text("Models", weight="bold", size="2"),
                        spacing="2", align="center",
                    ),
                    rx.heading(model_count, size="6", weight="bold", color="var(--blue-11)"),
                    rx.text("model(s) configured", size="1", color="var(--gray-9)"),
                    spacing="1", align="start", width="100%",
                ),
                padding="1rem",
                border="1px solid var(--blue-4)",
                border_radius="var(--radius-3)",
                background="var(--blue-1)",
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("database", size=16, color="var(--green-9)"),
                        rx.text("Samples", weight="bold", size="2"),
                        spacing="2", align="center",
                    ),
                    rx.heading(sample_display, size="6", weight="bold", color="var(--green-11)"),
                    rx.text("samples per model", size="1", color="var(--gray-9)"),
                    spacing="1", align="start", width="100%",
                ),
                padding="1rem",
                border="1px solid var(--green-4)",
                border_radius="var(--radius-3)",
                background="var(--green-1)",
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("clock", size=16, color="var(--orange-9)"),
                        rx.text("Est. Time", weight="bold", size="2"),
                        spacing="2", align="center",
                    ),
                    rx.heading("5–15 min", size="6", weight="bold", color="var(--orange-11)"),
                    rx.text("depending on API latency", size="1", color="var(--gray-9)"),
                    spacing="1", align="start", width="100%",
                ),
                padding="1rem",
                border="1px solid var(--orange-4)",
                border_radius="var(--radius-3)",
                background="var(--orange-1)",
                flex="1",
            ),
            columns="3",
            spacing="3",
            width="100%",
        ),
        rx.box(
            rx.hstack(
                rx.icon("triangle_alert", size=14, color="var(--orange-9)"),
                rx.text(
                    "API costs depend on your provider's pricing. BenchHub Plus does not charge separately.",
                    size="1",
                    color="var(--orange-11)",
                ),
                spacing="2",
                align="start",
            ),
            padding="0.625rem 0.875rem",
            background="var(--orange-2)",
            border_radius="var(--radius-2)",
            border="1px solid var(--orange-4)",
            width="100%",
        ),
        width="100%",
        spacing="3",
        align="start",
    )


# =========================================================================
# Step 2 — Configure wrapper
# =========================================================================

def _eval_configure_step() -> rx.Component:
    return rx.vstack(
        # Hidden button triggered by swipe-left gesture (JS below)
        rx.button(
            id="swipe-back-btn",
            on_click=AppState.back_to_query,
            display="none",
        ),
        # Swipe-left → back gesture (touch + mouse drag)
        rx.script("""
(function() {
  var sx = 0, sy = 0;
  function onStart(x, y) { sx = x; sy = y; }
  function onEnd(x, y) {
    var dx = x - sx, dy = y - sy;
    if (dx < -80 && Math.abs(dx) > Math.abs(dy) * 1.5) {
      var btn = document.getElementById('swipe-back-btn');
      if (btn) btn.click();
    }
  }
  document.addEventListener('touchstart', function(e) {
    onStart(e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });
  document.addEventListener('touchend', function(e) {
    onEnd(e.changedTouches[0].clientX, e.changedTouches[0].clientY);
  }, { passive: true });
  document.addEventListener('mousedown', function(e) { onStart(e.clientX, e.clientY); });
  document.addEventListener('mouseup',   function(e) { onEnd(e.clientX,   e.clientY);   });
})();
"""),
        # Stats bar
        _eval_stats_bar(),
        # Back button + submitted query chip
        rx.hstack(
            rx.button(
                rx.icon("arrow_left", size=14),
                "Back",
                on_click=AppState.back_to_query,
                variant="ghost",
                color_scheme="gray",
                size="2",
                cursor="pointer",
            ),
            rx.box(
                rx.hstack(
                    rx.icon("sparkles", size=13, color="var(--accent-9)"),
                    rx.text(
                        AppState.query,
                        size="2",
                        color="var(--gray-11)",
                        weight="medium",
                        flex="1",
                        no_of_lines=1,
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                padding="0.5rem 0.875rem",
                border="1px solid var(--gray-4)",
                border_radius="full",
                background="var(--gray-2)",
                flex="1",
                min_width="0",
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        # 3 config tabs
        rx.hstack(
            _config_tab_btn("model", "bot", "Model Selection", "blue"),
            _config_tab_btn("data", "database", "Data Review", "green"),
            _config_tab_btn("cost", "dollar_sign", "Cost Planning", "orange"),
            spacing="3",
            width="100%",
        ),
        # Tab content
        rx.box(
            rx.cond(
                AppState.eval_config_tab == "model",
                _model_config_panel(),
                rx.cond(
                    AppState.eval_config_tab == "data",
                    _data_review_panel(),
                    _cost_planning_panel(),
                ),
            ),
            padding="1.25rem",
            border="1px solid var(--gray-4)",
            border_radius="var(--radius-3)",
            background="var(--color-surface)",
            width="100%",
        ),
        # Submit
        rx.center(
            rx.button(
                rx.icon("rocket", size=18),
                "Start Evaluation",
                size="4",
                color_scheme="blue",
                loading=AppState.is_submitting,
                width="300px",
                disabled=rx.cond(AppState.models.length() == 0, True, False),
                on_click=AppState.submit_evaluation,
            ),
            width="100%",
            padding_top="0.5rem",
        ),
        width="100%",
        spacing="4",
        align="start",
    )


# =========================================================================
# Stats bar (configure step only)
# =========================================================================

def _eval_stats_bar() -> rx.Component:
    def _stat(icon_name, label, value, color):
        return rx.hstack(
            rx.box(
                rx.icon(icon_name, size=14, color=f"var(--{color}-9)"),
                padding="6px",
                border_radius="var(--radius-2)",
                background=f"var(--{color}-3)",
            ),
            rx.vstack(
                rx.text(value, size="3", weight="bold", color=f"var(--{color}-11)"),
                rx.text(label, size="1", color="var(--gray-9)"),
                spacing="0",
                align="start",
                line_height="1",
            ),
            spacing="2",
            align="center",
        )

    return rx.hstack(
        rx.heading("Evaluation", size="5", weight="bold"),
        rx.spacer(),
        _stat("layers", "Total", AppState.total_task_count, "gray"),
        rx.box(width="1px", height="28px", background="var(--gray-4)"),
        _stat("loader", "Running", AppState.running_task_count, "blue"),
        rx.box(width="1px", height="28px", background="var(--gray-4)"),
        _stat("circle_check", "Completed", AppState.completed_task_count, "green"),
        rx.box(width="1px", height="28px", background="var(--gray-4)"),
        _stat("clock", "Pending", AppState.pending_task_count, "orange"),
        rx.button(
            rx.icon("refresh_cw", size=13),
            on_click=AppState.refresh_current_task,
            variant="ghost",
            color_scheme="gray",
            size="2",
            disabled=rx.cond(AppState.total_task_count == 0, True, False),
            cursor="pointer",
        ),
        width="100%",
        align="center",
        spacing="3",
        padding="0.75rem 1rem",
        background="var(--gray-1)",
        border="1px solid var(--gray-4)",
        border_radius="var(--radius-3)",
    )


# =========================================================================
# Step 3 — Task detail view
# =========================================================================

def _task_detail_view() -> rx.Component:
    task = AppState.selected_task

    status_cfg = rx.cond(
        task["status"] == "completed",
        {"color": "green", "icon": "circle_check", "label": "Completed"},
        rx.cond(
            task["status"] == "running",
            {"color": "blue", "icon": "loader", "label": "Running"},
            rx.cond(
                task["status"] == "pending",
                {"color": "orange", "icon": "clock", "label": "Pending"},
                rx.cond(
                    task["status"] == "cancelled",
                    {"color": "gray", "icon": "x_circle", "label": "Cancelled"},
                    {"color": "red", "icon": "circle_x", "label": "Failed"},
                ),
            ),
        ),
    )

    can_cancel = (task["status"] == "pending") | (task["status"] == "running")

    return rx.vstack(
        _eval_stats_bar(),
        # Header row
        rx.hstack(
            rx.button(
                rx.icon("arrow_left", size=14),
                "Back",
                on_click=AppState.set_eval_step("input"),
                variant="ghost",
                color_scheme="gray",
                size="2",
                cursor="pointer",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("refresh_cw", size=13),
                "Refresh",
                id="task-refresh-btn",
                on_click=AppState.refresh_task_status(task["id"]),
                variant="soft",
                color_scheme="gray",
                size="2",
            ),
            width="100%",
            align="center",
        ),
        # Status card
        rx.box(
            rx.hstack(
                rx.box(
                    rx.icon(status_cfg["icon"], size=20),
                    padding="0.6rem",
                    border_radius="var(--radius-3)",
                    background=f"var(--{status_cfg['color']}-3)",
                    color=f"var(--{status_cfg['color']}-9)",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.badge(
                            status_cfg["label"],
                            color_scheme=status_cfg["color"],
                            variant="soft",
                            size="2",
                        ),
                        rx.text(
                            task["id"],
                            size="1",
                            color="var(--gray-8)",
                            font_family="monospace",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        task["created_at"],
                        size="1",
                        color="var(--gray-9)",
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            padding="1rem",
            border="1px solid var(--gray-4)",
            border_radius="var(--radius-3)",
            background="var(--gray-1)",
            width="100%",
        ),
        # Query
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("sparkles", size=14, color="var(--accent-9)"),
                    rx.text("Query", weight="bold", size="2"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    task["query"],
                    size="2",
                    color="var(--gray-12)",
                    white_space="pre-wrap",
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            padding="1rem",
            border="1px solid var(--gray-4)",
            border_radius="var(--radius-3)",
            background="var(--color-surface)",
            width="100%",
        ),
        # Evaluation config card (models + sample scale + labels)
        rx.box(
            rx.vstack(
                # Section header
                rx.hstack(
                    rx.icon("settings_2", size=14, color="var(--blue-9)"),
                    rx.text("Evaluation Config", weight="bold", size="2"),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.divider(),
                # Models
                rx.vstack(
                    rx.text("Models", size="1", weight="medium", color="var(--gray-10)"),
                    rx.cond(
                        AppState.selected_task_models.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                AppState.selected_task_models,
                                lambda m: rx.box(
                                    rx.vstack(
                                        rx.hstack(
                                            rx.icon("bot", size=12, color="var(--blue-9)"),
                                            rx.text(m["name"], size="2", weight="medium", color="var(--blue-11)"),
                                            spacing="1",
                                            align="center",
                                        ),
                                        rx.hstack(
                                            rx.text("Type:", size="1", color="var(--gray-9)"),
                                            rx.text(m["model_type"], size="1", color="var(--gray-11)"),
                                            rx.text("·", size="1", color="var(--gray-6)"),
                                            rx.text("Endpoint:", size="1", color="var(--gray-9)"),
                                            rx.text(m["api_base"], size="1", color="var(--gray-11)", max_width="220px", overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
                                            spacing="1",
                                            align="center",
                                        ),
                                        spacing="1",
                                        align="start",
                                    ),
                                    padding="0.5rem 0.75rem",
                                    border="1px solid var(--blue-4)",
                                    border_radius="var(--radius-2)",
                                    background="var(--blue-1)",
                                    width="100%",
                                ),
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        rx.badge(
                            task["model_name"],
                            variant="soft",
                            color_scheme="blue",
                            size="2",
                        ),
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                ),
                # Sample scale
                rx.vstack(
                    rx.text("Sample Size", size="1", weight="medium", color="var(--gray-10)"),
                    rx.cond(
                        AppState.selected_task_sample_scale != "",
                        rx.badge(
                            AppState.selected_task_sample_label,
                            variant="soft",
                            color_scheme="violet",
                            size="2",
                        ),
                        rx.text("—", size="2", color="var(--gray-9)"),
                    ),
                    spacing="1",
                    align="start",
                    width="100%",
                ),
                # Category labels (language / subject / task_type from suggest)
                rx.cond(
                    AppState.selected_task_labels.length() > 0,
                    rx.vstack(
                        rx.text("Category Labels", size="1", weight="medium", color="var(--gray-10)"),
                        rx.hstack(
                            rx.cond(
                                AppState.selected_task_labels.length() > 0,
                                rx.badge(
                                    AppState.selected_task_labels[0],
                                    variant="soft",
                                    color_scheme="blue",
                                    size="2",
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                AppState.selected_task_labels.length() > 1,
                                rx.badge(
                                    AppState.selected_task_labels[1],
                                    variant="soft",
                                    color_scheme="green",
                                    size="2",
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                AppState.selected_task_labels.length() > 2,
                                rx.badge(
                                    AppState.selected_task_labels[2],
                                    variant="soft",
                                    color_scheme="orange",
                                    size="2",
                                ),
                                rx.fragment(),
                            ),
                            spacing="2",
                            flex_wrap="wrap",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            padding="1rem",
            border="1px solid var(--gray-4)",
            border_radius="var(--radius-3)",
            background="var(--color-surface)",
            width="100%",
        ),
        # Progress panel (running / pending)
        rx.cond(
            (task["status"] == "running") | (task["status"] == "pending"),
            rx.box(
                rx.vstack(
                    # Header row
                    rx.hstack(
                        rx.icon("loader", size=14, color="var(--blue-9)"),
                        rx.text("Evaluation in progress", size="2", color="var(--blue-11)", weight="medium"),
                        rx.spacer(),
                        rx.text(task["progress"], "%", size="2", weight="bold", color="var(--blue-11)"),
                        width="100%",
                        align="center",
                    ),
                    rx.progress(value=task["progress"], width="100%", color_scheme="blue"),
                    # Stage indicator
                    rx.cond(
                        AppState.selected_task_stage != "",
                        rx.hstack(
                            rx.icon("circle_dot", size=12, color="var(--blue-9)"),
                            rx.text(
                                AppState.selected_task_stage,
                                size="2",
                                color="var(--blue-11)",
                            ),
                            spacing="1",
                            align="center",
                        ),
                        rx.fragment(),
                    ),
                    # Pipeline step indicators (active step highlighted)
                    rx.hstack(
                        *[
                            rx.fragment(
                                rx.text(
                                    label,
                                    size="1",
                                    weight=rx.cond(AppState.selected_task_stage_index == idx, "bold", "regular"),
                                    color=rx.cond(
                                        AppState.selected_task_stage_index > idx,
                                        "var(--green-9)",
                                        rx.cond(
                                            AppState.selected_task_stage_index == idx,
                                            "var(--blue-11)",
                                            "var(--gray-8)",
                                        ),
                                    ),
                                ),
                                rx.cond(
                                    idx < 4,
                                    rx.text("→", size="1", color="var(--gray-6)"),
                                    rx.fragment(),
                                ),
                            )
                            for idx, label in enumerate([
                                "① Initialize",
                                "② Validate",
                                "③ Run benchmark",
                                "④ Map results",
                                "⑤ Store",
                            ])
                        ],
                        spacing="1",
                        flex_wrap="wrap",
                        align="center",
                        padding_top="4px",
                    ),
                    rx.text(
                        "Results will update automatically when ready.",
                        size="1",
                        color="var(--gray-8)",
                    ),
                    spacing="2",
                    width="100%",
                ),
                padding="1rem",
                border="1px solid var(--blue-4)",
                border_radius="var(--radius-3)",
                background="var(--blue-1)",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Result card (completed only)
        rx.cond(
            task["status"] == "completed",
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("chart_bar", size=14, color="var(--green-9)"),
                        rx.text("Results", weight="bold", size="2"),
                        rx.spacer(),
                        rx.cond(
                            AppState.selected_task_completed_at != "",
                            rx.text(AppState.selected_task_completed_at, size="1", color="var(--gray-8)"),
                            rx.fragment(),
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                    ),
                    # Per-model result rows
                    rx.foreach(
                        AppState.selected_task_result_rows,
                        lambda row: rx.hstack(
                            rx.badge(row["model_name"], variant="soft", color_scheme="blue", size="1"),
                            rx.spacer(),
                            rx.vstack(
                                rx.hstack(
                                    rx.text("Accuracy", size="1", color="var(--gray-9)"),
                                    rx.text(row["accuracy"], size="2", weight="bold", color="var(--green-11)"),
                                    spacing="2", align="center",
                                ),
                                rx.hstack(
                                    rx.text("Samples", size="1", color="var(--gray-9)"),
                                    rx.text(row["samples"], size="1", color="var(--gray-11)"),
                                    rx.text("·", size="1", color="var(--gray-6)"),
                                    rx.text("Time", size="1", color="var(--gray-9)"),
                                    rx.text(row["exec_time"], size="1", color="var(--gray-11)"),
                                    spacing="1", align="center",
                                ),
                                spacing="1", align="end",
                            ),
                            padding="0.5rem 0",
                            border_bottom="1px solid var(--gray-3)",
                            width="100%",
                            align="center",
                        ),
                    ),
                    spacing="3",
                    align="start",
                    width="100%",
                ),
                padding="1rem",
                border="1px solid var(--green-4)",
                border_radius="var(--radius-3)",
                background="var(--green-1)",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Error card (failed only)
        rx.cond(
            task["status"] == "failed",
            rx.box(
                rx.hstack(
                    rx.icon("circle_x", size=14, color="var(--red-9)"),
                    rx.text(
                        rx.cond(
                            AppState.selected_task_error_msg != "",
                            AppState.selected_task_error_msg,
                            "Evaluation failed.",
                        ),
                        size="2",
                        color="var(--red-11)",
                    ),
                    spacing="2",
                    align="center",
                ),
                padding="1rem",
                border="1px solid var(--red-4)",
                border_radius="var(--radius-3)",
                background="var(--red-1)",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Auto-refresh JS for running/pending tasks
        rx.cond(
            (task["status"] == "running") | (task["status"] == "pending"),
            rx.script("""
            (function() {
                if (window._taskPoller) clearInterval(window._taskPoller);
                window._taskPoller = setInterval(function() {
                    var btn = document.getElementById('task-refresh-btn');
                    if (btn) btn.click();
                    else clearInterval(window._taskPoller);
                }, 8000);
            })();
            """),
            rx.script("if (window._taskPoller) { clearInterval(window._taskPoller); window._taskPoller = null; }"),
        ),
        # Action buttons
        rx.hstack(
            # Re-run button (always available)
            rx.button(
                rx.icon("rotate_ccw", size=14),
                "Re-run",
                on_click=AppState.rerun_task(task["id"]),
                variant="soft",
                color_scheme="blue",
                size="2",
                cursor="pointer",
            ),
            # Cancel button (only if cancellable)
            rx.cond(
                can_cancel,
                rx.button(
                    rx.icon("square", size=14),
                    "Cancel Evaluation",
                    on_click=AppState.cancel_selected_task,
                    variant="soft",
                    color_scheme="red",
                    size="2",
                    cursor="pointer",
                ),
                rx.fragment(),
            ),
            spacing="3",
            width="100%",
            padding_top="0.5rem",
        ),
        width="100%",
        spacing="4",
        align="start",
    )


# =========================================================================
# Page entry point
# =========================================================================

def evaluation_page() -> rx.Component:
    return rx.cond(
        AppState.is_authenticated,
        rx.cond(
            AppState.eval_step == "input",
            _eval_input_step(),
            rx.cond(
                AppState.eval_step == "configure",
                _eval_configure_step(),
                _task_detail_view(),
            ),
        ),
        login_required_card("Please log in to create a new evaluation."),
    )
