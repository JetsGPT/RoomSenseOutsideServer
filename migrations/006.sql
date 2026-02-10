-- Migration: Notification System for relay gateway
-- Date: 2026-02-10

-- Add identity_token column to connected_servers table
-- Used for authenticating Local Servers when they relay notifications
ALTER TABLE connected_servers
ADD COLUMN IF NOT EXISTS identity_token TEXT;

-- Create index for faster identity token lookups
CREATE INDEX IF NOT EXISTS idx_connected_servers_identity_token ON connected_servers(identity_token);

-- Global notification configuration table
-- Stores global settings like default NTFY URL, DND schedules, etc.
CREATE TABLE IF NOT EXISTS global_notification_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key TEXT UNIQUE NOT NULL,
    config_value JSONB NOT NULL DEFAULT '{}'::jsonb,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_global_notification_config_key ON global_notification_config(config_key);

-- Server-specific notification settings table
CREATE TABLE IF NOT EXISTS server_notification_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL REFERENCES connected_servers(id) ON DELETE CASCADE,
    ntfy_enabled BOOLEAN DEFAULT true,
    ntfy_base_url TEXT,
    ntfy_default_topic TEXT,
    email_enabled BOOLEAN DEFAULT false,
    sms_enabled BOOLEAN DEFAULT false,
    dnd_enabled BOOLEAN DEFAULT false,
    dnd_start TIME,
    dnd_end TIME,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(server_id)
);

CREATE INDEX IF NOT EXISTS idx_server_notification_settings_server_id ON server_notification_settings(server_id);

-- Notification logs table for audit trail
CREATE TABLE IF NOT EXISTS notification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID REFERENCES connected_servers(id) ON DELETE SET NULL,
    provider TEXT NOT NULL,
    target TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    priority TEXT DEFAULT 'default',
    success BOOLEAN NOT NULL,
    status_code INTEGER,
    error_message TEXT,
    response_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_logs_server_id ON notification_logs(server_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_created_at ON notification_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_logs_provider ON notification_logs(provider);
CREATE INDEX IF NOT EXISTS idx_notification_logs_success ON notification_logs(success);

-- Insert default global configurations
INSERT INTO global_notification_config (config_key, config_value, description)
VALUES
    ('ntfy_config', '{"base_url": "https://ntfy.sh"}'::jsonb, 'Default ntfy.sh configuration'),
    ('dnd_schedule', '{"enabled": false, "start": "22:00", "end": "07:00"}'::jsonb, 'Global Do Not Disturb schedule')
ON CONFLICT (config_key) DO NOTHING;

-- Row Level Security
ALTER TABLE global_notification_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE server_notification_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_logs ENABLE ROW LEVEL SECURITY;

-- Global config: authenticated users can read
CREATE POLICY "Users can read global config" ON global_notification_config
    FOR SELECT
    TO authenticated
    USING (true);

-- Server notification settings: owners and assigned users can read
CREATE POLICY "Users can view server notification settings" ON server_notification_settings
    FOR SELECT
    TO authenticated
    USING (
        server_id IN (
            SELECT id FROM connected_servers WHERE owner = auth.uid()
        )
        OR server_id IN (
            SELECT server_id FROM server_assignments WHERE assigned_to = auth.uid()
        )
    );

-- Server notification settings: only owners can insert
CREATE POLICY "Owners can create server notification settings" ON server_notification_settings
    FOR INSERT
    TO authenticated
    WITH CHECK (
        server_id IN (
            SELECT id FROM connected_servers WHERE owner = auth.uid()
        )
    );

-- Server notification settings: only owners can update
CREATE POLICY "Owners can update server notification settings" ON server_notification_settings
    FOR UPDATE
    TO authenticated
    USING (
        server_id IN (
            SELECT id FROM connected_servers WHERE owner = auth.uid()
        )
    );

-- Notification logs: owners and assigned users can read
CREATE POLICY "Users can view notification logs" ON notification_logs
    FOR SELECT
    TO authenticated
    USING (
        server_id IN (
            SELECT id FROM connected_servers WHERE owner = auth.uid()
        )
        OR server_id IN (
            SELECT server_id FROM server_assignments WHERE assigned_to = auth.uid()
        )
    );


