-- Initialize BenchHub Plus Database
--
-- NOTE: The official postgres docker image creates the POSTGRES_USER /
-- POSTGRES_DB / POSTGRES_PASSWORD before running scripts in
-- /docker-entrypoint-initdb.d, so we do NOT (and must not) hardcode a
-- password here. This script only adds extensions and helpers on top of
-- the already-provisioned database/role.

\c benchhub_plus;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for performance
-- These will be created by SQLAlchemy migrations, but we can prepare them

-- Sample data (optional)
-- INSERT INTO leaderboard_cache (model_name, score, language, subject_type, task_type, last_updated)
-- VALUES 
--   ('gpt-3.5-turbo', 0.85, 'English', 'General', 'QA', NOW()),
--   ('gpt-4', 0.92, 'English', 'General', 'QA', NOW());

-- Create a function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- This will be used by SQLAlchemy models with triggers