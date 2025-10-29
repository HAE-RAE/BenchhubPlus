"""Planner Agent for converting natural language queries to evaluation plans."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

import yaml
from openai import OpenAI

from ..config import get_settings
from ..schemas import ModelInfo, PlanConfig

logger = logging.getLogger(__name__)
settings = get_settings()


class PlannerAgent:
    """LLM-based agent for converting natural language queries to evaluation plans."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize planner agent."""
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required for planner agent")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = settings.planner_model
        self.temperature = settings.planner_temperature
    
    def parse_query(self, query: str) -> PlanConfig:
        """Parse natural language query into structured plan configuration."""
        
        system_prompt = """You are an expert evaluation planner for language models using BenchHub dataset structure.
Your task is to convert natural language queries into structured evaluation plans following BenchHub configuration.

Given a user query, extract the following information:
1. problem_type: Problem format - one of ["Binary", "MCQA", "short-form", "open-ended"]
2. target_type: Target scope - one of ["General", "Local"] 
3. subject_type: Subject categories - list from BenchHub categories (can include both coarse and fine-grained)
4. task_type: Task type - one of ["Knowledge", "Reasoning", "Value", "Alignment"]
5. external_tool_usage: Whether external tools are needed - boolean
6. language: Target language (Korean, English, etc.)
7. sample_size: Number of samples to evaluate (default: 100, max: 1000)

BenchHub Categories:
- Science: Math/Algebra, Math/Geometry, Physics/Classical Mechanics, Chemistry/General, Biology/General, etc.
- Technology: Tech./Computer Science, Tech./Electrical Eng., Tech./AI/ML, etc.
- Humanities and Social Science (HASS): HASS/History, HASS/Philosophy, HASS/Literature, etc.
- Arts & Sports: Arts/Visual Arts, Arts/Music, Sports/General, etc.
- Culture: Culture/Korean Traditional, Culture/East Asian, Culture/Western, etc.
- Social Intelligence: Social/Communication, Social/Ethics, Social/Leadership, etc.

Return your response as a JSON object with these exact keys.

Examples:
Query: "한국어로 된 프로그래밍 문제를 잘 푸는 모델을 찾고 싶어"
Response: {"problem_type": "MCQA", "target_type": "General", "subject_type": ["Technology", "Tech./Computer Science"], "task_type": "Knowledge", "external_tool_usage": false, "language": "Korean", "sample_size": 100}

Query: "Which model is best at English math problems?"
Response: {"problem_type": "MCQA", "target_type": "General", "subject_type": ["Science", "Math/Algebra"], "task_type": "Reasoning", "external_tool_usage": false, "language": "English", "sample_size": 100}

Query: "I need to evaluate models on Korean traditional culture knowledge with 200 samples"
Response: {"problem_type": "MCQA", "target_type": "Local", "subject_type": ["Culture", "Culture/Korean Traditional"], "task_type": "Knowledge", "external_tool_usage": false, "language": "Korean", "sample_size": 200}
"""
        
        user_prompt = f"Query: {query}\nResponse:"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
            else:
                # Fallback parsing
                parsed_data = json.loads(content)
            
            # Validate and create PlanConfig
            plan_config = PlanConfig(**parsed_data)
            
            logger.info(f"Successfully parsed query: {query} -> {plan_config}")
            return plan_config
            
        except Exception as e:
            logger.error(f"Failed to parse query '{query}': {e}")
            # Return default configuration
            return PlanConfig(
                problem_type="MCQA",
                target_type="General", 
                subject_type=["Science"],
                task_type="Knowledge",
                external_tool_usage=False,
                language="Korean",
                sample_size=100
            )
    
    def generate_plan_yaml(
        self, 
        plan_config: PlanConfig, 
        models: List[ModelInfo]
    ) -> str:
        """Generate HRET-compatible plan.yaml from configuration and models."""
        
        # TODO: This is a placeholder implementation
        # In a real implementation, this would generate proper HRET configuration
        # based on BenchHub data structure and HRET requirements
        
        plan_data = {
            "version": "2.0",
            "metadata": {
                "name": f"BenchHub Plus Evaluation - {plan_config.task_type}",
                "description": f"Evaluation plan for {plan_config.language} {'/'.join(plan_config.subject_type)} {plan_config.task_type}",
                "created_by": "BenchHub Plus Planner Agent",
                "language": plan_config.language,
                "problem_type": plan_config.problem_type,
                "target_type": plan_config.target_type,
                "subject_type": plan_config.subject_type,
                "task_type": plan_config.task_type,
                "external_tool_usage": plan_config.external_tool_usage,
                "sample_size": plan_config.sample_size,
                "seed": plan_config.seed
            },
            "models": [],
            "datasets": [
                {
                    "name": "benchhub_filtered",
                    "type": "benchhub",
                    "filters": {
                        "problem_type": plan_config.problem_type,
                        "target_type": plan_config.target_type,
                        "subject_type": plan_config.subject_type,
                        "task_type": plan_config.task_type,
                        "external_tool_usage": plan_config.external_tool_usage,
                        "language": plan_config.language
                    },
                    "sample_size": plan_config.sample_size,
                    "seed": plan_config.seed
                }
            ],
            "evaluation": {
                "method": "string_match" if plan_config.problem_type == "MCQA" else "llm_judge",
                "judge_model": "gpt-4" if plan_config.problem_type != "MCQA" else None,
                "criteria": [
                    "correctness",
                    "completeness",
                    "clarity"
                ] if plan_config.problem_type != "MCQA" else ["correctness"]
            },
            "output": {
                "format": "json",
                "include_samples": True,
                "include_metadata": True
            }
        }
        
        # Add model configurations
        for model in models:
            model_config = {
                "name": model.name,
                "type": model.model_type,
                "api_base": model.api_base,
                "api_key": "${API_KEY}",  # Will be replaced at runtime
                "parameters": {
                    "temperature": 0.1,
                    "max_tokens": 1000,
                    "top_p": 1.0
                }
            }
            plan_data["models"].append(model_config)
        
        return yaml.dump(plan_data, default_flow_style=False, allow_unicode=True)
    
    def create_evaluation_plan(
        self, 
        query: str, 
        models: List[ModelInfo]
    ) -> Dict[str, Any]:
        """Create complete evaluation plan from query and models."""
        
        # Parse the natural language query
        plan_config = self.parse_query(query)
        
        # Generate YAML configuration
        plan_yaml = self.generate_plan_yaml(plan_config, models)
        
        # Create plan metadata
        plan_metadata = {
            "query": query,
            "config": plan_config.dict(),
            "models": [model.dict() for model in models],
            "plan_yaml": plan_yaml,
            "estimated_duration": self._estimate_duration(plan_config, len(models)),
            "estimated_cost": self._estimate_cost(plan_config, models)
        }
        
        return plan_metadata
    
    def _estimate_duration(self, config: PlanConfig, num_models: int) -> int:
        """Estimate evaluation duration in seconds."""
        # Simple estimation: 1 second per sample per model
        base_time = config.sample_size * num_models
        
        # Add overhead for setup and aggregation
        overhead = 30 + (num_models * 10)
        
        return base_time + overhead
    
    def _estimate_cost(self, config: PlanConfig, models: List[ModelInfo]) -> float:
        """Estimate evaluation cost in USD."""
        # Simple estimation based on typical API costs
        # This would need to be more sophisticated in production
        
        cost_per_sample = {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002,
            "claude": 0.01,
            "default": 0.005
        }
        
        total_cost = 0.0
        for model in models:
            model_cost = cost_per_sample.get(
                model.name.lower(), 
                cost_per_sample["default"]
            )
            total_cost += model_cost * config.sample_size
        
        return round(total_cost, 2)
    
    def validate_plan(self, plan_yaml: str) -> bool:
        """Validate generated plan YAML."""
        try:
            plan_data = yaml.safe_load(plan_yaml)
            
            # Basic validation
            required_keys = ["version", "metadata", "models", "datasets"]
            for key in required_keys:
                if key not in plan_data:
                    logger.error(f"Missing required key in plan: {key}")
                    return False
            
            # Validate models
            if not plan_data["models"]:
                logger.error("No models specified in plan")
                return False
            
            # Validate datasets
            if not plan_data["datasets"]:
                logger.error("No datasets specified in plan")
                return False
            
            logger.info("Plan validation successful")
            return True
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in plan: {e}")
            return False
        except Exception as e:
            logger.error(f"Plan validation error: {e}")
            return False


def create_planner_agent() -> PlannerAgent:
    """Factory function to create planner agent."""
    return PlannerAgent()


# Example usage and testing
if __name__ == "__main__":
    # This would be used for testing the planner agent
    import os
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Example usage (requires OpenAI API key)
    if os.getenv("OPENAI_API_KEY"):
        planner = PlannerAgent()
        
        # Test query parsing
        test_queries = [
            "한국어로 된 프로그래밍 문제를 잘 푸는 모델을 찾고 싶어",
            "Which model is best at English math problems?",
            "I need to evaluate models on Korean traditional culture knowledge",
            "전기공학 관련 객관식 문제로 모델을 평가하고 싶어요",
            "Find the best model for reasoning tasks in social intelligence"
        ]
        
        for query in test_queries:
            try:
                config = planner.parse_query(query)
                print(f"Query: {query}")
                print(f"Config: {config}")
                print("-" * 50)
            except Exception as e:
                print(f"Error parsing query '{query}': {e}")
    else:
        print("OPENAI_API_KEY not set, skipping tests")