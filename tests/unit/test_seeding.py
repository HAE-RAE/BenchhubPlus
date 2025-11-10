"""Tests for database seeding functionality."""

import os
import tempfile
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from apps.backend.seeding import seed_database, get_db_session, SEED_FILE_PATH
from apps.backend.repositories.leaderboard_repo import LeaderboardRepository
from apps.core.db import LeaderboardCache


class TestSeeding:
    """Test cases for database seeding functionality."""

    def test_seed_database_with_empty_db(self, test_db, temp_dir):
        """Test seeding when database is empty."""
        # Create test parquet file
        test_data = [
            {
                'model_name': 'TestModel_GPT-4',
                'language': 'Korean',
                'subject_type': 'HASS/Economics',
                'task_type': 'Knowledge',
                'score': 0.85
            },
            {
                'model_name': 'TestModel_Claude-3',
                'language': 'English',
                'subject_type': 'Tech./Coding',
                'task_type': 'Reasoning',
                'score': 0.88
            }
        ]
        df = pd.DataFrame(test_data)
        test_parquet_path = os.path.join(temp_dir, 'test_seed.parquet')
        df.to_parquet(test_parquet_path, index=False)

        # Mock the database session and file path
        with patch('apps.backend.seeding.get_db_session') as mock_get_db, \
             patch('apps.backend.seeding.SEED_FILE_PATH', test_parquet_path), \
             patch('apps.backend.seeding.os.path.exists', return_value=True):
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None
            
            # Ensure database is empty
            repo = LeaderboardRepository(test_db)
            existing_data = repo.get_leaderboard(limit=1)
            assert len(existing_data) == 0
            
            # Run seeding
            seed_database()
            
            # Verify data was inserted
            seeded_data = repo.get_leaderboard()
            assert len(seeded_data) == 2
            
            # Verify specific data
            model_names = [entry.model_name for entry in seeded_data]
            assert 'TestModel_GPT-4' in model_names
            assert 'TestModel_Claude-3' in model_names

    def test_seed_database_with_existing_data(self, test_db, temp_dir):
        """Test seeding when database already has data (idempotency)."""
        # Insert existing data
        repo = LeaderboardRepository(test_db)
        repo.upsert_entry(
            model_name='ExistingModel',
            language='Korean',
            subject_type='Test/Subject',
            task_type='Knowledge',
            score=0.75
        )
        
        # Create test parquet file
        test_data = [
            {
                'model_name': 'TestModel_GPT-4',
                'language': 'Korean',
                'subject_type': 'HASS/Economics',
                'task_type': 'Knowledge',
                'score': 0.85
            }
        ]
        df = pd.DataFrame(test_data)
        test_parquet_path = os.path.join(temp_dir, 'test_seed.parquet')
        df.to_parquet(test_parquet_path, index=False)

        # Mock the database session and file path
        with patch('apps.backend.seeding.get_db_session') as mock_get_db, \
             patch('apps.backend.seeding.SEED_FILE_PATH', test_parquet_path), \
             patch('apps.backend.seeding.os.path.exists', return_value=True):
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None
            
            # Verify existing data
            existing_data = repo.get_leaderboard()
            assert len(existing_data) == 1
            assert existing_data[0].model_name == 'ExistingModel'
            
            # Run seeding (should skip due to existing data)
            seed_database()
            
            # Verify no new data was added
            final_data = repo.get_leaderboard()
            assert len(final_data) == 1
            assert final_data[0].model_name == 'ExistingModel'

    def test_seed_database_file_not_found(self, test_db):
        """Test seeding when seed file doesn't exist."""
        with patch('apps.backend.seeding.get_db_session') as mock_get_db, \
             patch('apps.backend.seeding.SEED_FILE_PATH', 'nonexistent_file.parquet'), \
             patch('apps.backend.seeding.os.path.exists', return_value=False):
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None
            
            # Run seeding (should skip due to missing file)
            seed_database()
            
            # Verify no data was inserted
            repo = LeaderboardRepository(test_db)
            seeded_data = repo.get_leaderboard()
            assert len(seeded_data) == 0

    def test_seed_database_invalid_parquet_file(self, test_db, temp_dir):
        """Test seeding with invalid parquet file."""
        # Create invalid file
        invalid_file_path = os.path.join(temp_dir, 'invalid.parquet')
        with open(invalid_file_path, 'w') as f:
            f.write("This is not a parquet file")

        with patch('apps.backend.seeding.get_db_session') as mock_get_db, \
             patch('apps.backend.seeding.SEED_FILE_PATH', invalid_file_path), \
             patch('apps.backend.seeding.os.path.exists', return_value=True):
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None
            
            # Run seeding (should handle error gracefully)
            seed_database()
            
            # Verify no data was inserted
            repo = LeaderboardRepository(test_db)
            seeded_data = repo.get_leaderboard()
            assert len(seeded_data) == 0

    def test_seed_database_partial_failure(self, test_db, temp_dir):
        """Test seeding with some records failing to insert."""
        # Create test data with one invalid record
        test_data = [
            {
                'model_name': 'ValidModel',
                'language': 'Korean',
                'subject_type': 'HASS/Economics',
                'task_type': 'Knowledge',
                'score': 0.85
            },
            {
                'model_name': 'InvalidModel',
                'language': 'Korean',
                'subject_type': 'HASS/Economics',
                'task_type': 'Knowledge',
                'score': 'invalid_score'  # This should cause an error
            }
        ]
        df = pd.DataFrame(test_data)
        test_parquet_path = os.path.join(temp_dir, 'test_seed.parquet')
        df.to_parquet(test_parquet_path, index=False)

        with patch('apps.backend.seeding.get_db_session') as mock_get_db, \
             patch('apps.backend.seeding.SEED_FILE_PATH', test_parquet_path), \
             patch('apps.backend.seeding.os.path.exists', return_value=True):
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None
            
            # Run seeding
            seed_database()
            
            # Verify at least valid data was inserted
            repo = LeaderboardRepository(test_db)
            seeded_data = repo.get_leaderboard()
            # Should have at least 1 record (the valid one)
            assert len(seeded_data) >= 1
            model_names = [entry.model_name for entry in seeded_data]
            assert 'ValidModel' in model_names

    def test_get_db_session_context_manager(self):
        """Test the database session context manager."""
        with patch('apps.backend.seeding.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            
            with get_db_session() as session:
                assert session == mock_session
            
            # Verify session was closed
            mock_session.close.assert_called_once()

    def test_seed_database_with_real_schema(self, test_db, temp_dir):
        """Test seeding with data that matches the real LeaderboardCache schema."""
        # Create test data matching the exact schema
        test_data = [
            {
                'model_name': 'Qwen_Qwen2.5-72B-Instruct',
                'language': 'English',
                'subject_type': 'Art & Sports/Architecture',
                'task_type': 'Knowledge',
                'score': 0.571429
            },
            {
                'model_name': 'Qwen_Qwen2.5-72B-Instruct',
                'language': 'English',
                'subject_type': 'Art & Sports/Architecture',
                'task_type': 'Reasoning',
                'score': 1.000000
            },
            {
                'model_name': 'Claude_Claude-3-Opus',
                'language': 'Korean',
                'subject_type': 'HASS/Economics',
                'task_type': 'Knowledge',
                'score': 0.852000
            }
        ]
        df = pd.DataFrame(test_data)
        test_parquet_path = os.path.join(temp_dir, 'real_schema_seed.parquet')
        df.to_parquet(test_parquet_path, index=False)

        with patch('apps.backend.seeding.get_db_session') as mock_get_db, \
             patch('apps.backend.seeding.SEED_FILE_PATH', test_parquet_path), \
             patch('apps.backend.seeding.os.path.exists', return_value=True):
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None
            
            # Run seeding
            seed_database()
            
            # Verify all data was inserted correctly
            repo = LeaderboardRepository(test_db)
            seeded_data = repo.get_leaderboard()
            assert len(seeded_data) == 3
            
            # Verify specific entries
            qwen_entries = [entry for entry in seeded_data if 'Qwen' in entry.model_name]
            assert len(qwen_entries) == 2
            
            claude_entries = [entry for entry in seeded_data if 'Claude' in entry.model_name]
            assert len(claude_entries) == 1
            assert claude_entries[0].language == 'Korean'
            assert claude_entries[0].subject_type == 'HASS/Economics'
            assert claude_entries[0].score == 0.852000

    def test_seed_database_large_dataset(self, test_db, temp_dir):
        """Test seeding with a larger dataset to verify performance."""
        # Create a larger test dataset
        test_data = []
        models = ['GPT-4', 'Claude-3', 'Gemini-Pro', 'Llama-2']
        languages = ['English', 'Korean']
        subjects = ['HASS/Economics', 'Tech./Coding', 'Science/Physics', 'Art & Sports/Music']
        tasks = ['Knowledge', 'Reasoning']
        
        for model in models:
            for lang in languages:
                for subject in subjects:
                    for task in tasks:
                        test_data.append({
                            'model_name': f'TestModel_{model}',
                            'language': lang,
                            'subject_type': subject,
                            'task_type': task,
                            'score': 0.5 + (hash(f'{model}{lang}{subject}{task}') % 500) / 1000.0
                        })
        
        df = pd.DataFrame(test_data)
        test_parquet_path = os.path.join(temp_dir, 'large_seed.parquet')
        df.to_parquet(test_parquet_path, index=False)

        with patch('apps.backend.seeding.get_db_session') as mock_get_db, \
             patch('apps.backend.seeding.SEED_FILE_PATH', test_parquet_path), \
             patch('apps.backend.seeding.os.path.exists', return_value=True):
            
            mock_get_db.return_value.__enter__.return_value = test_db
            mock_get_db.return_value.__exit__.return_value = None
            
            # Run seeding
            seed_database()
            
            # Verify all data was inserted
            repo = LeaderboardRepository(test_db)
            seeded_data = repo.get_leaderboard(limit=1000)  # Increase limit for large dataset
            expected_count = len(models) * len(languages) * len(subjects) * len(tasks)
            assert len(seeded_data) == expected_count
            
            # Verify data integrity
            model_names = set(entry.model_name for entry in seeded_data)
            assert len(model_names) == len(models)
            
            languages_found = set(entry.language for entry in seeded_data)
            assert languages_found == set(languages)