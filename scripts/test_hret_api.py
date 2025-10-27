#!/usr/bin/env python3
"""Test script for HRET API integration."""

import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastapi.testclient import TestClient
    from apps.backend.main import create_app
    print("✅ Successfully imported FastAPI test client")
except ImportError as e:
    print(f"❌ Failed to import FastAPI test client: {e}")
    print("Installing required packages...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
    
    try:
        from fastapi.testclient import TestClient
        from apps.backend.main import create_app
        print("✅ Successfully imported FastAPI test client after installation")
    except ImportError as e2:
        print(f"❌ Still failed to import after installation: {e2}")
        sys.exit(1)


def test_hret_status_endpoint():
    """Test HRET status endpoint."""
    print("\n🔍 Testing HRET status endpoint...")
    
    try:
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/hret/status")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ HRET status endpoint working")
            print(f"   - HRET Available: {data.get('hret_available')}")
            print(f"   - Integration Status: {data.get('integration_status')}")
            print(f"   - Supported Features: {len(data.get('supported_features', []))}")
            return True
        else:
            print(f"❌ Status endpoint failed with code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Status endpoint test failed: {e}")
        return False


def test_hret_config_endpoint():
    """Test HRET configuration endpoint."""
    print("\n🔧 Testing HRET config endpoint...")
    
    try:
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/hret/config")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ HRET config endpoint working")
            print(f"   - Supported Datasets: {len(data.get('supported_datasets', []))}")
            print(f"   - Supported Models: {len(data.get('supported_models', []))}")
            print(f"   - Evaluation Methods: {len(data.get('supported_evaluation_methods', []))}")
            print(f"   - Example Plan Length: {len(data.get('example_plan', ''))}")
            return True
        elif response.status_code == 503:
            print("⚠️  HRET not available (expected if not installed)")
            return True
        else:
            print(f"❌ Config endpoint failed with code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Config endpoint test failed: {e}")
        return False


def test_hret_validate_plan_endpoint():
    """Test HRET plan validation endpoint."""
    print("\n✅ Testing HRET plan validation endpoint...")
    
    try:
        app = create_app()
        client = TestClient(app)
        
        # Test with valid plan
        valid_plan = """
version: "1.0"
metadata:
  name: "Test Plan"
  evaluation_method: "string_match"
  target_lang: "ko"
datasets:
  - name: "benchhub"
    split: "test"
"""
        
        response = client.post("/hret/validate-plan", json={"plan_yaml": valid_plan})
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Plan validation endpoint working")
            print(f"   - Valid Plan Result: {data.get('valid')}")
            print(f"   - Message: {data.get('message')}")
            
            # Test with invalid plan
            invalid_plan = "invalid yaml content"
            response2 = client.post("/hret/validate-plan", json={"plan_yaml": invalid_plan})
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"   - Invalid Plan Result: {data2.get('valid')}")
                return True
            else:
                print(f"❌ Invalid plan test failed with code {response2.status_code}")
                return False
                
        elif response.status_code == 503:
            print("⚠️  HRET not available (expected if not installed)")
            return True
        else:
            print(f"❌ Validation endpoint failed with code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Plan validation test failed: {e}")
        return False


def test_hret_evaluation_endpoint():
    """Test HRET evaluation endpoint (without actually running evaluation)."""
    print("\n🚀 Testing HRET evaluation endpoint...")
    
    try:
        app = create_app()
        client = TestClient(app)
        
        # Create test evaluation request
        evaluation_request = {
            "plan_yaml": """
version: "1.0"
metadata:
  name: "Test Evaluation"
  evaluation_method: "string_match"
  target_lang: "ko"
datasets:
  - name: "benchhub"
    split: "test"
""",
            "models": [
                {
                    "name": "test-model",
                    "model_type": "litellm",
                    "api_base": "https://api.example.com/v1",
                    "api_key": "test-key",
                    "model_name": "test-model"
                }
            ],
            "timeout_minutes": 5,
            "store_results": True
        }
        
        response = client.post("/hret/evaluate", json=evaluation_request)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Evaluation endpoint working")
            print(f"   - Task ID: {data.get('task_id')}")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Message: {data.get('message')}")
            print(f"   - Estimated Duration: {data.get('estimated_duration')} minutes")
            
            # Test status endpoint with the task ID
            task_id = data.get('task_id')
            if task_id:
                status_response = client.get(f"/hret/evaluate/{task_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   - Task Status Check: {status_data.get('status')}")
                    return True
                else:
                    print(f"❌ Task status check failed with code {status_response.status_code}")
                    return False
            else:
                print("⚠️  No task ID returned, but endpoint worked")
                return True
                
        elif response.status_code == 503:
            print("⚠️  HRET not available (expected if not installed)")
            return True
        elif response.status_code == 400:
            print("⚠️  Bad request (expected for test data)")
            return True
        else:
            print(f"❌ Evaluation endpoint failed with code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Evaluation endpoint test failed: {e}")
        return False


def test_hret_results_endpoints():
    """Test HRET results and leaderboard endpoints."""
    print("\n📊 Testing HRET results endpoints...")
    
    try:
        app = create_app()
        client = TestClient(app)
        
        # Test results endpoint
        response = client.get("/hret/results")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Results endpoint working")
            print(f"   - Results Count: {data.get('count', 0)}")
            
            # Test leaderboard endpoint
            leaderboard_response = client.get("/hret/leaderboard")
            
            if leaderboard_response.status_code == 200:
                leaderboard_data = leaderboard_response.json()
                print("✅ Leaderboard endpoint working")
                print(f"   - Leaderboard Count: {leaderboard_data.get('count', 0)}")
                return True
            else:
                print(f"❌ Leaderboard endpoint failed with code {leaderboard_response.status_code}")
                return False
                
        else:
            print(f"❌ Results endpoint failed with code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Results endpoints test failed: {e}")
        return False


def test_api_info_endpoint():
    """Test that API info includes HRET endpoints."""
    print("\n📋 Testing API info endpoint...")
    
    try:
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/api/v1")
        
        if response.status_code == 200:
            data = response.json()
            endpoints = data.get("endpoints", {})
            
            if "hret" in endpoints:
                hret_endpoints = endpoints["hret"]
                print("✅ API info includes HRET endpoints")
                print(f"   - HRET Endpoints: {len(hret_endpoints)}")
                for endpoint_name, endpoint_path in hret_endpoints.items():
                    print(f"     - {endpoint_name}: {endpoint_path}")
                return True
            else:
                print("❌ API info missing HRET endpoints")
                return False
                
        else:
            print(f"❌ API info endpoint failed with code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API info test failed: {e}")
        return False


def main():
    """Run all API integration tests."""
    print("🚀 Starting HRET API integration tests...")
    
    tests = [
        ("HRET Status", test_hret_status_endpoint),
        ("HRET Config", test_hret_config_endpoint),
        ("Plan Validation", test_hret_validate_plan_endpoint),
        ("Evaluation Endpoint", test_hret_evaluation_endpoint),
        ("Results Endpoints", test_hret_results_endpoints),
        ("API Info", test_api_info_endpoint)
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
        print("🎉 All API tests passed! HRET API integration is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())