#!/usr/bin/env python3
"""Test script for HRET integration with BenchhubPlus."""

import sys
import os
import yaml
import json
from pathlib import Path

# Add the apps directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

try:
    from worker.hret_runner import HRETRunner, HRET_AVAILABLE
    from worker.hret_config import HRETConfigManager
    print("✅ Successfully imported HRET integration modules")
except ImportError as e:
    print(f"❌ Failed to import HRET integration modules: {e}")
    sys.exit(1)


def test_hret_availability():
    """Test if HRET is available and importable."""
    print("\n🔍 Testing HRET availability...")
    
    if HRET_AVAILABLE:
        print("✅ HRET is available and importable")
        
        # Test basic HRET imports
        try:
            from llm_eval.evaluator import Evaluator
            from llm_eval.runner import PipelineRunner
            print("✅ HRET core modules imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import HRET core modules: {e}")
            return False
    else:
        print("❌ HRET is not available")
        return False
    
    return True


def test_config_manager():
    """Test HRET configuration manager."""
    print("\n🔧 Testing HRET configuration manager...")
    
    try:
        # Create config manager
        config_manager = HRETConfigManager()
        print("✅ Created HRET configuration manager")
        
        # Test supported datasets
        datasets = config_manager.get_supported_datasets()
        print(f"✅ Supported datasets: {datasets}")
        
        # Test supported models
        models = config_manager.get_supported_models()
        print(f"✅ Supported models: {models}")
        
        # Test supported evaluation methods
        eval_methods = config_manager.get_supported_evaluation_methods()
        print(f"✅ Supported evaluation methods: {eval_methods}")
        
        # Create example plan
        example_plan_path = config_manager.create_example_plan()
        print(f"✅ Created example plan: {example_plan_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration manager test failed: {e}")
        return False


def test_hret_runner():
    """Test HRET runner initialization."""
    print("\n🏃 Testing HRET runner...")
    
    try:
        # Create HRET runner
        runner = HRETRunner()
        print("✅ Created HRET runner")
        
        # Test plan validation
        example_plan = """
version: "1.0"
metadata:
  name: "Test Plan"
  evaluation_method: "string_match"
  target_lang: "ko"
datasets:
  - name: "benchhub"
    split: "test"
"""
        
        is_valid = runner.validate_plan(example_plan)
        if is_valid:
            print("✅ Plan validation successful")
        else:
            print("❌ Plan validation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ HRET runner test failed: {e}")
        return False


def test_plan_conversion():
    """Test conversion from BenchhubPlus plan to HRET config."""
    print("\n🔄 Testing plan conversion...")
    
    try:
        config_manager = HRETConfigManager()
        
        # Sample BenchhubPlus plan
        plan_data = {
            "version": "1.0",
            "metadata": {
                "name": "Test Evaluation",
                "evaluation_method": "string_match",
                "language_penalize": True,
                "target_lang": "ko",
                "few_shot_num": 0
            },
            "datasets": [
                {
                    "name": "benchhub",
                    "split": "test",
                    "params": {"language": "ko"}
                }
            ]
        }
        
        # Sample model info
        model_info = {
            "name": "test-model",
            "model_type": "litellm",
            "api_base": "https://api.openai.com/v1",
            "api_key": "test-key",
            "model_name": "gpt-3.5-turbo"
        }
        
        # Create HRET config
        config_path = config_manager.create_hret_config(plan_data, model_info)
        print(f"✅ Created HRET config: {config_path}")
        
        # Load and validate config
        config = config_manager.load_config(config_path)
        is_valid = config_manager.validate_config(config)
        
        if is_valid:
            print("✅ HRET config validation successful")
            print(f"📄 Config preview: {json.dumps(config, indent=2)}")
        else:
            print("❌ HRET config validation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Plan conversion test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting HRET integration tests...")
    
    tests = [
        ("HRET Availability", test_hret_availability),
        ("Configuration Manager", test_config_manager),
        ("HRET Runner", test_hret_runner),
        ("Plan Conversion", test_plan_conversion)
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
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! HRET integration is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())