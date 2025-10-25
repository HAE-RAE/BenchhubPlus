-- Initialize BenchHub Plus Database

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS benchhub_plus;

-- Create user if not exists
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'benchhub') THEN

      CREATE ROLE benchhub LOGIN PASSWORD 'benchhub_password';
   END IF;
END
$do$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE benchhub_plus TO benchhub;

-- Connect to the database
\c benchhub_plus;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO benchhub;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO benchhub;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO benchhub;

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