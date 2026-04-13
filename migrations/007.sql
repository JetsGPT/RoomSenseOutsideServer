-- Migration: Rebind connected_servers.owner FK to public.users
-- Date: 2026-04-13
-- Reason:
-- Previous FK pointed to auth.users(id), but app queries/embeds expect public.users(id).

DO $$
DECLARE
    fk_name text;
BEGIN
    -- Find any existing FK constraint on public.connected_servers(owner)
    SELECT tc.constraint_name
    INTO fk_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema = 'public'
      AND tc.table_name = 'connected_servers'
      AND kcu.column_name = 'owner'
    LIMIT 1;

    -- Drop prior FK (e.g. owner -> auth.users), if present
    IF fk_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE public.connected_servers DROP CONSTRAINT %I', fk_name);
    END IF;
END $$;

-- Ensure owner column exists
ALTER TABLE public.connected_servers
ADD COLUMN IF NOT EXISTS owner uuid;

-- Ensure target FK exists and points to public.users(id)
ALTER TABLE public.connected_servers
DROP CONSTRAINT IF EXISTS connected_servers_owner_fkey;

ALTER TABLE public.connected_servers
ADD CONSTRAINT connected_servers_owner_fkey
FOREIGN KEY (owner)
REFERENCES public.users(id)
ON DELETE SET NULL;

-- Keep owner lookup index
CREATE INDEX IF NOT EXISTS idx_connected_servers_owner
ON public.connected_servers(owner);
