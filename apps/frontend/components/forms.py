"""Form components for Streamlit frontend."""

from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


def render_model_config_form(
    model_index: int,
    default_values: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Render model configuration form."""
    
    defaults = default_values or {}
    
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            model_name = st.text_input(
                "Model Name",
                value=defaults.get("name", f"model_{model_index + 1}"),
                key=f"model_name_{model_index}",
                help="Unique identifier for the model"
            )
            
            api_base = st.text_input(
                "API Base URL",
                value=defaults.get("api_base", "https://api.openai.com/v1"),
                key=f"api_base_{model_index}",
                help="Base URL for the model API"
            )
        
        with col2:
            api_key = st.text_input(
                "API Key",
                type="password",
                value=defaults.get("api_key", ""),
                key=f"api_key_{model_index}",
                help="API key for authentication"
            )
            
            model_type = st.selectbox(
                "Model Type",
                ["openai", "anthropic", "huggingface", "custom"],
                index=["openai", "anthropic", "huggingface", "custom"].index(
                    defaults.get("model_type", "openai")
                ),
                key=f"model_type_{model_index}",
                help="Type of model API"
            )
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=defaults.get("temperature", 0.7),
                step=0.1,
                key=f"temperature_{model_index}",
                help="Sampling temperature"
            )
            
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=1,
                max_value=4096,
                value=defaults.get("max_tokens", 1024),
                key=f"max_tokens_{model_index}",
                help="Maximum number of tokens to generate"
            )
            
            timeout = st.number_input(
                "Timeout (seconds)",
                min_value=1,
                max_value=300,
                value=defaults.get("timeout", 30),
                key=f"timeout_{model_index}",
                help="Request timeout in seconds"
            )
    
    # Validate and return model config
    if model_name and api_base and api_key:
        return {
            "name": model_name,
            "api_base": api_base,
            "api_key": api_key,
            "model_type": model_type,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": timeout
        }
    
    return None


def render_evaluation_criteria_form() -> Dict[str, Any]:
    """Render evaluation criteria form."""
    
    st.subheader("🎯 Evaluation Criteria")
    
    col1, col2 = st.columns(2)
    
    with col1:
        language = st.selectbox(
            "Language",
            ["Auto-detect", "English", "Korean", "Chinese", "Japanese", "Spanish", "French"],
            help="Target language for evaluation"
        )
        
        subject_type = st.selectbox(
            "Subject Type",
            ["Auto-detect", "Math", "Science", "History", "Literature", "General", "Programming"],
            help="Subject domain for evaluation"
        )
    
    with col2:
        task_type = st.selectbox(
            "Task Type",
            ["Auto-detect", "QA", "Classification", "Generation", "Reasoning", "Translation"],
            help="Type of task to evaluate"
        )
        
        difficulty = st.selectbox(
            "Difficulty Level",
            ["Auto-detect", "Elementary", "Middle School", "High School", "University", "Expert"],
            help="Difficulty level of questions"
        )
    
    # Sample size
    sample_size = st.slider(
        "Sample Size",
        min_value=10,
        max_value=1000,
        value=100,
        step=10,
        help="Number of samples to evaluate"
    )
    
    # Evaluation metrics
    st.subheader("📊 Evaluation Metrics")
    
    metrics = st.multiselect(
        "Select Metrics",
        ["Accuracy", "F1 Score", "BLEU", "ROUGE", "Perplexity", "Semantic Similarity"],
        default=["Accuracy"],
        help="Metrics to calculate during evaluation"
    )
    
    return {
        "language": language if language != "Auto-detect" else None,
        "subject_type": subject_type if subject_type != "Auto-detect" else None,
        "task_type": task_type if task_type != "Auto-detect" else None,
        "difficulty": difficulty if difficulty != "Auto-detect" else None,
        "sample_size": sample_size,
        "metrics": metrics
    }


def render_filter_form() -> Dict[str, Any]:
    """Render filter form for leaderboard browsing."""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        language_filter = st.selectbox(
            "Language",
            ["All", "English", "Korean", "Chinese", "Japanese", "Spanish", "French"],
            help="Filter by language"
        )
    
    with col2:
        subject_filter = st.selectbox(
            "Subject",
            ["All", "Math", "Science", "History", "Literature", "General", "Programming"],
            help="Filter by subject type"
        )
    
    with col3:
        task_filter = st.selectbox(
            "Task Type",
            ["All", "QA", "Classification", "Generation", "Reasoning", "Translation"],
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
    
    # Date range filter
    col1, col2 = st.columns(2)
    
    with col1:
        date_from = st.date_input(
            "From Date",
            help="Filter results from this date"
        )
    
    with col2:
        date_to = st.date_input(
            "To Date",
            help="Filter results to this date"
        )
    
    # Score range filter
    score_range = st.slider(
        "Score Range",
        min_value=0.0,
        max_value=1.0,
        value=(0.0, 1.0),
        step=0.01,
        help="Filter by score range"
    )
    
    return {
        "language": language_filter if language_filter != "All" else None,
        "subject_type": subject_filter if subject_filter != "All" else None,
        "task_type": task_filter if task_filter != "All" else None,
        "limit": limit,
        "date_from": date_from,
        "date_to": date_to,
        "score_min": score_range[0],
        "score_max": score_range[1]
    }


def render_query_builder() -> str:
    """Render query builder interface."""
    
    st.subheader("🔍 Query Builder")
    
    # Query templates
    templates = {
        "Custom": "",
        "Math Comparison": "Compare these models on math problems for high school students",
        "Language Understanding": "Evaluate language understanding capabilities in Korean",
        "Code Generation": "Test code generation abilities for Python programming",
        "Reasoning Tasks": "Compare logical reasoning performance on complex problems",
        "Translation Quality": "Evaluate translation quality between English and Korean"
    }
    
    template_choice = st.selectbox(
        "Choose Template",
        list(templates.keys()),
        help="Select a pre-built query template or choose Custom"
    )
    
    # Query input
    if template_choice == "Custom":
        query = st.text_area(
            "Natural Language Query",
            placeholder="Describe what you want to evaluate...",
            height=100,
            help="Describe your evaluation requirements in natural language"
        )
    else:
        query = st.text_area(
            "Natural Language Query",
            value=templates[template_choice],
            height=100,
            help="Edit the template or use as-is"
        )
    
    # Query enhancement options
    with st.expander("Query Enhancement"):
        include_context = st.checkbox(
            "Include Context",
            value=True,
            help="Include additional context in the evaluation"
        )
        
        randomize_order = st.checkbox(
            "Randomize Question Order",
            value=True,
            help="Randomize the order of questions"
        )
        
        use_few_shot = st.checkbox(
            "Use Few-shot Examples",
            value=False,
            help="Include few-shot examples in prompts"
        )
    
    # Add enhancement flags to query if needed
    enhancements = []
    if include_context:
        enhancements.append("with context")
    if randomize_order:
        enhancements.append("randomized order")
    if use_few_shot:
        enhancements.append("few-shot examples")
    
    if enhancements and query:
        query += f" ({', '.join(enhancements)})"
    
    return query


def render_batch_upload_form() -> Optional[List[Dict[str, Any]]]:
    """Render batch model upload form."""
    
    st.subheader("📁 Batch Model Upload")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Model Configuration",
        type=["json", "csv", "yaml"],
        help="Upload a file containing multiple model configurations"
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.json'):
                import json
                models = json.load(uploaded_file)
            elif uploaded_file.name.endswith('.csv'):
                import pandas as pd
                df = pd.read_csv(uploaded_file)
                models = df.to_dict('records')
            elif uploaded_file.name.endswith('.yaml'):
                import yaml
                models = yaml.safe_load(uploaded_file)
            else:
                st.error("Unsupported file format")
                return None
            
            # Validate models
            if isinstance(models, list):
                st.success(f"Loaded {len(models)} model configurations")
                
                # Preview
                with st.expander("Preview Models"):
                    for i, model in enumerate(models[:5]):  # Show first 5
                        st.write(f"**Model {i+1}:** {model.get('name', 'Unknown')}")
                        st.json(model)
                
                return models
            else:
                st.error("File must contain a list of model configurations")
                return None
                
        except Exception as e:
            st.error(f"Error parsing file: {e}")
            return None
    
    # Manual template
    st.subheader("📝 Template")
    
    template = {
        "models": [
            {
                "name": "model_1",
                "api_base": "https://api.openai.com/v1",
                "api_key": "your_api_key_here",
                "model_type": "openai"
            },
            {
                "name": "model_2", 
                "api_base": "https://api.anthropic.com",
                "api_key": "your_api_key_here",
                "model_type": "anthropic"
            }
        ]
    }
    
    st.code(json.dumps(template, indent=2), language="json")
    
    return None