"""Chart components for Streamlit frontend."""

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_leaderboard_chart(
    data: List[Dict[str, Any]],
    chart_type: str = "bar",
    title: str = "Model Performance"
) -> None:
    """Render leaderboard chart."""
    
    if not data:
        st.info("No data to display")
        return
    
    df = pd.DataFrame(data)
    
    if chart_type == "bar":
        fig = px.bar(
            df,
            x="model_name" if "model_name" in df.columns else "Model",
            y="score" if "score" in df.columns else "Score",
            title=title,
            color="score" if "score" in df.columns else "Score",
            color_continuous_scale="viridis"
        )
        fig.update_layout(showlegend=False)
        
    elif chart_type == "line":
        fig = px.line(
            df,
            x="model_name" if "model_name" in df.columns else "Model",
            y="score" if "score" in df.columns else "Score",
            title=title,
            markers=True
        )
        
    elif chart_type == "scatter":
        fig = px.scatter(
            df,
            x="model_name" if "model_name" in df.columns else "Model",
            y="score" if "score" in df.columns else "Score",
            title=title,
            size="score" if "score" in df.columns else "Score",
            color="score" if "score" in df.columns else "Score",
            color_continuous_scale="viridis"
        )
    
    else:
        st.error(f"Unsupported chart type: {chart_type}")
        return
    
    st.plotly_chart(fig, use_container_width=True)


def render_comparison_radar(
    models: List[str],
    metrics: Dict[str, List[float]],
    title: str = "Model Comparison"
) -> None:
    """Render radar chart for model comparison."""
    
    if not models or not metrics:
        st.info("No data to display")
        return
    
    fig = go.Figure()
    
    for i, model in enumerate(models):
        values = [metrics[metric][i] for metric in metrics.keys()]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=list(metrics.keys()),
            fill='toself',
            name=model
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=True,
        title=title
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_score_distribution(
    scores: List[float],
    title: str = "Score Distribution"
) -> None:
    """Render score distribution histogram."""
    
    if not scores:
        st.info("No data to display")
        return
    
    fig = px.histogram(
        x=scores,
        nbins=20,
        title=title,
        labels={"x": "Score", "y": "Frequency"}
    )
    
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_time_series(
    timestamps: List[str],
    values: List[float],
    title: str = "Performance Over Time",
    y_label: str = "Score"
) -> None:
    """Render time series chart."""
    
    if not timestamps or not values:
        st.info("No data to display")
        return
    
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(timestamps),
        "value": values
    })
    
    fig = px.line(
        df,
        x="timestamp",
        y="value",
        title=title,
        labels={"value": y_label, "timestamp": "Time"}
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_heatmap(
    data: pd.DataFrame,
    title: str = "Performance Heatmap"
) -> None:
    """Render heatmap for multi-dimensional data."""
    
    if data.empty:
        st.info("No data to display")
        return
    
    fig = px.imshow(
        data,
        title=title,
        color_continuous_scale="viridis",
        aspect="auto"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_metric_cards(metrics: Dict[str, Any]) -> None:
    """Render metric cards."""
    
    if not metrics:
        return
    
    cols = st.columns(len(metrics))
    
    for i, (key, value) in enumerate(metrics.items()):
        with cols[i]:
            if isinstance(value, (int, float)):
                if isinstance(value, float):
                    st.metric(key.replace("_", " ").title(), f"{value:.3f}")
                else:
                    st.metric(key.replace("_", " ").title(), value)
            else:
                st.metric(key.replace("_", " ").title(), str(value))


def render_progress_chart(
    task_data: List[Dict[str, Any]],
    title: str = "Task Progress"
) -> None:
    """Render task progress chart."""
    
    if not task_data:
        st.info("No task data to display")
        return
    
    df = pd.DataFrame(task_data)
    
    # Count tasks by status
    status_counts = df["status"].value_counts()
    
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title=title,
        color_discrete_map={
            "PENDING": "#ffa500",
            "STARTED": "#007bff", 
            "SUCCESS": "#28a745",
            "FAILURE": "#dc3545"
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)