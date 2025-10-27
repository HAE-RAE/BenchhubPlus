"""HRET configuration management for BenchhubPlus."""

import os
import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class HRETConfigManager:
    """Manages HRET configuration files and settings."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize HRET configuration manager."""
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent / "configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default HRET configuration
        self.default_config = {
            "default_dataset": "benchhub",
            "default_model": "litellm",
            "default_split": "test",
            "default_evaluation_method": "string_match",
            "mlflow_tracking": False,
            "wandb_tracking": False,
            "tensorboard_tracking": False,
            "log_level": "INFO",
            "output_dir": "./hret_results",
            "auto_save_results": True,
            "batch_size": None,
            "max_workers": None,
            "custom_loggers": []
        }
    
    def create_hret_config(
        self, 
        plan_data: Dict[str, Any], 
        model_info: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """Create HRET configuration file from BenchhubPlus plan."""
        
        metadata = plan_data.get("metadata", {})
        datasets = plan_data.get("datasets", [])
        
        # Use first dataset for configuration
        dataset_config = datasets[0] if datasets else {"name": "benchhub", "split": "test"}
        
        # Create HRET evaluator configuration
        hret_config = {
            "dataset": {
                "name": dataset_config.get("name", "benchhub"),
                "split": dataset_config.get("split", "test"),
                "params": dataset_config.get("params", {})
            },
            "model": {
                "name": self._get_hret_model_backend(model_info),
                "params": self._get_model_params(model_info)
            },
            "evaluation": {
                "method": metadata.get("evaluation_method", "string_match"),
                "params": {}
            },
            "language_penalize": metadata.get("language_penalize", True),
            "target_lang": metadata.get("target_lang", "ko"),
            "few_shot": {
                "num": metadata.get("few_shot_num", 0),
                "split": metadata.get("few_shot_split"),
                "instruction": metadata.get("few_shot_instruction", "Use the following examples to answer the question."),
                "example_template": metadata.get("few_shot_template", "Q: {input}\nA: {reference}")
            }
        }
        
        # Save configuration file
        if not output_path:
            output_path = self.config_dir / f"hret_config_{model_info['name']}.yaml"
        
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(hret_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Created HRET config: {output_path}")
        return str(output_path)
    
    def create_hret_global_config(
        self, 
        benchhub_settings: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None
    ) -> str:
        """Create global HRET configuration file."""
        
        config = self.default_config.copy()
        
        # Update with BenchhubPlus settings if provided
        if benchhub_settings:
            config.update(benchhub_settings)
        
        # Save global configuration
        if not output_path:
            output_path = self.config_dir / "hret_global_config.yaml"
        
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Created HRET global config: {output_path}")
        return str(output_path)
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load HRET configuration from file."""
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loaded HRET config from: {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load HRET config from {config_path}: {e}")
            raise
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate HRET configuration."""
        
        try:
            # Check required fields
            required_fields = ["dataset", "model", "evaluation"]
            for field in required_fields:
                if field not in config:
                    logger.error(f"Missing required field in HRET config: {field}")
                    return False
            
            # Validate dataset configuration
            dataset_config = config["dataset"]
            if not isinstance(dataset_config, dict) or "name" not in dataset_config:
                logger.error("Invalid dataset configuration")
                return False
            
            # Validate model configuration
            model_config = config["model"]
            if not isinstance(model_config, dict) or "name" not in model_config:
                logger.error("Invalid model configuration")
                return False
            
            # Validate evaluation configuration
            eval_config = config["evaluation"]
            if not isinstance(eval_config, dict) or "method" not in eval_config:
                logger.error("Invalid evaluation configuration")
                return False
            
            logger.info("HRET configuration validation successful")
            return True
            
        except Exception as e:
            logger.error(f"HRET configuration validation error: {e}")
            return False
    
    def _get_hret_model_backend(self, model: Dict[str, Any]) -> str:
        """Determine HRET model backend based on model configuration."""
        
        model_type = model.get("model_type", "").lower()
        api_base = model.get("api_base", "").lower()
        
        # Map model types to HRET backends
        if "openai" in model_type or "openai" in api_base:
            return "openai"
        elif "huggingface" in model_type or "hf" in model_type:
            return "huggingface"
        elif "litellm" in model_type:
            return "litellm"
        elif "vllm" in model_type:
            return "vllm"
        else:
            # Default to litellm for API-based models
            return "litellm"
    
    def _get_model_params(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Extract model parameters for HRET."""
        
        params = {}
        
        # Common parameters
        if "api_key" in model:
            params["api_key"] = model["api_key"]
        if "api_base" in model:
            params["api_base"] = model["api_base"]
        if "model_name" in model:
            params["model_name_or_path"] = model["model_name"]
        
        # Model-specific parameters
        model_type = model.get("model_type", "").lower()
        
        if "openai" in model_type:
            params.update({
                "model": model.get("model_name", "gpt-3.5-turbo"),
                "temperature": model.get("temperature", 0.0),
                "max_tokens": model.get("max_tokens", 1024)
            })
        elif "huggingface" in model_type:
            params.update({
                "model_name_or_path": model.get("model_name", "gpt2"),
                "device": model.get("device", "auto"),
                "torch_dtype": model.get("torch_dtype", "auto")
            })
        elif "litellm" in model_type:
            params.update({
                "model": model.get("model_name", "gpt-3.5-turbo"),
                "api_base": model.get("api_base"),
                "api_key": model.get("api_key"),
                "temperature": model.get("temperature", 0.0)
            })
        
        return params
    
    def get_supported_datasets(self) -> List[str]:
        """Get list of datasets supported by HRET."""
        
        return [
            "benchhub",
            "haerae_bench", 
            "kmmlu",
            "kudge",
            "click",
            "k2_eval",
            "hrm8k",
            "kormedqa",
            "kbl"
        ]
    
    def get_supported_models(self) -> List[str]:
        """Get list of model backends supported by HRET."""
        
        return [
            "openai",
            "huggingface",
            "litellm",
            "vllm"
        ]
    
    def get_supported_evaluation_methods(self) -> List[str]:
        """Get list of evaluation methods supported by HRET."""
        
        return [
            "string_match",
            "log_prob", 
            "llm_judge",
            "partial_match",
            "math_eval"
        ]
    
    def create_example_plan(self, output_path: Optional[str] = None) -> str:
        """Create an example BenchhubPlus plan file compatible with HRET."""
        
        example_plan = {
            "version": "1.0",
            "metadata": {
                "name": "HRET Integration Example",
                "description": "Example evaluation plan for HRET integration",
                "evaluation_method": "string_match",
                "language_penalize": True,
                "target_lang": "ko",
                "few_shot_num": 0,
                "sample_size": 100
            },
            "datasets": [
                {
                    "name": "benchhub",
                    "split": "test",
                    "params": {
                        "language": "ko",
                        "problem_types": ["multiple_choice"],
                        "task_types": ["qa"]
                    }
                }
            ]
        }
        
        if not output_path:
            output_path = self.config_dir / "example_plan.yaml"
        
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(example_plan, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Created example plan: {output_path}")
        return str(output_path)


def create_hret_config_manager(config_dir: Optional[str] = None) -> HRETConfigManager:
    """Factory function to create HRET configuration manager."""
    return HRETConfigManager(config_dir)