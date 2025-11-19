-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database if it doesn't exist (this runs automatically with POSTGRES_DB)
-- The database is already created by the Docker environment variable