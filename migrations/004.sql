-- Table to track server assignments/sharing between users
-- This allows owners to grant access to their servers to other users

CREATE TABLE IF NOT EXISTS server_assignments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    server_id UUID NOT NULL REFERENCES connected_servers(id) ON DELETE CASCADE,
    assigned_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    assigned_to UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Prevent duplicate assignments
    UNIQUE(server_id, assigned_to)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_server_assignments_server_id ON server_assignments(server_id);
CREATE INDEX IF NOT EXISTS idx_server_assignments_assigned_to ON server_assignments(assigned_to);
CREATE INDEX IF NOT EXISTS idx_server_assignments_assigned_by ON server_assignments(assigned_by);

-- Row Level Security
ALTER TABLE server_assignments ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view assignments for servers they own or are assigned to
CREATE POLICY "Users can view their own assignments" ON server_assignments
    FOR SELECT
    USING (
        assigned_to = auth.uid()
        OR assigned_by = auth.uid()
        OR EXISTS (
            SELECT 1 FROM connected_servers
            WHERE connected_servers.id = server_assignments.server_id
            AND connected_servers.owner = auth.uid()
        )
    );

-- Policy: Only server owners can insert assignments
CREATE POLICY "Server owners can create assignments" ON server_assignments
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM connected_servers
            WHERE connected_servers.id = server_assignments.server_id
            AND connected_servers.owner = auth.uid()
        )
    );

-- Policy: Server owners can delete assignments for their servers
CREATE POLICY "Server owners can delete assignments" ON server_assignments
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM connected_servers
            WHERE connected_servers.id = server_assignments.server_id
            AND connected_servers.owner = auth.uid()
        )
    );

