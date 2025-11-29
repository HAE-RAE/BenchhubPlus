"""Streamlit frontend for BenchHub Plus."""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

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
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:12000")

# Session state initialization
if "task_history" not in st.session_state:
    st.session_state.task_history = []

if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None

if "user" not in st.session_state:
    st.session_state.user = None

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "requests_session" not in st.session_state:
    st.session_state.requests_session = requests.Session()

# Check for logout request
query_params = st.query_params
if "logout" in query_params:
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.requests_session = requests.Session()
    st.query_params.clear()
    st.rerun()

# Check for token in URL (from OAuth callback)
if "token" in query_params:
    token = query_params["token"]
    st.session_state.access_token = token
    st.query_params.clear()
    st.rerun()


def make_api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
    """Make API request with error handling and JWT token support."""
    
    try:
        url = f"{API_BASE_URL}{endpoint}"
        session = st.session_state.requests_session
        
        # Add JWT token to headers if available
        headers = {}
        if st.session_state.access_token:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        
        if method == "GET":
            response = session.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = session.post(url, json=data, headers=headers, timeout=30)
        elif method == "DELETE":
            response = session.delete(url, headers=headers, timeout=30)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
        
        if response.status_code in [200, 202]:
            return response.json()
        elif response.status_code == 401:
            st.session_state.user = None
            st.session_state.access_token = None
            return None
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def check_auth():
    """Check authentication status."""
    if not st.session_state.access_token:
        st.session_state.user = None
        return False
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        response = st.session_state.requests_session.get(
            f"{API_BASE_URL}/api/v1/auth/me",
            headers=headers,
            timeout=5
        )
        
        # Debug logging
        logger.info(f"Auth check - Status: {response.status_code}")
        logger.info(f"Auth check - URL: {API_BASE_URL}/api/v1/auth/me")
        
        if response.status_code == 200:
            st.session_state.user = response.json()
            logger.info(f"Auth check - User: {st.session_state.user}")
            return True
        else:
            # Token invalid or expired
            logger.error(f"Auth check failed - Status: {response.status_code}, Response: {response.text}")
            st.session_state.access_token = None
            st.session_state.user = None
            return False
    except Exception as e:
        logger.error(f"Auth check exception: {e}")
        st.session_state.user = None
        return False


def render_auth_section():
    """Render auth section in top-right corner."""
    is_auth = check_auth()
    browser_api_url = os.getenv("BROWSER_API_URL", "http://localhost:8001")
    login_url = f"{browser_api_url}/api/v1/auth/google/login"
    logout_url = f"{browser_api_url}/api/v1/auth/logout"
    
    if is_auth and st.session_state.user:
        user = st.session_state.user
        picture = user.get("picture", "")
        name = user.get("name", "User")
        email = user.get("email", "")
        
        st.markdown(
            f"""
            <div id="auth-container">
                <div class="auth-dropdown">
                    <input type="checkbox" id="auth-toggle" class="auth-toggle-checkbox">
                    <label for="auth-toggle" class="auth-profile-btn">
                        <img src="{picture}" class="auth-avatar" onerror="this.src='https://ui-avatars.com/api/?name={name}&background=667eea&color=fff'">
                        <span class="auth-name">{name}</span>
                        <svg class="dropdown-arrow" width="12" height="12" viewBox="0 0 12 12">
                            <path d="M6 9L1 4h10z" fill="#5f6368"/>
                        </svg>
                    </label>
                    <div class="auth-dropdown-content">
                        <div class="auth-user-info">
                            <img src="{picture}" style="width:60px;height:60px;border-radius:50%;margin-bottom:12px;" onerror="this.src='https://ui-avatars.com/api/?name={name}&background=667eea&color=fff'">
                            <strong style="font-size:18px;font-weight:600;color:#3c4043;margin-bottom:6px;display:block;">{name}</strong>
                            <span style="font-size:13px;color:#666;">{email}</span>
                        </div>
                        <form action="{logout_url}" method="POST" style="margin:0;padding:0;">
                            <button type="submit" class="auth-logout-btn">
                                Logout
                            </button>
                        </form>
                    </div>
                </div>
            </div>
            <style>
                #auth-container {{
                    position: fixed;
                    top: 60px;
                    right: 20px;
                    z-index: 999999;
                }}
                .auth-dropdown {{
                    position: relative;
                    display: inline-block;
                }}
                .auth-toggle-checkbox {{
                    display: none;
                }}
                .auth-profile-btn {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 6px 12px 6px 6px;
                    background: white;
                    border: 1px solid #dadce0;
                    border-radius: 24px;
                    cursor: pointer;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    transition: all 0.2s;
                    user-select: none;
                }}
                .auth-profile-btn:hover {{
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                    border-color: #667eea;
                }}
                .auth-avatar {{
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    flex-shrink: 0;
                }}
                .auth-name {{
                    font-size: 14px;
                    font-weight: 500;
                    color: #3c4043;
                    max-width: 120px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .dropdown-arrow {{
                    flex-shrink: 0;
                    transition: transform 0.2s;
                }}
                .auth-toggle-checkbox:checked ~ .auth-profile-btn .dropdown-arrow {{
                    transform: rotate(180deg);
                }}
                .auth-dropdown-content {{
                    display: none;
                    position: absolute;
                    right: 0;
                    top: 50px;
                    background-color: white;
                    min-width: 250px;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
                    border-radius: 8px;
                    padding: 20px;
                    z-index: 1000000;
                }}
                .auth-toggle-checkbox:checked ~ .auth-dropdown-content {{
                    display: block;
                }}
                .auth-user-info {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #eee;
                    margin-bottom: 15px;
                }}
                .auth-logout-btn {{
                    display: block;
                    width: 100%;
                    padding: 10px;
                    background: #dc3545;
                    color: white;
                    text-align: center;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    transition: background 0.2s;
                    cursor: pointer;
                }}
                .auth-logout-btn:hover {{
                    background: #c82333;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        # Not logged in state
        st.markdown(
            f"""
            <div id="auth-container">
                <a href="{login_url}" target="_self" style="text-decoration: none;">
                    <div class="auth-login-btn">
                        <svg class="google-icon" viewBox="0 0 24 24" width="20" height="20">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        <span class="login-text">Google Login</span>
                    </div>
                </a>
            </div>
            <style>
                #auth-container {{
                    position: fixed;
                    top: 60px;
                    right: 20px;
                    z-index: 999999;
                }}
                .auth-login-btn {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 10px 16px;
                    background: white;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    cursor: pointer;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    transition: all 0.2s;
                }}
                .auth-login-btn:hover {{
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                    border-color: #4285F4;
                }}
                .google-icon {{
                    flex-shrink: 0;
                }}
                .login-text {{
                    font-size: 14px;
                    font-weight: 500;
                    color: #3c4043;
                    white-space: nowrap;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )


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
    """Render leaderboard browser with chat-assisted filtering."""
    
    st.subheader("🏅 Browse Leaderboards")
    
    # Session state initialization for browse interactions
    if "browse_chat_history" not in st.session_state:
        st.session_state.browse_chat_history = [
            {
                "role": "assistant",
                "content": "안녕하세요! 관심 있는 주제를 말씀해 주시면 리더보드 필터를 추천해 드릴게요."
            }
        ]
    if "browse_initial_loaded" not in st.session_state:
        st.session_state.browse_initial_loaded = False
    if "browse_trigger_search" not in st.session_state:
        st.session_state.browse_trigger_search = False
    if "browse_last_result" not in st.session_state:
        st.session_state.browse_last_result = None
    if "browse_limit" not in st.session_state:
        st.session_state.browse_limit = 100
    if "browse_language_filter" not in st.session_state:
        st.session_state.browse_language_filter = "All"
    if "browse_subject_filter" not in st.session_state:
        st.session_state.browse_subject_filter = "All"
    if "browse_task_filter" not in st.session_state:
        st.session_state.browse_task_filter = "All"
    if "browse_categories" not in st.session_state:
        categories_data = make_api_request("/api/v1/leaderboard/categories")
        st.session_state.browse_categories = categories_data or {}
    
    categories = st.session_state.get("browse_categories", {}) or {}
    
    def render_results(result: Optional[Dict[str, Any]]) -> None:
        """Display leaderboard results stored in session state."""
        if not result:
            st.info("아직 리더보드 데이터를 불러오지 못했어요.")
            return
        
        entries = result.get("entries", [])
        if not entries:
            st.info("조건에 맞는 리더보드 항목이 없습니다.")
            return
        
        df = pd.DataFrame([
            {
                "Rank": i + 1,
                "Model": entry.get("model_name"),
                "Score": entry.get("score"),
                "Language": entry.get("language"),
                "Subject": entry.get("subject_type"),
                "Task": entry.get("task_type"),
                "Last Updated": (entry.get("last_updated") or "")[:10]
            }
            for i, entry in enumerate(entries)
        ])
        
        st.write(f"**총 {len(entries)}개 항목**")
        if result.get("query"):
            st.caption(f"현재 필터: {result['query']}")
        
        st.dataframe(
            df.style.format({
                "Score": "{:.3f}"
            }).background_gradient(subset=["Score"]),
            use_container_width=True
        )
        
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
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
    
    def perform_leaderboard_fetch() -> None:
        """Fetch leaderboard entries based on current filters."""
        params: Dict[str, Any] = {
            "limit": int(st.session_state.browse_limit)
        }
        
        if st.session_state.browse_language_filter != "All":
            params["language"] = st.session_state.browse_language_filter
        if st.session_state.browse_subject_filter != "All":
            params["subject_type"] = st.session_state.browse_subject_filter
        if st.session_state.browse_task_filter != "All":
            params["task_type"] = st.session_state.browse_task_filter
        
        query_string = urlencode(params)
        endpoint = "/api/v1/leaderboard/browse"
        if query_string:
            endpoint = f"{endpoint}?{query_string}"
        
        with st.spinner("Fetching leaderboard..."):
            result = make_api_request(endpoint)
        
        st.session_state.browse_last_result = result
        st.session_state.browse_initial_loaded = True
    
    # Chat assistant
    st.markdown("### 🗣️ Browse Assistant")
    for message in st.session_state.browse_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    user_query = st.chat_input("원하는 리더보드 주제를 입력해 주세요", key="browse_chat_input")
    if user_query:
        st.session_state.browse_chat_history.append({
            "role": "user",
            "content": user_query
        })
        
        with st.spinner("추천 필터를 준비하고 있어요..."):
            suggestion = make_api_request(
                "/api/v1/leaderboard/suggest",
                method="POST",
                data={"query": user_query}
            )
        
        if suggestion:
            display_lines = [suggestion.get("plan_summary", "추천 필터를 적용했어요.")]
            filter_lines = []
            
            if suggestion.get("language"):
                filter_lines.append(f"- 언어: **{suggestion['language']}**")
            if suggestion.get("subject_type"):
                filter_lines.append(f"- 주제: **{suggestion['subject_type']}**")
            if suggestion.get("task_type"):
                filter_lines.append(f"- 태스크: **{suggestion['task_type']}**")
            
            subject_candidates = suggestion.get("subject_type_options") or []
            if subject_candidates:
                candidate_text = ", ".join(subject_candidates)
                filter_lines.append(f"- 관련 주제 후보: {candidate_text}")
            
            if filter_lines:
                display_lines.append("\n".join(filter_lines))
            
            if not suggestion.get("used_planner", False):
                display_lines.append("_플래너 에이전트가 없어 기본 추천을 사용했어요._")
            
            assistant_message = "\n\n".join(display_lines)
            st.session_state.browse_chat_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            if suggestion.get("language"):
                st.session_state.browse_language_filter = suggestion["language"]
            if suggestion.get("subject_type"):
                st.session_state.browse_subject_filter = suggestion["subject_type"]
            if suggestion.get("task_type"):
                st.session_state.browse_task_filter = suggestion["task_type"]
            
            st.session_state.browse_trigger_search = True
        else:
            st.session_state.browse_chat_history.append({
                "role": "assistant",
                "content": "죄송해요, 추천 필터를 생성하지 못했어요. 다시 시도해 주세요."
            })
    
    # Filters
    language_options = ["All"] + sorted([
        lang for lang in categories.get("languages", []) if lang
    ])
    subject_options = ["All"] + sorted([
        subj for subj in categories.get("subject_types", []) if subj
    ])
    task_options = ["All"] + sorted([
        task for task in categories.get("task_types", []) if task
    ])
    
    current_language = st.session_state.browse_language_filter
    if current_language and current_language not in language_options:
        language_options.append(current_language)
    current_subject = st.session_state.browse_subject_filter
    if current_subject and current_subject not in subject_options:
        subject_options.append(current_subject)
    current_task = st.session_state.browse_task_filter
    if current_task and current_task not in task_options:
        task_options.append(current_task)
    
    language_options = list(dict.fromkeys(language_options))
    subject_options = list(dict.fromkeys(subject_options))
    task_options = list(dict.fromkeys(task_options))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.selectbox(
            "Language",
            language_options,
            help="Filter by language",
            key="browse_language_filter"
        )
    
    with col2:
        st.selectbox(
            "Subject",
            subject_options,
            help="Filter by subject type",
            key="browse_subject_filter"
        )
    
    with col3:
        st.selectbox(
            "Task Type",
            task_options,
            help="Filter by task type",
            key="browse_task_filter"
        )
    
    with col4:
        st.number_input(
            "Max Results",
            min_value=10,
            max_value=1000,
            value=st.session_state.browse_limit,
            step=10,
            help="Maximum number of results",
            key="browse_limit"
        )
    
    search_button_clicked = st.button("🔍 Search Leaderboard", use_container_width=True)
    
    if not st.session_state.browse_initial_loaded and not st.session_state.browse_trigger_search:
        st.session_state.browse_trigger_search = True
    
    if search_button_clicked or st.session_state.browse_trigger_search:
        st.session_state.browse_trigger_search = False
        perform_leaderboard_fetch()
    
    render_results(st.session_state.browse_last_result)


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
    render_auth_section()
    
    # Navigation menu
    nav_options = ["Evaluate", "Status", "Browse", "System"]
    if "main_nav" not in st.session_state:
        st.session_state.main_nav = nav_options[0]
    default_index = nav_options.index(st.session_state.main_nav) if st.session_state.main_nav in nav_options else 0
    selected = option_menu(
        menu_title=None,
        options=nav_options,
        icons=["play-circle", "activity", "search", "gear"],
        menu_icon="cast",
        default_index=default_index,
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
        },
        key="main_nav"
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
