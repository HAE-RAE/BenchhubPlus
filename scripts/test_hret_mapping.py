#!/usr/bin/env python3
"""Test script for HRET data mapping and storage."""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add the apps directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

try:
    from worker.hret_mapper import HRETResultMapper, BenchhubSample, BenchhubModelResult
    from worker.hret_storage import HRETStorageManager
    print("✅ Successfully imported HRET mapping modules")
except ImportError as e:
    print(f"❌ Failed to import HRET mapping modules: {e}")
    sys.exit(1)


class MockHRETResult:
    """Mock HRET evaluation result for testing."""
    
    def __init__(self):
        self.metrics = {
            "total_samples": 10,
            "correct_samples": 7,
            "accuracy": 0.7,
            "average_score": 0.75
        }
        
        self.samples = [
            {
                "input": "한국의 수도는 어디인가요?",
                "prediction": "서울",
                "reference": "서울",
                "score": 1.0,
                "metadata": {"question_type": "factual"}
            },
            {
                "input": "2 + 2는 얼마인가요?",
                "prediction": "4",
                "reference": "4",
                "score": 1.0,
                "metadata": {"question_type": "math"}
            },
            {
                "input": "파이썬에서 리스트를 정렬하는 방법은?",
                "prediction": "sort() 메서드를 사용합니다",
                "reference": "sort() 메서드나 sorted() 함수를 사용합니다",
                "score": 0.8,
                "metadata": {"question_type": "programming"}
            },
            {
                "input": "지구의 위성은 무엇인가요?",
                "prediction": "달",
                "reference": "달",
                "score": 1.0,
                "metadata": {"question_type": "science"}
            },
            {
                "input": "1945년에 끝난 전쟁은?",
                "prediction": "제2차 세계대전",
                "reference": "제2차 세계대전",
                "score": 1.0,
                "metadata": {"question_type": "history"}
            },
            {
                "input": "셰익스피어의 대표작은?",
                "prediction": "햄릿",
                "reference": "햄릿, 로미오와 줄리엣 등",
                "score": 0.7,
                "metadata": {"question_type": "literature"}
            },
            {
                "input": "물의 화학식은?",
                "prediction": "H2O",
                "reference": "H2O",
                "score": 1.0,
                "metadata": {"question_type": "chemistry"}
            },
            {
                "input": "한국의 전통 음식은?",
                "prediction": "김치",
                "reference": "김치, 불고기, 비빔밥 등",
                "score": 0.6,
                "metadata": {"question_type": "culture"}
            },
            {
                "input": "컴퓨터의 CPU는 무엇의 약자인가요?",
                "prediction": "Central Processing Unit",
                "reference": "Central Processing Unit",
                "score": 1.0,
                "metadata": {"question_type": "technology"}
            },
            {
                "input": "태양계에서 가장 큰 행성은?",
                "prediction": "목성",
                "reference": "목성",
                "score": 1.0,
                "metadata": {"question_type": "astronomy"}
            }
        ]


def test_hret_mapper():
    """Test HRET result mapper."""
    print("\n🔄 Testing HRET result mapper...")
    
    try:
        # Create mapper
        mapper = HRETResultMapper()
        print("✅ Created HRET result mapper")
        
        # Create mock data
        mock_result = MockHRETResult()
        model_info = {
            "name": "test-gpt-3.5",
            "model_type": "openai",
            "api_base": "https://api.openai.com/v1",
            "model_name": "gpt-3.5-turbo"
        }
        dataset_info = {
            "name": "benchhub",
            "split": "test",
            "task_type": "qa",
            "target_lang": "ko",
            "subject_type": "general"
        }
        execution_time = 45.2
        
        # Map result
        model_result, sample_results = mapper.map_hret_result_to_benchhub(
            mock_result, model_info, dataset_info, execution_time
        )
        
        print(f"✅ Mapped model result: {model_result.model_name}")
        print(f"   - Total samples: {model_result.total_samples}")
        print(f"   - Accuracy: {model_result.accuracy:.2f}")
        print(f"   - Execution time: {model_result.execution_time:.1f}s")
        
        print(f"✅ Mapped {len(sample_results)} sample results")
        
        # Show sample preview
        if sample_results:
            sample = sample_results[0]
            print(f"   - Sample preview:")
            print(f"     Prompt: {sample.prompt[:50]}...")
            print(f"     Answer: {sample.answer}")
            print(f"     Skill: {sample.skill_label}")
            print(f"     Target: {sample.target_label}")
            print(f"     Subject: {sample.subject_label}")
            print(f"     Correctness: {sample.correctness}")
        
        return True
        
    except Exception as e:
        print(f"❌ HRET mapper test failed: {e}")
        return False


def test_batch_mapping():
    """Test batch mapping of multiple results."""
    print("\n📦 Testing batch mapping...")
    
    try:
        mapper = HRETResultMapper()
        
        # Create multiple mock results
        hret_results = []
        for i in range(3):
            mock_result = MockHRETResult()
            model_info = {
                "name": f"test-model-{i+1}",
                "model_type": "litellm",
                "api_base": "https://api.example.com/v1",
                "model_name": f"model-{i+1}"
            }
            dataset_info = {
                "name": "kmmlu",
                "split": "test",
                "task_type": "multiple_choice",
                "target_lang": "ko",
                "subject_type": "science"
            }
            execution_time = 30.0 + i * 10
            
            hret_results.append((mock_result, model_info, dataset_info, execution_time))
        
        # Batch map results
        model_results, all_sample_results = mapper.batch_map_hret_results(hret_results)
        
        print(f"✅ Batch mapped {len(model_results)} model results")
        print(f"✅ Total sample results: {len(all_sample_results)}")
        
        for model_result in model_results:
            print(f"   - {model_result.model_name}: {model_result.accuracy:.2f} accuracy")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch mapping test failed: {e}")
        return False


def test_leaderboard_entry_creation():
    """Test leaderboard entry creation."""
    print("\n🏆 Testing leaderboard entry creation...")
    
    try:
        mapper = HRETResultMapper()
        
        # Create mock model result
        model_result = BenchhubModelResult(
            model_name="test-model",
            total_samples=100,
            correct_samples=85,
            accuracy=0.85,
            average_score=0.87,
            execution_time=120.5,
            metadata={
                "dataset_name": "benchhub",
                "target_lang": "ko",
                "evaluation_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Create leaderboard entry
        leaderboard_entry = mapper.create_leaderboard_entry(
            model_result,
            language="Korean",
            subject_type="General",
            task_type="QA"
        )
        
        print("✅ Created leaderboard entry:")
        print(f"   - Model: {leaderboard_entry['model_name']}")
        print(f"   - Language: {leaderboard_entry['language']}")
        print(f"   - Subject: {leaderboard_entry['subject_type']}")
        print(f"   - Task: {leaderboard_entry['task_type']}")
        print(f"   - Score: {leaderboard_entry['score']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Leaderboard entry test failed: {e}")
        return False


def test_storage_manager():
    """Test storage manager (without actual database operations)."""
    print("\n💾 Testing storage manager...")
    
    try:
        # Create storage manager
        storage_manager = HRETStorageManager()
        print("✅ Created HRET storage manager")
        
        # Test category determination methods
        dataset_name = "kmmlu_math"
        metadata = {"target_lang": "ko", "dataset_name": "kmmlu_math"}
        
        language = storage_manager._determine_language(dataset_name, metadata)
        subjects = storage_manager._determine_subject_types(dataset_name, metadata)
        tasks = storage_manager._determine_task_types(dataset_name, metadata)
        
        print(f"✅ Category determination:")
        print(f"   - Language: {language}")
        print(f"   - Subjects: {subjects}")
        print(f"   - Tasks: {tasks}")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage manager test failed: {e}")
        return False


def main():
    """Run all mapping tests."""
    print("🚀 Starting HRET mapping and storage tests...")
    
    tests = [
        ("HRET Mapper", test_hret_mapper),
        ("Batch Mapping", test_batch_mapping),
        ("Leaderboard Entry", test_leaderboard_entry_creation),
        ("Storage Manager", test_storage_manager)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All mapping tests passed! Data mapping is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())