"""Streamlit frontend for BenchHub Plus."""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_option_menu import option_menu

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="BenchHub Plus",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .status-pending { color: #ffa500; }
    .status-running { color: #007bff; }
    .status-success { color: #28a745; }
    .status-failure { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

# Session state initialization
if "task_history" not in st.session_state:
    st.session_state.task_history = []

if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None


def make_api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
    """Make API request with error handling."""
    
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, timeout=30)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def render_header():
    """Render main header."""
    st.markdown('<h1 class="main-header">🏆 BenchHub Plus</h1>', unsafe_allow_html=True)
    st.markdown("**Interactive Leaderboard System for Dynamic LLM Evaluation**")
    st.markdown("---")


def render_model_input_form() -> List[Dict[str, Any]]:
    """Render model input form and return model configurations."""
    
    st.subheader("🤖 Model Configuration")
    
    models = []
    
    # Number of models
    num_models = st.number_input(
        "Number of models to evaluate",
        min_value=1,
        max_value=10,
        value=2,
        help="Maximum 10 models per evaluation"
    )
    
    # Model configuration forms
    for i in range(num_models):
        with st.expander(f"Model {i+1} Configuration", expanded=i < 2):
            col1, col2 = st.columns(2)
            
            with col1:
                model_name = st.text_input(
                    f"Model Name",
                    value=f"model_{i+1}",
                    key=f"model_name_{i}",
                    help="Unique identifier for the model"
                )
                
                api_base = st.text_input(
                    f"API Base URL",
                    value="https://api.openai.com/v1",
                    key=f"api_base_{i}",
                    help="Base URL for the model API"
                )
            
            with col2:
                api_key = st.text_input(
                    f"API Key",
                    type="password",
                    key=f"api_key_{i}",
                    help="API key for authentication"
                )
                
                model_type = st.selectbox(
                    f"Model Type",
                    ["openai", "anthropic", "huggingface", "custom"],
                    key=f"model_type_{i}",
                    help="Type of model API"
                )
            
            if model_name and api_base and api_key:
                models.append({
                    "name": model_name,
                    "api_base": api_base,
                    "api_key": api_key,
                    "model_type": model_type
                })
    
    return models


def render_evaluation_form():
    """Render evaluation request form."""
    
    st.subheader("📝 Evaluation Request")
    
    # Query input
    query = st.text_area(
        "Natural Language Query",
        placeholder="Compare these models on Korean math problems for high school students",
        height=100,
        help="Describe what you want to evaluate in natural language"
    )
    
    # Model configuration
    models = render_model_input_form()
    
    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Start Evaluation", type="primary", use_container_width=True):
            if not query.strip():
                st.error("Please enter a query")
                return
            
            if not models:
                st.error("Please configure at least one model")
                return
            
            # Validate models
            for i, model in enumerate(models):
                if not all([model["name"], model["api_base"], model["api_key"]]):
                    st.error(f"Model {i+1} is missing required fields")
                    return
            
            # Submit evaluation request
            request_data = {
                "query": query,
                "models": models
            }
            
            with st.spinner("Submitting evaluation request..."):
                result = make_api_request("/api/v1/leaderboard/generate", "POST", request_data)
            
            if result:
                st.success(f"Evaluation started! Task ID: {result['task_id']}")
                st.session_state.current_task_id = result["task_id"]
                st.session_state.task_history.append({
                    "task_id": result["task_id"],
                    "query": query,
                    "models": [m["name"] for m in models],
                    "submitted_at": datetime.now(),
                    "status": result["status"]
                })
                
                # Auto-refresh to status page
                time.sleep(1)
                st.rerun()


def render_task_status():
    """Render task status monitoring."""
    
    st.subheader("📊 Task Status")
    
    # Current task status
    if st.session_state.current_task_id:
        with st.container():
            st.write(f"**Current Task:** `{st.session_state.current_task_id}`")
            
            col1, col2 = st.columns([3, 1])
            
            with col2:
                if st.button("🔄 Refresh Status"):
                    st.rerun()
            
            # Get task status
            task_status = make_api_request(f"/api/v1/tasks/{st.session_state.current_task_id}")
            
            if task_status:
                status = task_status["status"]
                
                # Status indicator
                status_colors = {
                    "PENDING": "🟡",
                    "STARTED": "🔵", 
                    "SUCCESS": "🟢",
                    "FAILURE": "🔴"
                }
                
                st.write(f"**Status:** {status_colors.get(status, '⚪')} {status}")
                
                # Progress information
                if status == "PENDING":
                    st.info("Task is queued for processing...")
                elif status == "STARTED":
                    st.info("Task is currently running...")
                    # Auto-refresh every 5 seconds for running tasks
                    time.sleep(5)
                    st.rerun()
                elif status == "SUCCESS":
                    st.success("Task completed successfully!")
                    
                    # Display results
                    if "result" in task_status:
                        render_evaluation_results(task_status["result"])
                elif status == "FAILURE":
                    st.error("Task failed!")
                    if "error_message" in task_status:
                        st.error(f"Error: {task_status['error_message']}")
                
                # Task details
                with st.expander("Task Details"):
                    st.json(task_status)
    
    # Task history
    if st.session_state.task_history:
        st.subheader("📋 Task History")
        
        history_df = pd.DataFrame([
            {
                "Task ID": task["task_id"][:8] + "...",
                "Query": task["query"][:50] + "..." if len(task["query"]) > 50 else task["query"],
                "Models": ", ".join(task["models"]),
                "Submitted": task["submitted_at"].strftime("%Y-%m-%d %H:%M"),
                "Status": task["status"]
            }
            for task in reversed(st.session_state.task_history[-10:])  # Last 10 tasks
        ])
        
        st.dataframe(history_df, use_container_width=True)


def render_evaluation_results(results: Dict[str, Any]):
    """Render evaluation results."""
    
    st.subheader("🏆 Evaluation Results")
    
    if "model_results" in results:
        model_results = results["model_results"]
        
        # Create results DataFrame
        df = pd.DataFrame([
            {
                "Model": result["model_name"],
                "Score": result["average_score"],
                "Accuracy": result.get("accuracy", 0),
                "Samples": result["total_samples"],
                "Execution Time": f"{result.get('execution_time', 0):.1f}s"
            }
            for result in model_results
        ])
        
        # Sort by score
        df = df.sort_values("Score", ascending=False).reset_index(drop=True)
        df.index += 1  # Start ranking from 1
        
        # Display results table
        st.dataframe(
            df.style.format({
                "Score": "{:.3f}",
                "Accuracy": "{:.1%}"
            }).background_gradient(subset=["Score"]),
            use_container_width=True
        )
        
        # Visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Bar chart
            fig_bar = px.bar(
                df,
                x="Model",
                y="Score",
                title="Model Performance Comparison",
                color="Score",
                color_continuous_scale="viridis"
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Radar chart for multiple metrics
            if len(df) > 1:
                fig_radar = go.Figure()
                
                for _, row in df.iterrows():
                    fig_radar.add_trace(go.Scatterpolar(
                        r=[row["Score"], row["Accuracy"], row["Samples"]/max(df["Samples"])],
                        theta=["Score", "Accuracy", "Relative Samples"],
                        fill='toself',
                        name=row["Model"]
                    ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 1]
                        )),
                    showlegend=True,
                    title="Multi-dimensional Comparison"
                )
                st.plotly_chart(fig_radar, use_container_width=True)
        
        # Detailed results
        with st.expander("Detailed Results"):
            st.json(results)


def render_leaderboard_browser():
    """Render leaderboard browser."""
    
    st.subheader("🏅 Browse Leaderboards")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        language_filter = st.selectbox(
            "Language",
            ["All", "English", "Korean", "Chinese", "Japanese"],
            help="Filter by language"
        )
    
    with col2:
        subject_filter = st.selectbox(
            "Subject",
            ["All", "Math", "Science", "History", "Literature", "General"],
            help="Filter by subject type"
        )
    
    with col3:
        task_filter = st.selectbox(
            "Task Type",
            ["All", "QA", "Classification", "Generation", "Reasoning"],
            help="Filter by task type"
        )
    
    with col4:
        limit = st.number_input(
            "Max Results",
            min_value=10,
            max_value=1000,
            value=100,
            help="Maximum number of results"
        )
    
    # Fetch leaderboard
    if st.button("🔍 Search Leaderboard"):
        params = {
            "limit": limit
        }
        
        if language_filter != "All":
            params["language"] = language_filter
        if subject_filter != "All":
            params["subject_type"] = subject_filter
        if task_filter != "All":
            params["task_type"] = task_filter
        
        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        
        with st.spinner("Fetching leaderboard..."):
            result = make_api_request(f"/api/v1/leaderboard/browse?{query_string}")
        
        if result and "entries" in result:
            entries = result["entries"]
            
            if entries:
                # Create DataFrame
                df = pd.DataFrame([
                    {
                        "Rank": i + 1,
                        "Model": entry["model_name"],
                        "Score": entry["score"],
                        "Language": entry["language"],
                        "Subject": entry["subject_type"],
                        "Task": entry["task_type"],
                        "Last Updated": entry["last_updated"][:10]  # Date only
                    }
                    for i, entry in enumerate(entries)
                ])
                
                # Display results
                st.write(f"**Found {len(entries)} entries**")
                
                st.dataframe(
                    df.style.format({
                        "Score": "{:.3f}"
                    }).background_gradient(subset=["Score"]),
                    use_container_width=True
                )
                
                # Top performers chart
                if len(df) > 0:
                    top_10 = df.head(10)
                    fig = px.bar(
                        top_10,
                        x="Score",
                        y="Model",
                        orientation="h",
                        title="Top 10 Models",
                        color="Score",
                        color_continuous_scale="viridis"
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No entries found matching the criteria")


def render_system_status():
    """Render system status and statistics."""
    
    st.subheader("⚙️ System Status")
    
    # Health check
    health = make_api_request("/api/v1/health")
    
    if health:
        status = health["status"]
        
        if status == "healthy":
            st.success("🟢 System is healthy")
        else:
            st.error("🔴 System has issues")
        
        # Status details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            db_status = health.get("database_status", "unknown")
            if db_status == "connected":
                st.success("Database: Connected")
            else:
                st.error("Database: Disconnected")
        
        with col2:
            redis_status = health.get("redis_status", "unknown")
            if redis_status == "connected":
                st.success("Redis: Connected")
            else:
                st.error("Redis: Disconnected")
        
        with col3:
            st.info("API: Available")
    
    # System statistics
    stats = make_api_request("/api/v1/stats")
    
    if stats:
        st.subheader("📈 System Statistics")
        
        # Task statistics
        if "tasks" in stats:
            task_stats = stats["tasks"]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Pending Tasks", task_stats.get("PENDING", 0))
            with col2:
                st.metric("Running Tasks", task_stats.get("STARTED", 0))
            with col3:
                st.metric("Completed Tasks", task_stats.get("SUCCESS", 0))
            with col4:
                st.metric("Failed Tasks", task_stats.get("FAILURE", 0))
        
        # Cache statistics
        if "cache_entries" in stats:
            st.metric("Cache Entries", stats["cache_entries"])
        
        # Planner status
        if "planner_available" in stats:
            if stats["planner_available"]:
                st.success("🤖 Planner Agent: Available")
            else:
                st.warning("🤖 Planner Agent: Unavailable")


def main():
    """Main application."""
    
    render_header()
    
    # Navigation menu
    selected = option_menu(
        menu_title=None,
        options=["Evaluate", "Status", "Browse", "System"],
        icons=["play-circle", "activity", "search", "gear"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "25px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#eee",
            },
            "nav-link-selected": {"background-color": "#667eea"},
        }
    )
    
    # Render selected page
    if selected == "Evaluate":
        render_evaluation_form()
    elif selected == "Status":
        render_task_status()
    elif selected == "Browse":
        render_leaderboard_browser()
    elif selected == "System":
        render_system_status()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**BenchHub Plus v2.0** | "
        "Built with Streamlit, FastAPI, and HRET | "
        f"API: {API_BASE_URL}"
    )


if __name__ == "__main__":
    main()