"""HRET runner for executing evaluations."""

import json
import logging
import os
import tempfile
import time
from typing import Any, Dict, List, Optional
import yaml
from datetime import datetime

# HRET imports
try:
    from llm_eval.evaluator import Evaluator
    from llm_eval.runner import PipelineRunner, PipelineConfig
    from llm_eval.utils.util import EvaluationResult
    from llm_eval.utils.logging import get_logger as get_hret_logger
    HRET_AVAILABLE = True
except ImportError as e:
    logging.warning(f"HRET not available: {e}")
    EvaluationResult = Any  # type: ignore
    HRET_AVAILABLE = False

logger = logging.getLogger(__name__)


class HRETRunner:
    """Runner for HRET evaluation toolkit."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize HRET runner."""
        if not HRET_AVAILABLE:
            raise RuntimeError("HRET is not available. Please install haerae-evaluation-toolkit.")
        
        self.config_path = config_path
        self.temp_dir = tempfile.mkdtemp(prefix="benchhub_plus_")
        self.hret_logger = get_hret_logger(name="benchhub_hret", level=logging.INFO)
        logger.info(f"HRET runner initialized with temp dir: {self.temp_dir}")
    
    def run_evaluation(
        self,
        plan_yaml: str,
        models: List[Dict[str, Any]],
        timeout: int = 1800  # 30 minutes
    ) -> Dict[str, Any]:
        """Run evaluation using HRET."""
        
        try:
            logger.info("Starting HRET evaluation...")
            
            # Parse plan YAML
            plan_data = yaml.safe_load(plan_yaml)
            
            # Convert BenchhubPlus plan to HRET configuration
            hret_configs = self._convert_plan_to_hret_configs(plan_data, models)
            
            # Run evaluations for each model
            results = self._run_hret_evaluations(hret_configs, timeout)
            
            logger.info("HRET evaluation completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"HRET evaluation failed: {e}")
            raise
        finally:
            # Cleanup temporary files
            self._cleanup()
    
    def _convert_plan_to_hret_configs(
        self, 
        plan_data: Dict[str, Any], 
        models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert BenchhubPlus plan to HRET configuration format."""
        
        hret_configs = []
        metadata = plan_data.get("metadata", {})
        datasets = plan_data.get("datasets", [])
        
        for model in models:
            # Determine model backend based on model type
            model_backend = self._get_hret_model_backend(model)
            
            # Create HRET configuration for each dataset
            for dataset_config in datasets:
                # Prepare dataset params - exclude split/subset as they're set explicitly
                original_params = dataset_config.get("params", {})
                dataset_params = {
                    k: v for k, v in original_params.items()
                    if k not in ['split', 'subset']
                }
                
                # Add sample_size and seed if present at dataset level
                if "sample_size" in dataset_config:
                    dataset_params["sample_size"] = dataset_config["sample_size"]
                if "seed" in dataset_config:
                    dataset_params["seed"] = dataset_config["seed"]
                
                # Add base_prompt_template for MCQA
                filters = dataset_config.get("filters", {})
                problem_type = filters.get("problem_type") or metadata.get("problem_type", "")
                if problem_type == "MCQA":
                    dataset_params["base_prompt_template"] = (
                        "{query}\n\n"
                        "Choices:\n"
                        "{options_str}\n\n"
                        "Answer with ONLY the option text (without the number prefix like '1.' or '2.'). "
                        "Do not include any additional text, explanation, or formatting:"
                    )
                
                config = {
                    "dataset": {
                        "name": dataset_config.get("name", "benchhub"),
                        "split": "train",  # BenchHub only has 'train' split
                        "params": dataset_params
                    },
                    "model": {
                        "name": model_backend,
                        "params": self._get_model_params(model)
                    },
                    "evaluation": {
                        "method": metadata.get("evaluation_method", "string_match"),
                        "params": {}
                    },
                    "language_penalize": metadata.get("language_penalize", True),
                    "target_lang": metadata.get("target_lang", "ko"),
                    "few_shot": {
                        "num": metadata.get("few_shot_num", 0)
                    },
                    "model_info": model,
                    "dataset_info": dataset_config
                }
                hret_configs.append(config)
        
        return hret_configs
    
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
                "model_name": model.get("model_name", model.get("name", "gpt-3.5-turbo")),
                "api_base": model.get("api_base"),
                "api_key": model.get("api_key"),
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
    
    def _run_hret_evaluations(
        self, 
        hret_configs: List[Dict[str, Any]], 
        timeout: int
    ) -> Dict[str, Any]:
        """Run HRET evaluations for all configurations."""
        
        results = {
            "metadata": {
                "execution_time": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "total_configs": len(hret_configs)
            },
            "model_results": []
        }
        
        start_time = time.time()
        
        for config in hret_configs:
            try:
                logger.info(f"Running evaluation for model: {config['model_info']['name']}")
                
                # Create HRET Evaluator
                evaluator = Evaluator()
                
                # Run evaluation
                evaluation_result = evaluator.run(
                    model=config["model"]["name"],
                    dataset=config["dataset"]["name"],
                    split=config["dataset"]["split"],
                    dataset_params=config["dataset"]["params"],
                    model_params=config["model"]["params"],
                    evaluation_method=config["evaluation"]["method"],
                    evaluator_params=config["evaluation"]["params"],
                    language_penalize=config["language_penalize"],
                    target_lang=config["target_lang"],
                    num_few_shot=config["few_shot"].get("num", 0)
                )
                
                # Convert HRET result to BenchhubPlus format
                model_result = self._convert_hret_result(
                    evaluation_result, 
                    config["model_info"], 
                    config["dataset_info"]
                )
                
                results["model_results"].append(model_result)
                
                # Generate sample-level results for database storage
                self._generate_sample_results_from_hret(
                    evaluation_result,
                    config["model_info"],
                    config["dataset_info"]
                )
                
            except Exception as e:
                logger.error(f"Failed to evaluate model {config['model_info']['name']}: {e}")
                # Add error result
                error_result = {
                    "model_name": config["model_info"]["name"],
                    "error": str(e),
                    "total_samples": 0,
                    "correct_samples": 0,
                    "accuracy": 0.0,
                    "average_score": 0.0,
                    "execution_time": 0.0,
                    "metadata": config["model_info"]
                }
                results["model_results"].append(error_result)
        
        results["metadata"]["execution_time"] = time.time() - start_time
        return results
    
    def _convert_hret_result(
        self, 
        hret_result: EvaluationResult, 
        model_info: Dict[str, Any],
        dataset_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert HRET EvaluationResult to BenchhubPlus format."""
        
        # Extract metrics from HRET result
        metrics = hret_result.metrics if hasattr(hret_result, 'metrics') else {}
        
        # Calculate total_samples and correct_samples from samples
        samples = getattr(hret_result, 'samples', []) if hasattr(hret_result, 'samples') else []
        total_samples = len(samples)
        correct_samples = sum(
            1 for s in samples 
            if isinstance(s, dict) and s.get('evaluation', {}).get('is_correct', False)
        )
        
        ### Debug: Print first 5 samples for inspection ###
        # logger.warning(f"\n{'='*80}")
        # logger.warning(f"Evaluation Results Summary")
        # logger.warning(f"{'='*80}")
        # logger.warning(f"Model: {model_info['name']}")
        # logger.warning(f"Total Samples: {total_samples}")
        # logger.warning(f"Correct Samples: {correct_samples}")
        # logger.warning(f"Accuracy: {correct_samples / total_samples * 100:.1f}%" if total_samples > 0 else "N/A")
        # logger.warning(f"\n{'='*80}")
        # logger.warning(f"{'='*80}\n")
        
        # for i, sample in enumerate(samples[:5]):
        #     if isinstance(sample, dict):
        #         logger.warning(f"\n🔍 Sample {i+1}:")
        #         logger.warning(f"Question: {sample.get('input', 'N/A')[:200]}...")
        #         logger.warning(f"Prediction: {sample.get('prediction', 'N/A')}")
        #         logger.warning(f"Reference: {sample.get('reference', 'N/A')}")
        #         logger.warning(f"Correct: {sample.get('evaluation', {}).get('is_correct', False)}")
        #         if 'options' in sample:
        #             logger.warning(f"Options: {sample.get('options', [])}")
        #         logger.warning("-" * 80)
        
        # logger.warning(f"\n{'='*80}\n")
        #######################################################

        return {
            "model_name": model_info["name"],
            "total_samples": total_samples,
            "correct_samples": correct_samples,
            "accuracy": metrics.get("accuracy", correct_samples / total_samples if total_samples > 0 else 0.0),
            "average_score": metrics.get("average_score", correct_samples / total_samples if total_samples > 0 else 0.0),
            "execution_time": metrics.get("execution_time", 0.0),
            "metadata": {
                "api_base": model_info.get("api_base"),
                "model_type": model_info.get("model_type"),
                "dataset_name": dataset_info.get("name"),
                "dataset_split": dataset_info.get("split"),
                "hret_metrics": metrics
            }
        }
    
    def _generate_sample_results_from_hret(
        self,
        hret_result: EvaluationResult,
        model_info: Dict[str, Any],
        dataset_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate sample-level results from HRET evaluation for database storage."""
        
        sample_results = []
        
        # Extract sample data from HRET result
        samples = getattr(hret_result, 'samples', []) if hasattr(hret_result, 'samples') else []
        
        for i, sample in enumerate(samples):
            sample_result = {
                "prompt": sample.get("input", f"Sample prompt {i+1}"),
                "answer": sample.get("prediction", f"Sample answer {i+1}"),
                "skill_label": dataset_info.get("task_type", "QA"),
                "target_label": dataset_info.get("language", "ko"),
                "subject_label": dataset_info.get("subject_type", "General"),
                "format_label": "text",
                "dataset_name": dataset_info.get("name", "hret_evaluation"),
                "meta_data": json.dumps({
                    "model_name": model_info["name"],
                    "sample_index": i,
                    "hret_evaluation": True,
                    "reference": sample.get("reference", ""),
                    "metadata": sample.get("metadata", {})
                }),
                "correctness": sample.get("score", 0.0)
            }
            sample_results.append(sample_result)
        
        # Store results in a temporary file for later processing
        results_file = os.path.join(self.temp_dir, f"{model_info['name']}_samples.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(sample_results, f, indent=2)
        
        return sample_results
    
    def _cleanup(self) -> None:
        """Clean up temporary files."""
        
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")
    
    def validate_plan(self, plan_yaml: str) -> bool:
        """Validate BenchhubPlus plan configuration for HRET compatibility."""
        
        try:
            plan_data = yaml.safe_load(plan_yaml)
            
            # Basic validation
            required_keys = ["version", "metadata", "datasets"]
            for key in required_keys:
                if key not in plan_data:
                    logger.error(f"Missing required key in plan: {key}")
                    return False
            
            # Validate metadata
            metadata = plan_data.get("metadata", {})
            if not isinstance(metadata, dict):
                logger.error("Metadata must be a dictionary")
                return False
            
            # Validate datasets
            datasets = plan_data.get("datasets", [])
            if not datasets:
                logger.error("No datasets specified in plan")
                return False
            
            for dataset in datasets:
                if not isinstance(dataset, dict):
                    logger.error("Each dataset must be a dictionary")
                    return False
                
                if "name" not in dataset:
                    logger.error("Dataset missing required 'name' field")
                    return False
                
                # Check if dataset is supported by HRET
                dataset_name = dataset["name"]
                supported_datasets = [
                    "benchhub", "haerae_bench", "kmmlu", "kudge", 
                    "click", "k2_eval", "hrm8k", "kormedqa", "kbl"
                ]
                
                if dataset_name not in supported_datasets:
                    logger.warning(f"Dataset '{dataset_name}' may not be supported by HRET")
            
            # Validate evaluation method if specified
            eval_method = metadata.get("evaluation_method", "string_match")
            supported_methods = [
                "string_match", "log_prob", "llm_judge", "partial_match", "math_eval"
            ]
            
            if eval_method not in supported_methods:
                logger.warning(f"Evaluation method '{eval_method}' may not be supported by HRET")
            
            logger.info("Plan validation successful")
            return True
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in plan: {e}")
            return False
        except Exception as e:
            logger.error(f"Plan validation error: {e}")
            return False


def create_hret_runner() -> HRETRunner:
    """Factory function to create HRET runner."""
    return HRETRunner()