-- Migration: Add owner field to connected_servers and create unclaimed_servers table
-- Date: 2026-01-13

-- Add owner column to connected_servers table
ALTER TABLE connected_servers
ADD COLUMN IF NOT EXISTS owner uuid REFERENCES auth.users(id) ON DELETE SET NULL;

-- Create index for faster owner lookups
CREATE INDEX IF NOT EXISTS idx_connected_servers_owner ON connected_servers(owner);

-- Create unclaimed_servers table
-- This table stores servers that are available to be claimed by users
CREATE TABLE IF NOT EXISTS unclaimed_servers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id uuid NOT NULL REFERENCES connected_servers(id) ON DELETE CASCADE,
    password text NOT NULL,
    created_at timestamptz DEFAULT now(),
    UNIQUE(server_id)
);

-- Create index for faster server_id lookups
CREATE INDEX IF NOT EXISTS idx_unclaimed_servers_server_id ON unclaimed_servers(server_id);

-- Add comment for documentation

