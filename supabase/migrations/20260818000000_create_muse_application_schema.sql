-- Muse Build 3: application-state database.
-- Supabase Auth remains the identity source; Sibyl remains the memory/intelligence layer.
-- This migration stores Muse application state and enforces per-user isolation with RLS.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default '',
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, display_name, avatar_url)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'displayName', new.raw_user_meta_data ->> 'full_name', ''),
    new.raw_user_meta_data ->> 'avatar_url'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

-- Backfill profiles for users that existed before this migration.
insert into public.profiles (id, display_name, avatar_url)
select
  id,
  coalesce(raw_user_meta_data ->> 'displayName', raw_user_meta_data ->> 'full_name', ''),
  raw_user_meta_data ->> 'avatar_url'
from auth.users
on conflict (id) do nothing;

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  file_name text not null,
  kind text not null check (kind in ('pdf', 'docx', 'txt', 'md')),
  status text not null default 'queued' check (status in ('queued', 'processing', 'ready', 'failed', 'needs_review')),
  size_bytes bigint not null default 0 check (size_bytes >= 0),
  page_count integer,
  excerpt text,
  language text,
  authored_at timestamptz,
  uploaded_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists documents_user_id_idx on public.documents(user_id);
create index if not exists documents_user_status_idx on public.documents(user_id, status);

create table if not exists public.processing_jobs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  status text not null default 'queued' check (status in ('queued', 'running', 'complete', 'failed')),
  progress numeric(5,4) not null default 0 check (progress >= 0 and progress <= 1),
  current_stage text,
  stages jsonb not null default '[]'::jsonb,
  discovered jsonb not null default '{"memories":0,"entities":0,"relationships":0,"timelineEvents":0,"highlights":[]}'::jsonb,
  error jsonb,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists processing_jobs_user_id_idx on public.processing_jobs(user_id);
create index if not exists processing_jobs_document_id_idx on public.processing_jobs(document_id);

create table if not exists public.extraction_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  processing_job_id uuid references public.processing_jobs(id) on delete set null,
  extractor_version text not null,
  status text not null default 'running' check (status in ('running', 'complete', 'failed')),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  result jsonb not null default '{}'::jsonb,
  error jsonb,
  created_at timestamptz not null default now()
);

create index if not exists extraction_runs_user_id_idx on public.extraction_runs(user_id);
create index if not exists extraction_runs_document_id_idx on public.extraction_runs(document_id);

create table if not exists public.entities (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  type text not null check (type in ('person', 'project', 'concept', 'place', 'organization', 'work')),
  aliases text[] not null default '{}',
  description text not null default '',
  first_seen_at timestamptz,
  last_seen_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists entities_user_id_idx on public.entities(user_id);
create index if not exists entities_user_type_idx on public.entities(user_id, type);

create table if not exists public.entity_mentions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  entity_id uuid not null references public.entities(id) on delete cascade,
  document_id uuid references public.documents(id) on delete cascade,
  extraction_run_id uuid references public.extraction_runs(id) on delete set null,
  memory_id uuid,
  char_start integer,
  char_end integer,
  mention_text text not null,
  confidence numeric(5,4),
  created_at timestamptz not null default now()
);

create index if not exists entity_mentions_user_id_idx on public.entity_mentions(user_id);
create index if not exists entity_mentions_entity_id_idx on public.entity_mentions(entity_id);
create index if not exists entity_mentions_document_id_idx on public.entity_mentions(document_id);

create table if not exists public.relationships (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  from_entity_id uuid not null references public.entities(id) on delete cascade,
  to_entity_id uuid not null references public.entities(id) on delete cascade,
  type text not null check (type in ('influences', 'contradicts', 'continues', 'mentions', 'collaborates_with', 'derived_from')),
  label text not null default '',
  confidence numeric(5,4),
  memory_ids uuid[] not null default '{}',
  observed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (from_entity_id <> to_entity_id)
);

create index if not exists relationships_user_id_idx on public.relationships(user_id);
create index if not exists relationships_from_entity_idx on public.relationships(from_entity_id);
create index if not exists relationships_to_entity_idx on public.relationships(to_entity_id);

create table if not exists public.temporal_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  description text not null default '',
  kind text not null check (kind in ('created', 'abandoned', 'revisited', 'milestone', 'mention')),
  occurred_at timestamptz not null,
  memory_ids uuid[] not null default '{}',
  document_ids uuid[] not null default '{}',
  entity_ids uuid[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists temporal_events_user_occurred_idx on public.temporal_events(user_id, occurred_at desc);

create table if not exists public.provenance_records (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  page integer,
  char_start integer,
  char_end integer,
  quote text not null default '',
  context text not null default '',
  extracted_at timestamptz not null default now(),
  extractor_version text not null,
  derived_memory_ids uuid[] not null default '{}',
  confidence numeric(5,4),
  created_at timestamptz not null default now()
);

create index if not exists provenance_records_user_id_idx on public.provenance_records(user_id);
create index if not exists provenance_records_document_id_idx on public.provenance_records(document_id);

create table if not exists public.user_corrections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  target_type text not null check (target_type in ('memory', 'entity', 'relationship', 'timeline_event')),
  target_id uuid not null,
  kind text not null check (kind in ('edit', 'merge', 'split', 'reject', 'retype')),
  field text,
  value text,
  reason text not null,
  status text not null default 'pending' check (status in ('pending', 'applied', 'rejected')),
  submitted_at timestamptz not null default now(),
  applied_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists user_corrections_user_id_idx on public.user_corrections(user_id);
create index if not exists user_corrections_target_idx on public.user_corrections(target_type, target_id);

create table if not exists public.revivals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  memory_id uuid not null,
  intent text not null check (intent in ('expand', 'reframe', 'combine', 'next_steps')),
  note text,
  summary text not null default '',
  suggestions jsonb not null default '[]'::jsonb,
  source_ids uuid[] not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists revivals_user_id_idx on public.revivals(user_id);
create index if not exists revivals_memory_id_idx on public.revivals(memory_id);

-- Keep timestamps consistent on mutable application tables.
drop trigger if exists documents_set_updated_at on public.documents;
create trigger documents_set_updated_at before update on public.documents for each row execute function public.set_updated_at();
drop trigger if exists processing_jobs_set_updated_at on public.processing_jobs;
create trigger processing_jobs_set_updated_at before update on public.processing_jobs for each row execute function public.set_updated_at();
drop trigger if exists entities_set_updated_at on public.entities;
create trigger entities_set_updated_at before update on public.entities for each row execute function public.set_updated_at();
drop trigger if exists relationships_set_updated_at on public.relationships;
create trigger relationships_set_updated_at before update on public.relationships for each row execute function public.set_updated_at();
drop trigger if exists temporal_events_set_updated_at on public.temporal_events;
create trigger temporal_events_set_updated_at before update on public.temporal_events for each row execute function public.set_updated_at();

-- RLS: every application row belongs to the authenticated Supabase user.
alter table public.profiles enable row level security;
alter table public.documents enable row level security;
alter table public.processing_jobs enable row level security;
alter table public.extraction_runs enable row level security;
alter table public.entities enable row level security;
alter table public.entity_mentions enable row level security;
alter table public.relationships enable row level security;
alter table public.temporal_events enable row level security;
alter table public.provenance_records enable row level security;
alter table public.user_corrections enable row level security;
alter table public.revivals enable row level security;

create policy profiles_select_own on public.profiles for select using (auth.uid() = id);
create policy profiles_insert_own on public.profiles for insert with check (auth.uid() = id);
create policy profiles_update_own on public.profiles for update using (auth.uid() = id) with check (auth.uid() = id);

create policy documents_own on public.documents for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy processing_jobs_own on public.processing_jobs for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy extraction_runs_own on public.extraction_runs for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy entities_own on public.entities for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy entity_mentions_own on public.entity_mentions for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy relationships_own on public.relationships for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy temporal_events_own on public.temporal_events for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy provenance_records_own on public.provenance_records for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy user_corrections_own on public.user_corrections for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy revivals_own on public.revivals for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
