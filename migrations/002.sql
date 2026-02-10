create table public.connected_servers (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()),
  last_seen timestamp with time zone default timezone('utc'::text, now()),
  status text default 'offline',
  name text,
  metadata jsonb default '{}'::jsonb
);

alter table public.connected_servers enable row level security;