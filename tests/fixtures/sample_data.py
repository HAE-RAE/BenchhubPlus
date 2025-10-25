"""Sample data fixtures for testing."""

import json
from datetime import datetime, timedelta


# Sample evaluation plans
SAMPLE_PLANS = {
    "basic_math": {
        "version": "1.0",
        "metadata": {
            "name": "Basic Math Evaluation",
            "description": "Evaluation of basic mathematical problem solving",
            "language": "English",
            "subject_type": "Math",
            "task_type": "QA",
            "sample_size": 50
        },
        "models": [
            {
                "name": "gpt-4",
                "api_base": "https://api.openai.com/v1",
                "api_key": "sk-test-key",
                "model_type": "openai",
                "temperature": 0.7,
                "max_tokens": 1024
            }
        ],
        "datasets": [
            {
                "name": "basic_math_qa",
                "type": "qa",
                "source": "hret",
                "filters": {
                    "subject": "math",
                    "difficulty": "basic",
                    "language": "en"
                }
            }
        ],
        "evaluation": {
            "metrics": ["accuracy", "f1_score"],
            "timeout": 30,
            "batch_size": 10
        }
    },
    
    "korean_literature": {
        "version": "1.0",
        "metadata": {
            "name": "Korean Literature Evaluation",
            "description": "Evaluation of Korean literature comprehension",
            "language": "Korean",
            "subject_type": "Literature",
            "task_type": "QA",
            "sample_size": 30
        },
        "models": [
            {
                "name": "claude-3",
                "api_base": "https://api.anthropic.com",
                "api_key": "test-key",
                "model_type": "anthropic"
            }
        ],
        "datasets": [
            {
                "name": "korean_literature_qa",
                "type": "qa",
                "source": "local",
                "path": "korean_lit_samples.json"
            }
        ],
        "evaluation": {
            "metrics": ["accuracy", "semantic_similarity"],
            "timeout": 45,
            "batch_size": 5
        }
    }
}


# Sample evaluation samples
SAMPLE_EVALUATION_SAMPLES = {
    "math_samples": [
        {
            "id": 1,
            "question": "What is 15 + 27?",
            "answer": "42",
            "category": "arithmetic",
            "difficulty": "easy"
        },
        {
            "id": 2,
            "question": "Solve for x: 2x + 5 = 13",
            "answer": "4",
            "category": "algebra",
            "difficulty": "medium"
        },
        {
            "id": 3,
            "question": "What is the area of a circle with radius 5?",
            "answer": "25π or approximately 78.54",
            "category": "geometry",
            "difficulty": "medium"
        },
        {
            "id": 4,
            "question": "If f(x) = x² + 3x - 2, what is f(2)?",
            "answer": "8",
            "category": "functions",
            "difficulty": "medium"
        },
        {
            "id": 5,
            "question": "What is the derivative of x³?",
            "answer": "3x²",
            "category": "calculus",
            "difficulty": "hard"
        }
    ],
    
    "science_samples": [
        {
            "id": 1,
            "question": "What is the chemical formula for water?",
            "answer": "H2O",
            "category": "chemistry",
            "difficulty": "easy"
        },
        {
            "id": 2,
            "question": "What is Newton's second law of motion?",
            "answer": "F = ma (Force equals mass times acceleration)",
            "category": "physics",
            "difficulty": "medium"
        },
        {
            "id": 3,
            "question": "What organelle is responsible for photosynthesis in plants?",
            "answer": "Chloroplast",
            "category": "biology",
            "difficulty": "medium"
        }
    ],
    
    "korean_samples": [
        {
            "id": 1,
            "question": "한국의 수도는 어디인가요?",
            "answer": "서울",
            "category": "geography",
            "difficulty": "easy"
        },
        {
            "id": 2,
            "question": "조선왕조를 건국한 사람은 누구인가요?",
            "answer": "이성계 (태조)",
            "category": "history",
            "difficulty": "medium"
        },
        {
            "id": 3,
            "question": "'춘향전'의 주인공은 누구인가요?",
            "answer": "성춘향과 이몽룡",
            "category": "literature",
            "difficulty": "medium"
        }
    ]
}


# Sample model configurations
SAMPLE_MODEL_CONFIGS = {
    "openai_models": [
        {
            "name": "gpt-4",
            "api_base": "https://api.openai.com/v1",
            "api_key": "sk-test-key-1",
            "model_type": "openai",
            "temperature": 0.7,
            "max_tokens": 1024,
            "timeout": 30
        },
        {
            "name": "gpt-3.5-turbo",
            "api_base": "https://api.openai.com/v1",
            "api_key": "sk-test-key-2",
            "model_type": "openai",
            "temperature": 0.5,
            "max_tokens": 512,
            "timeout": 20
        }
    ],
    
    "anthropic_models": [
        {
            "name": "claude-3-opus",
            "api_base": "https://api.anthropic.com",
            "api_key": "test-anthropic-key-1",
            "model_type": "anthropic",
            "temperature": 0.8,
            "max_tokens": 2048,
            "timeout": 45
        },
        {
            "name": "claude-3-sonnet",
            "api_base": "https://api.anthropic.com",
            "api_key": "test-anthropic-key-2",
            "model_type": "anthropic",
            "temperature": 0.6,
            "max_tokens": 1024,
            "timeout": 30
        }
    ]
}


# Sample evaluation results
SAMPLE_EVALUATION_RESULTS = {
    "successful_result": {
        "model_results": [
            {
                "model_name": "gpt-4",
                "average_score": 0.92,
                "accuracy": 0.89,
                "total_samples": 50,
                "execution_time": 245.6,
                "detailed_metrics": {
                    "f1_score": 0.91,
                    "precision": 0.93,
                    "recall": 0.88,
                    "semantic_similarity": 0.87
                },
                "category_breakdown": {
                    "arithmetic": {"accuracy": 0.95, "count": 15},
                    "algebra": {"accuracy": 0.88, "count": 20},
                    "geometry": {"accuracy": 0.85, "count": 15}
                }
            },
            {
                "model_name": "claude-3",
                "average_score": 0.88,
                "accuracy": 0.85,
                "total_samples": 50,
                "execution_time": 198.3,
                "detailed_metrics": {
                    "f1_score": 0.87,
                    "precision": 0.89,
                    "recall": 0.84,
                    "semantic_similarity": 0.90
                },
                "category_breakdown": {
                    "arithmetic": {"accuracy": 0.90, "count": 15},
                    "algebra": {"accuracy": 0.82, "count": 20},
                    "geometry": {"accuracy": 0.83, "count": 15}
                }
            }
        ],
        "evaluation_metadata": {
            "total_duration": 450.2,
            "samples_processed": 50,
            "language": "English",
            "subject_type": "Math",
            "task_type": "QA",
            "evaluation_date": "2024-01-15T10:30:00Z",
            "statistical_significance": {
                "gpt-4_vs_claude-3": {
                    "p_value": 0.023,
                    "significant": True,
                    "confidence_level": 0.95
                }
            }
        }
    },
    
    "failed_result": {
        "error": "Model API call failed",
        "error_details": {
            "model": "gpt-4",
            "error_type": "AuthenticationError",
            "message": "Invalid API key",
            "timestamp": "2024-01-15T10:15:30Z"
        },
        "partial_results": {
            "samples_processed": 15,
            "samples_failed": 35
        }
    }
}


# Sample leaderboard entries
SAMPLE_LEADERBOARD_ENTRIES = [
    {
        "id": "entry-1",
        "model_name": "gpt-4",
        "score": 0.95,
        "accuracy": 0.92,
        "language": "English",
        "subject_type": "Math",
        "task_type": "QA",
        "sample_count": 100,
        "last_updated": "2024-01-15T10:30:00Z",
        "metadata": {
            "difficulty": "High School",
            "evaluation_time": 245.6,
            "f1_score": 0.91
        }
    },
    {
        "id": "entry-2",
        "model_name": "claude-3-opus",
        "score": 0.88,
        "accuracy": 0.85,
        "language": "English",
        "subject_type": "Math",
        "task_type": "QA",
        "sample_count": 100,
        "last_updated": "2024-01-15T09:45:00Z",
        "metadata": {
            "difficulty": "High School",
            "evaluation_time": 198.3,
            "f1_score": 0.87
        }
    },
    {
        "id": "entry-3",
        "model_name": "gpt-3.5-turbo",
        "score": 0.82,
        "accuracy": 0.78,
        "language": "English",
        "subject_type": "Math",
        "task_type": "QA",
        "sample_count": 100,
        "last_updated": "2024-01-15T09:15:00Z",
        "metadata": {
            "difficulty": "High School",
            "evaluation_time": 156.7,
            "f1_score": 0.80
        }
    },
    {
        "id": "entry-4",
        "model_name": "claude-3-sonnet",
        "score": 0.91,
        "accuracy": 0.88,
        "language": "Korean",
        "subject_type": "Literature",
        "task_type": "QA",
        "sample_count": 50,
        "last_updated": "2024-01-15T11:00:00Z",
        "metadata": {
            "difficulty": "University",
            "evaluation_time": 312.4,
            "semantic_similarity": 0.93
        }
    }
]


# Sample task data
SAMPLE_TASKS = [
    {
        "task_id": "task-1",
        "query": "Compare GPT-4 and Claude-3 on high school math problems",
        "status": "SUCCESS",
        "progress": 100,
        "created_at": datetime.utcnow() - timedelta(hours=2),
        "started_at": datetime.utcnow() - timedelta(hours=2, minutes=-5),
        "completed_at": datetime.utcnow() - timedelta(hours=1, minutes=30),
        "models_config": SAMPLE_MODEL_CONFIGS["openai_models"][:1] + SAMPLE_MODEL_CONFIGS["anthropic_models"][:1],
        "result": SAMPLE_EVALUATION_RESULTS["successful_result"]
    },
    {
        "task_id": "task-2",
        "query": "Evaluate Korean language understanding capabilities",
        "status": "PENDING",
        "progress": 0,
        "created_at": datetime.utcnow() - timedelta(minutes=30),
        "models_config": SAMPLE_MODEL_CONFIGS["anthropic_models"][:1]
    },
    {
        "task_id": "task-3",
        "query": "Test code generation abilities",
        "status": "STARTED",
        "progress": 65,
        "created_at": datetime.utcnow() - timedelta(minutes=45),
        "started_at": datetime.utcnow() - timedelta(minutes=40),
        "models_config": SAMPLE_MODEL_CONFIGS["openai_models"]
    },
    {
        "task_id": "task-4",
        "query": "Compare translation quality",
        "status": "FAILURE",
        "progress": 25,
        "created_at": datetime.utcnow() - timedelta(hours=1),
        "started_at": datetime.utcnow() - timedelta(minutes=55),
        "completed_at": datetime.utcnow() - timedelta(minutes=45),
        "error_message": "Model API authentication failed",
        "models_config": SAMPLE_MODEL_CONFIGS["openai_models"][:1]
    }
]


# Sample queries for testing planner
SAMPLE_QUERIES = [
    "Compare these models on Korean math problems for high school students",
    "Evaluate language understanding capabilities in English literature",
    "Test code generation abilities for Python programming tasks",
    "Compare logical reasoning performance on complex problems",
    "Evaluate translation quality between English and Korean",
    "Test scientific knowledge in chemistry and physics",
    "Compare creative writing abilities in storytelling",
    "Evaluate historical knowledge about world wars",
    "Test mathematical problem solving for university level calculus",
    "Compare reading comprehension in multiple languages"
]


# Helper functions to generate test data
def generate_sample_plan(query: str, models: list, language: str = "English", subject: str = "General"):
    """Generate a sample evaluation plan."""
    return {
        "version": "1.0",
        "metadata": {
            "name": f"Evaluation: {query[:50]}...",
            "description": f"Generated evaluation plan for: {query}",
            "language": language,
            "subject_type": subject,
            "task_type": "QA",
            "sample_size": 50
        },
        "models": models,
        "datasets": [
            {
                "name": f"{subject.lower()}_dataset",
                "type": "qa",
                "source": "hret",
                "filters": {
                    "language": language.lower(),
                    "subject": subject.lower()
                }
            }
        ],
        "evaluation": {
            "metrics": ["accuracy", "f1_score"],
            "timeout": 30,
            "batch_size": 10
        }
    }


def generate_mock_evaluation_result(models: list, samples_count: int = 50):
    """Generate mock evaluation results."""
    results = []
    
    for i, model in enumerate(models):
        # Generate realistic but varied scores
        base_score = 0.7 + (i * 0.05) + (hash(model["name"]) % 20) / 100
        base_accuracy = base_score * 0.9 + 0.05
        
        results.append({
            "model_name": model["name"],
            "average_score": round(base_score, 3),
            "accuracy": round(base_accuracy, 3),
            "total_samples": samples_count,
            "execution_time": 150 + (i * 30) + (hash(model["name"]) % 100),
            "detailed_metrics": {
                "f1_score": round(base_score * 0.95, 3),
                "precision": round(base_accuracy * 1.05, 3),
                "recall": round(base_accuracy * 0.95, 3)
            }
        })
    
    return {
        "model_results": results,
        "evaluation_metadata": {
            "total_duration": sum(r["execution_time"] for r in results),
            "samples_processed": samples_count,
            "evaluation_date": datetime.utcnow().isoformat()
        }
    }


# Export all sample data
__all__ = [
    "SAMPLE_PLANS",
    "SAMPLE_EVALUATION_SAMPLES", 
    "SAMPLE_MODEL_CONFIGS",
    "SAMPLE_EVALUATION_RESULTS",
    "SAMPLE_LEADERBOARD_ENTRIES",
    "SAMPLE_TASKS",
    "SAMPLE_QUERIES",
    "generate_sample_plan",
    "generate_mock_evaluation_result"
]