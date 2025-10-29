"""Data mapper for converting HRET results to BenchhubPlus format."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

# HRET imports
try:
    from llm_eval.utils.util import EvaluationResult
    HRET_AVAILABLE = True
except ImportError:
    HRET_AVAILABLE = False
    # Create mock class for type hints
    class EvaluationResult:
        pass

logger = logging.getLogger(__name__)


@dataclass
class BenchhubSample:
    """Data class for BenchhubPlus experiment sample."""
    prompt: str
    answer: str
    skill_label: str
    target_label: str
    subject_label: str
    format_label: str
    dataset_name: str
    meta_data: str  # JSON string
    correctness: float


@dataclass
class BenchhubModelResult:
    """Data class for BenchhubPlus model evaluation result."""
    model_name: str
    total_samples: int
    correct_samples: int
    accuracy: float
    average_score: float
    execution_time: float
    metadata: Dict[str, Any]


class HRETResultMapper:
    """Maps HRET evaluation results to BenchhubPlus database format."""
    
    def __init__(self):
        """Initialize HRET result mapper."""
        self.logger = logging.getLogger(__name__)
        
        # Default label mappings
        self.skill_label_mapping = {
            "qa": "QA",
            "reasoning": "Reasoning", 
            "math": "Math",
            "reading_comprehension": "Reading Comprehension",
            "knowledge": "Knowledge",
            "language_understanding": "Language Understanding",
            "generation": "Generation",
            "classification": "Classification",
            "multiple_choice": "Multiple Choice",
            "short_answer": "Short Answer",
            "long_answer": "Long Answer"
        }
        
        self.subject_label_mapping = {
            "general": "General",
            "science": "Science",
            "math": "Mathematics",
            "history": "History",
            "literature": "Literature",
            "law": "Law",
            "medicine": "Medicine",
            "economics": "Economics",
            "geography": "Geography",
            "korean": "Korean Language",
            "english": "English Language",
            "computer_science": "Computer Science",
            "philosophy": "Philosophy",
            "psychology": "Psychology",
            "sociology": "Sociology"
        }
        
        self.target_label_mapping = {
            "ko": "Korean",
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese",
            "multilingual": "Multilingual"
        }
    
    def map_hret_result_to_benchhub(
        self,
        hret_result: EvaluationResult,
        model_info: Dict[str, Any],
        dataset_info: Dict[str, Any],
        execution_time: float = 0.0
    ) -> Tuple[BenchhubModelResult, List[BenchhubSample]]:
        """
        Map HRET evaluation result to BenchhubPlus format.
        
        Returns:
            Tuple of (model_result, sample_results)
        """
        
        # Extract metrics from HRET result
        metrics = self._extract_metrics_from_hret_result(hret_result)
        
        # Create model result
        model_result = BenchhubModelResult(
            model_name=model_info["name"],
            total_samples=metrics["total_samples"],
            correct_samples=metrics["correct_samples"],
            accuracy=metrics["accuracy"],
            average_score=metrics["average_score"],
            execution_time=execution_time,
            metadata={
                "api_base": model_info.get("api_base"),
                "model_type": model_info.get("model_type"),
                "dataset_name": dataset_info.get("name"),
                "dataset_split": dataset_info.get("split"),
                "hret_metrics": metrics,
                "evaluation_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Create sample results
        sample_results = self._extract_samples_from_hret_result(
            hret_result, model_info, dataset_info
        )
        
        return model_result, sample_results
    
    def map_model_result(self, mock_result: Dict[str, Any]) -> Dict[str, Any]:
        """Map mock result to model result format (for testing)."""
        
        return {
            "model_name": mock_result["model_name"],
            "dataset_name": mock_result["dataset_name"],
            "total_samples": mock_result["total_samples"],
            "correct_samples": mock_result["correct_samples"],
            "accuracy": mock_result["accuracy"],
            "average_score": mock_result["accuracy"],  # Use accuracy as average score
            "execution_time": mock_result["execution_time"],
            "metadata": {
                "evaluation_type": "mock_test",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def map_sample_results(self, mock_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map mock result to sample results format (for testing)."""
        
        sample_results = []
        
        for i, sample in enumerate(mock_result.get("samples", [])):
            sample_result = {
                "prompt": sample["prompt"],
                "answer": sample["answer"],
                "skill_label": sample["skill"],
                "target_label": "Korean",  # Default for testing
                "subject_label": sample["subject"],
                "format_label": "text",
                "dataset_name": mock_result["dataset_name"],
                "meta_data": json.dumps({
                    "model_name": mock_result["model_name"],
                    "sample_index": i,
                    "target": sample.get("target", ""),
                    "evaluation_type": "mock_test"
                }),
                "correctness": 1.0 if sample["correct"] else 0.0
            }
            sample_results.append(sample_result)
        
        return sample_results
    

    
    def _extract_metrics_from_hret_result(self, hret_result: EvaluationResult) -> Dict[str, Any]:
        """Extract metrics from HRET evaluation result."""
        
        metrics = {
            "total_samples": 0,
            "correct_samples": 0,
            "accuracy": 0.0,
            "average_score": 0.0,
            "raw_metrics": {}
        }
        
        try:
            # Try to extract metrics from HRET result
            if hasattr(hret_result, 'metrics'):
                raw_metrics = hret_result.metrics
                metrics["raw_metrics"] = raw_metrics
                
                # Extract standard metrics
                metrics["total_samples"] = raw_metrics.get("total_samples", 0)
                metrics["correct_samples"] = raw_metrics.get("correct_samples", 0)
                metrics["accuracy"] = raw_metrics.get("accuracy", 0.0)
                metrics["average_score"] = raw_metrics.get("average_score", 0.0)
            
            # If metrics not available, try to compute from samples
            elif hasattr(hret_result, 'samples'):
                samples = hret_result.samples
                metrics["total_samples"] = len(samples)
                
                scores = []
                correct_count = 0
                
                for sample in samples:
                    score = sample.get("score", 0.0)
                    scores.append(score)
                    
                    # Consider score > 0.5 as correct
                    if score > 0.5:
                        correct_count += 1
                
                metrics["correct_samples"] = correct_count
                metrics["accuracy"] = correct_count / len(samples) if samples else 0.0
                metrics["average_score"] = sum(scores) / len(scores) if scores else 0.0
            
            # If no samples or metrics, use default values
            else:
                self.logger.warning("No metrics or samples found in HRET result")
                
        except Exception as e:
            self.logger.error(f"Failed to extract metrics from HRET result: {e}")
        
        return metrics
    
    def _extract_samples_from_hret_result(
        self,
        hret_result: EvaluationResult,
        model_info: Dict[str, Any],
        dataset_info: Dict[str, Any]
    ) -> List[BenchhubSample]:
        """Extract sample results from HRET evaluation result."""
        
        sample_results = []
        
        try:
            # Extract samples from HRET result
            samples = []
            if hasattr(hret_result, 'samples'):
                samples = hret_result.samples
            elif hasattr(hret_result, 'results'):
                samples = hret_result.results
            
            # Map each sample to BenchhubPlus format
            for i, sample in enumerate(samples):
                benchhub_sample = self._map_single_sample(
                    sample, model_info, dataset_info, i
                )
                sample_results.append(benchhub_sample)
                
        except Exception as e:
            self.logger.error(f"Failed to extract samples from HRET result: {e}")
        
        return sample_results
    
    def _map_single_sample(
        self,
        hret_sample: Dict[str, Any],
        model_info: Dict[str, Any],
        dataset_info: Dict[str, Any],
        sample_index: int
    ) -> BenchhubSample:
        """Map a single HRET sample to BenchhubPlus format."""
        
        # Extract basic fields
        prompt = hret_sample.get("input", hret_sample.get("prompt", f"Sample {sample_index + 1}"))
        answer = hret_sample.get("prediction", hret_sample.get("output", f"Answer {sample_index + 1}"))
        correctness = float(hret_sample.get("score", 0.0))
        
        # Map labels using dataset info and defaults
        skill_label = self._map_skill_label(dataset_info, hret_sample)
        target_label = self._map_target_label(dataset_info, hret_sample)
        subject_label = self._map_subject_label(dataset_info, hret_sample)
        format_label = self._map_format_label(dataset_info, hret_sample)
        
        # Create metadata
        meta_data = {
            "model_name": model_info["name"],
            "sample_index": sample_index,
            "hret_evaluation": True,
            "reference": hret_sample.get("reference", hret_sample.get("target", "")),
            "dataset_split": dataset_info.get("split", "test"),
            "original_sample": hret_sample
        }
        
        return BenchhubSample(
            prompt=prompt,
            answer=answer,
            skill_label=skill_label,
            target_label=target_label,
            subject_label=subject_label,
            format_label=format_label,
            dataset_name=dataset_info.get("name", "hret_evaluation"),
            meta_data=json.dumps(meta_data),
            correctness=correctness
        )
    
    def _map_skill_label(self, dataset_info: Dict[str, Any], sample: Dict[str, Any]) -> str:
        """Map skill label from dataset info and sample."""
        
        # Try to get from sample first
        if "skill" in sample:
            skill = sample["skill"].lower()
            return self.skill_label_mapping.get(skill, skill.title())
        
        # Try to get from dataset info
        task_type = dataset_info.get("task_type", "").lower()
        if task_type:
            return self.skill_label_mapping.get(task_type, task_type.title())
        
        # Try to infer from dataset name
        dataset_name = dataset_info.get("name", "").lower()
        if "math" in dataset_name:
            return "Math"
        elif "qa" in dataset_name or "question" in dataset_name:
            return "QA"
        elif "reasoning" in dataset_name:
            return "Reasoning"
        
        return "General"
    
    def _map_target_label(self, dataset_info: Dict[str, Any], sample: Dict[str, Any]) -> str:
        """Map target language label from dataset info and sample."""
        
        # Try to get from sample first
        if "language" in sample:
            lang = sample["language"].lower()
            return self.target_label_mapping.get(lang, lang.title())
        
        # Try to get from dataset info
        target_lang = dataset_info.get("target_lang", dataset_info.get("language", "")).lower()
        if target_lang:
            return self.target_label_mapping.get(target_lang, target_lang.title())
        
        # Default to Korean for Korean datasets
        dataset_name = dataset_info.get("name", "").lower()
        if any(korean_indicator in dataset_name for korean_indicator in ["korean", "ko", "haerae", "kmmlu"]):
            return "Korean"
        
        return "Unknown"
    
    def _map_subject_label(self, dataset_info: Dict[str, Any], sample: Dict[str, Any]) -> str:
        """Map subject label from dataset info and sample."""
        
        # Try to get from sample first
        if "subject" in sample:
            subject = sample["subject"].lower()
            return self.subject_label_mapping.get(subject, subject.title())
        
        # Try to get from dataset info
        subject_type = dataset_info.get("subject_type", "").lower()
        if subject_type:
            return self.subject_label_mapping.get(subject_type, subject_type.title())
        
        # Try to infer from dataset name
        dataset_name = dataset_info.get("name", "").lower()
        for subject_key, subject_label in self.subject_label_mapping.items():
            if subject_key in dataset_name:
                return subject_label
        
        return "General"
    
    def _map_format_label(self, dataset_info: Dict[str, Any], sample: Dict[str, Any]) -> str:
        """Map format label from dataset info and sample."""
        
        # Try to get from sample first
        if "format" in sample:
            return sample["format"].title()
        
        # Try to get from dataset info
        format_type = dataset_info.get("format_type", "").lower()
        if format_type:
            return format_type.title()
        
        # Try to infer from problem type
        problem_type = dataset_info.get("problem_type", "").lower()
        if "multiple_choice" in problem_type:
            return "Multiple Choice"
        elif "short_answer" in problem_type:
            return "Short Answer"
        elif "long_answer" in problem_type:
            return "Long Answer"
        
        return "Text"
    
    def create_leaderboard_entry(
        self,
        model_result: BenchhubModelResult,
        language: str = "Korean",
        subject_type: str = "General",
        task_type: str = "QA"
    ) -> Dict[str, Any]:
        """Create leaderboard cache entry from model result."""
        
        return {
            "model_name": model_result.model_name,
            "language": language,
            "subject_type": subject_type,
            "task_type": task_type,
            "score": model_result.accuracy,
            "last_updated": datetime.utcnow()
        }
    
    def batch_map_hret_results(
        self,
        hret_results: List[Tuple[EvaluationResult, Dict[str, Any], Dict[str, Any], float]]
    ) -> Tuple[List[BenchhubModelResult], List[BenchhubSample]]:
        """
        Batch map multiple HRET results to BenchhubPlus format.
        
        Args:
            hret_results: List of (hret_result, model_info, dataset_info, execution_time) tuples
            
        Returns:
            Tuple of (model_results, all_sample_results)
        """
        
        all_model_results = []
        all_sample_results = []
        
        for hret_result, model_info, dataset_info, execution_time in hret_results:
            try:
                model_result, sample_results = self.map_hret_result_to_benchhub(
                    hret_result, model_info, dataset_info, execution_time
                )
                
                all_model_results.append(model_result)
                all_sample_results.extend(sample_results)
                
            except Exception as e:
                self.logger.error(
                    f"Failed to map HRET result for model {model_info.get('name', 'unknown')}: {e}"
                )
        
        return all_model_results, all_sample_results


def create_hret_mapper() -> HRETResultMapper:
    """Factory function to create HRET result mapper."""
    return HRETResultMapper()