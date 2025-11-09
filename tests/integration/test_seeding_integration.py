"""Integration tests for database seeding functionality."""

import os
import tempfile
import pytest
import pandas as pd
from unittest.mock import patch
from fastapi.testclient import TestClient

from apps.backend.main import app
from apps.backend.repositories.leaderboard_repo import LeaderboardRepository
from apps.core.db import get_db


class TestSeedingIntegration:
    """Integration test cases for database seeding functionality."""

    def test_app_startup_with_seeding(self, test_db, temp_dir):
        """Test that the app starts up correctly and performs seeding."""
        # Create test parquet file
        test_data = [
            {
                'model_name': 'IntegrationTest_GPT-4',
                'language': 'Korean',
                'subject_type': 'HASS/Economics',
                'task_type': 'Knowledge',
                'score': 0.85
            },
            {
                'model_name': 'IntegrationTest_Claude-3',
                'language': 'English',
                'subject_type': 'Tech./Coding',
                'task_type': 'Reasoning',
                'score': 0.88
            }
        ]
        df = pd.DataFrame(test_data)
        test_parquet_path = os.path.join(temp_dir, 'integration_seed.parquet')
        df.to_parquet(test_parquet_path, index=False)

        # Override the database dependency
        def override_get_db():
            try:
                yield test_db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        # Mock the seed file path and existence check
        with patch('apps.backend.seeding.SEED_FILE_PATH', test_parquet_path), \
             patch('apps.backend.seeding.os.path.exists', return_value=True), \
             patch('apps.backend.seeding.get_db_session') as mock_get_db:
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None

            # Create test client (this triggers app startup)
            with TestClient(app) as client:
                # Test that the app is running
                response = client.get("/")
                assert response.status_code == 200
                
                # Verify seeding occurred
                repo = LeaderboardRepository(test_db)
                seeded_data = repo.get_leaderboard()
                assert len(seeded_data) == 2
                
                model_names = [entry.model_name for entry in seeded_data]
                assert 'IntegrationTest_GPT-4' in model_names
                assert 'IntegrationTest_Claude-3' in model_names

        # Clean up
        app.dependency_overrides.clear()

    def test_leaderboard_api_with_seeded_data(self, test_db, temp_dir):
        """Test that the leaderboard API works correctly with seeded data."""
        # Create test parquet file
        test_data = [
            {
                'model_name': 'APITest_GPT-4',
                'language': 'Korean',
                'subject_type': 'HASS/Economics',
                'task_type': 'Knowledge',
                'score': 0.95
            },
            {
                'model_name': 'APITest_Claude-3',
                'language': 'Korean',
                'subject_type': 'HASS/Economics',
                'task_type': 'Knowledge',
                'score': 0.88
            },
            {
                'model_name': 'APITest_Gemini',
                'language': 'English',
                'subject_type': 'Tech./Coding',
                'task_type': 'Reasoning',
                'score': 0.92
            }
        ]
        df = pd.DataFrame(test_data)
        test_parquet_path = os.path.join(temp_dir, 'api_test_seed.parquet')
        df.to_parquet(test_parquet_path, index=False)

        # Override the database dependency
        def override_get_db():
            try:
                yield test_db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        # Mock the seed file path and existence check
        with patch('apps.backend.seeding.SEED_FILE_PATH', test_parquet_path), \
             patch('apps.backend.seeding.os.path.exists', return_value=True), \
             patch('apps.backend.seeding.get_db_session') as mock_get_db:
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None

            # Create test client
            with TestClient(app) as client:
                # Test leaderboard browse endpoint
                response = client.get("/api/v1/leaderboard/browse")
                assert response.status_code == 200
                
                data = response.json()
                assert "entries" in data
                assert len(data["entries"]) == 3
                
                # Verify data is sorted by score (descending)
                scores = [entry["score"] for entry in data["entries"]]
                assert scores == sorted(scores, reverse=True)
                
                # Test filtering by language
                response = client.get("/api/v1/leaderboard/browse?language=Korean")
                assert response.status_code == 200
                
                data = response.json()
                korean_entries = data["entries"]
                assert len(korean_entries) == 2
                for entry in korean_entries:
                    assert entry["language"] == "Korean"
                
                # Test filtering by subject_type
                response = client.get("/api/v1/leaderboard/browse?subject_type=Tech./Coding")
                assert response.status_code == 200
                
                data = response.json()
                tech_entries = data["entries"]
                assert len(tech_entries) == 1
                assert tech_entries[0]["subject_type"] == "Tech./Coding"

        # Clean up
        app.dependency_overrides.clear()

    def test_seeding_idempotency_across_restarts(self, test_db, temp_dir):
        """Test that seeding is idempotent across multiple app restarts."""
        # Create test parquet file
        test_data = [
            {
                'model_name': 'IdempotencyTest_Model',
                'language': 'Korean',
                'subject_type': 'HASS/Economics',
                'task_type': 'Knowledge',
                'score': 0.85
            }
        ]
        df = pd.DataFrame(test_data)
        test_parquet_path = os.path.join(temp_dir, 'idempotency_seed.parquet')
        df.to_parquet(test_parquet_path, index=False)

        # Override the database dependency
        def override_get_db():
            try:
                yield test_db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        # Mock the seed file path and existence check
        with patch('apps.backend.seeding.SEED_FILE_PATH', test_parquet_path), \
             patch('apps.backend.seeding.os.path.exists', return_value=True), \
             patch('apps.backend.seeding.get_db_session') as mock_get_db:
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None

            # First startup
            with TestClient(app) as client1:
                response = client1.get("/")
                assert response.status_code == 200
                
                repo = LeaderboardRepository(test_db)
                first_data = repo.get_leaderboard()
                assert len(first_data) == 1

            # Second startup (simulating restart)
            with TestClient(app) as client2:
                response = client2.get("/")
                assert response.status_code == 200
                
                repo = LeaderboardRepository(test_db)
                second_data = repo.get_leaderboard()
                # Should still have only 1 record (no duplicates)
                assert len(second_data) == 1
                assert second_data[0].model_name == 'IdempotencyTest_Model'

        # Clean up
        app.dependency_overrides.clear()

    def test_seeding_with_large_real_world_data(self, test_db, temp_dir):
        """Test seeding with a realistic large dataset."""
        # Create a realistic large dataset
        test_data = []
        models = [
            'Qwen_Qwen2.5-72B-Instruct',
            'Claude_Claude-3-Opus',
            'OpenAI_GPT-4-Turbo',
            'Google_Gemini-Pro',
            'Meta_Llama-2-70B',
            'Anthropic_Claude-3-Sonnet',
            'Microsoft_Phi-3-Medium',
            'Mistral_Mixtral-8x7B'
        ]
        
        languages = ['English', 'Korean']
        
        subjects = [
            'Art & Sports/Architecture',
            'Art & Sports/Fashion',
            'Art & Sports/Music',
            'HASS/Economics',
            'HASS/History',
            'HASS/Philosophy',
            'Tech./Coding',
            'Tech./Engineering',
            'Science/Physics',
            'Science/Chemistry'
        ]
        
        tasks = ['Knowledge', 'Reasoning']
        
        # Generate realistic scores
        import random
        random.seed(42)  # For reproducible tests
        
        for model in models:
            base_score = 0.6 + random.random() * 0.3  # Base score between 0.6-0.9
            for lang in languages:
                lang_modifier = 0.05 if lang == 'English' else -0.05
                for subject in subjects:
                    subject_modifier = random.uniform(-0.1, 0.1)
                    for task in tasks:
                        task_modifier = 0.02 if task == 'Knowledge' else -0.02
                        final_score = max(0.0, min(1.0, 
                            base_score + lang_modifier + subject_modifier + task_modifier + random.uniform(-0.05, 0.05)
                        ))
                        
                        test_data.append({
                            'model_name': model,
                            'language': lang,
                            'subject_type': subject,
                            'task_type': task,
                            'score': round(final_score, 6)
                        })
        
        df = pd.DataFrame(test_data)
        test_parquet_path = os.path.join(temp_dir, 'large_real_seed.parquet')
        df.to_parquet(test_parquet_path, index=False)

        # Override the database dependency
        def override_get_db():
            try:
                yield test_db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        # Mock the seed file path and existence check
        with patch('apps.backend.seeding.SEED_FILE_PATH', test_parquet_path), \
             patch('apps.backend.seeding.os.path.exists', return_value=True), \
             patch('apps.backend.seeding.get_db_session') as mock_get_db:
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None

            # Create test client
            with TestClient(app) as client:
                # Test that the app starts up successfully
                response = client.get("/")
                assert response.status_code == 200
                
                # Verify all data was seeded
                repo = LeaderboardRepository(test_db)
                seeded_data = repo.get_leaderboard(limit=1000)
                expected_count = len(models) * len(languages) * len(subjects) * len(tasks)
                assert len(seeded_data) == expected_count
                
                # Test API performance with large dataset
                response = client.get("/api/v1/leaderboard/browse?limit=50")
                assert response.status_code == 200
                
                data = response.json()
                assert len(data["entries"]) == 50
                
                # Test filtering performance
                response = client.get("/api/v1/leaderboard/browse?language=Korean&subject_type=HASS/Economics")
                assert response.status_code == 200
                
                data = response.json()
                filtered_entries = data["entries"]
                assert len(filtered_entries) == len(models) * len(tasks)  # All models, both tasks
                
                for entry in filtered_entries:
                    assert entry["language"] == "Korean"
                    assert entry["subject_type"] == "HASS/Economics"

        # Clean up
        app.dependency_overrides.clear()

    def test_seeding_error_handling_in_production_scenario(self, test_db, temp_dir):
        """Test error handling in production-like scenarios."""
        # Create a parquet file with some problematic data
        test_data = [
            {
                'model_name': 'ValidModel',
                'language': 'Korean',
                'subject_type': 'HASS/Economics',
                'task_type': 'Knowledge',
                'score': 0.85
            },
            # This record has a very long model name that might cause issues
            {
                'model_name': 'A' * 300,  # Very long name
                'language': 'Korean',
                'subject_type': 'HASS/Economics',
                'task_type': 'Knowledge',
                'score': 0.75
            }
        ]
        df = pd.DataFrame(test_data)
        test_parquet_path = os.path.join(temp_dir, 'problematic_seed.parquet')
        df.to_parquet(test_parquet_path, index=False)

        # Override the database dependency
        def override_get_db():
            try:
                yield test_db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        # Mock the seed file path and existence check
        with patch('apps.backend.seeding.SEED_FILE_PATH', test_parquet_path), \
             patch('apps.backend.seeding.os.path.exists', return_value=True), \
             patch('apps.backend.seeding.get_db_session') as mock_get_db:
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None

            # App should still start successfully even with problematic data
            with TestClient(app) as client:
                response = client.get("/")
                assert response.status_code == 200
                
                # At least the valid record should be inserted
                repo = LeaderboardRepository(test_db)
                seeded_data = repo.get_leaderboard()
                assert len(seeded_data) >= 1
                
                # Check that valid data is present
                model_names = [entry.model_name for entry in seeded_data]
                assert 'ValidModel' in model_names

        # Clean up
        app.dependency_overrides.clear()