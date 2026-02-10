-- Migration: Create new_servers table for server registration flow
-- This table holds servers that need to be registered/connected for the first time

-- Create the new_servers table
CREATE TABLE IF NOT EXISTS new_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Add index for faster lookups by server_id
CREATE INDEX IF NOT EXISTS idx_new_servers_server_id ON new_servers(server_id);

-- Add comment to explain the table purpose
COMMENT ON TABLE new_servers IS 'Holds servers pending initial connection/registration. Once a server connects with correct password, it moves to connected_servers.';

-- Ensure connected_servers has the necessary columns (if not already present)
-- This is idempotent - will not fail if columns already exist
DO $$
BEGIN
    -- Add name column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'connected_servers' AND column_name = 'name') THEN
        ALTER TABLE connected_servers ADD COLUMN name VARCHAR(255);
    END IF;

    -- Add metadata column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'connected_servers' AND column_name = 'metadata') THEN
        ALTER TABLE connected_servers ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

