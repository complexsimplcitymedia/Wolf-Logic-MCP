-- Local PostgreSQL Mirror Setup
-- Matches schema from 100.110.82.181:5433

-- Create wolf user
CREATE USER wolf WITH PASSWORD 'wolflogic2024';

-- Create database
CREATE DATABASE wolf_logic OWNER wolf;

-- Connect to wolf_logic
\c wolf_logic

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE wolf_logic TO wolf;

-- Create memories table
CREATE TABLE IF NOT EXISTS memories (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    memory_type VARCHAR(50),
    namespace VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_namespace ON memories(namespace);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_memory_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_metadata ON memories USING GIN(metadata);

-- Grant table permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO wolf;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO wolf;

-- Create wolf_users table (for compatibility)
CREATE TABLE IF NOT EXISTS wolf_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO wolf;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO wolf;

-- Summary
SELECT 'Local wolf_logic database initialized' AS status;
