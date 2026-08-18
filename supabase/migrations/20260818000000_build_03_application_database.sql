-- Build 03 — Muse Application Database
-- Supabase Postgres stores Muse application state. Sibyl remains the intelligence
-- layer; this schema does not attempt to replace it.

create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- Profiles
-- ---------------------------------------------------------------------------
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default '',
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Documents
-- ---------------------------------------------------------------------------
create table public.documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  kind text not null check (kind in ('pdf', 'docx', 'txt', 'md')),
  status text not null default 'queued'
    check (status in ('queued', 'processing', 'ready', 'failed', 'needs_review')),
  storage_path text,
  size_bytes bigint not null default 0 check (size_bytes >= 0),
  page_count integer check (page_count is null or page_count >= 0),
  authored_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Processing jobs
-- ---------------------------------------------------------------------------
create table public.processing_jobs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  status text not null default 'queued'
    check (status in ('queued', 'running', 'complete', 'failed')),
  progress numeric(5,4) not null default 0 check (progress >= 0 and progress <= 1),
  current_stage text,
  stages jsonb not null default '[]'::jsonb,
  error jsonb,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Extraction runs — records individual extraction attempts/results.
-- ---------------------------------------------------------------------------
create table public.extraction_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  processing_job_id uuid references public.processing_jobs(id) on delete set null,
  extractor_version text,
  status text not null default 'running'
    check (status in ('running', 'complete', 'failed')),
  result jsonb not null default '{}'::jsonb,
  error jsonb,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Entities
-- ---------------------------------------------------------------------------
create table public.entities (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  type text not null
    check (type in ('person', 'project', 'concept', 'place', 'organization', 'work')),
  aliases text[] not null default '{}',
  description text not null default '',
  mention_count integer not null default 0 check (mention_count >= 0),
  first_seen_at timestamptz,
  last_seen_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Entity mentions — provenance of an entity inside a document/extraction.
-- ---------------------------------------------------------------------------
create table public.entity_mentions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  entity_id uuid not null references public.entities(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  extraction_run_id uuid references public.extraction_runs(id) on delete set null,
  char_start integer,
  char_end integer,
  page integer,
  text text,
  confidence numeric(5,4) check (confidence is null or (confidence >= 0 and confidence <= 1)),
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Relationships
-- ---------------------------------------------------------------------------
create table public.relationships (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  from_entity_id uuid not null references public.entities(id) on delete cascade,
  to_entity_id uuid not null references public.entities(id) on delete cascade,
  type text not null
    check (type in ('influences', 'contradicts', 'continues', 'mentions', 'collaborates_with', 'derived_from')),
  label text not null default '',
  confidence numeric(5,4) not null default 0
    check (confidence >= 0 and confidence <= 1),
  metadata jsonb not null default '{}'::jsonb,
  observed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (from_entity_id <> to_entity_id)
);

-- ---------------------------------------------------------------------------
-- Temporal events
-- ---------------------------------------------------------------------------
create table public.temporal_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  document_id uuid references public.documents(id) on delete cascade,
  extraction_run_id uuid references public.extraction_runs(id) on delete set null,
  title text not null,
  description text not null default '',
  kind text not null
    check (kind in ('created', 'abandoned', 'revisited', 'milestone', 'mention')),
  occurred_at timestamptz not null,
  confidence numeric(5,4) check (confidence is null or (confidence >= 0 and confidence <= 1)),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Provenance records
-- ---------------------------------------------------------------------------
create table public.provenance_records (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  extraction_run_id uuid references public.extraction_runs(id) on delete set null,
  page integer,
  char_start integer,
  char_end integer,
  quote text not null default '',
  context text,
  extractor_version text,
  confidence numeric(5,4) check (confidence is null or (confidence >= 0 and confidence <= 1)),
  derived_memory_ids uuid[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- User corrections
-- ---------------------------------------------------------------------------
create table public.user_corrections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  target_type text not null
    check (target_type in ('memory', 'entity', 'relationship', 'timeline_event')),
  target_id uuid not null,
  kind text not null
    check (kind in ('edit', 'merge', 'split', 'reject', 'retype')),
  field text,
  value text,
  reason text not null,
  status text not null default 'pending'
    check (status in ('pending', 'applied', 'rejected')),
  submitted_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Revivals
-- ---------------------------------------------------------------------------
create table public.revivals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  memory_id uuid not null,
  intent text not null
    check (intent in ('expand', 'reframe', 'combine', 'next_steps')),
  note text,
  summary text not null default '',
  suggestions jsonb not null default '[]'::jsonb,
  source_ids uuid[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------
create index documents_user_id_idx on public.documents(user_id);
create index documents_status_idx on public.documents(user_id, status);
create index processing_jobs_user_id_idx on public.processing_jobs(user_id);
create index processing_jobs_document_id_idx on public.processing_jobs(document_id);
create index extraction_runs_document_id_idx on public.extraction_runs(document_id);
create index entities_user_id_idx on public.entities(user_id);
create index entities_type_idx on public.entities(user_id, type);
create index entity_mentions_entity_id_idx on public.entity_mentions(entity_id);
create index entity_mentions_document_id_idx on public.entity_mentions(document_id);
create index relationships_from_entity_idx on public.relationships(from_entity_id);
create index relationships_to_entity_idx on public.relationships(to_entity_id);
create index temporal_events_user_time_idx on public.temporal_events(user_id, occurred_at);
create index temporal_events_document_id_idx on public.temporal_events(document_id);
create index provenance_document_id_idx on public.provenance_records(document_id);
create index corrections_user_status_idx on public.user_corrections(user_id, status);
create index revivals_user_created_idx on public.revivals(user_id, created_at desc);

-- ---------------------------------------------------------------------------
-- Updated-at triggers
-- ---------------------------------------------------------------------------
create trigger profiles_set_updated_at before update on public.profiles
for each row execute function public.set_updated_at();
create trigger documents_set_updated_at before update on public.documents
for each row execute function public.set_updated_at();
create trigger processing_jobs_set_updated_at before update on public.processing_jobs
for each row execute function public.set_updated_at();
create trigger extraction_runs_set_updated_at before update on public.extraction_runs
for each row execute function public.set_updated_at();
create trigger entities_set_updated_at before update on public.entities
for each row execute function public.set_updated_at();
create trigger relationships_set_updated_at before update on public.relationships
for each row execute function public.set_updated_at();
create trigger temporal_events_set_updated_at before update on public.temporal_events
for each row execute function public.set_updated_at();
create trigger provenance_records_set_updated_at before update on public.provenance_records
for each row execute function public.set_updated_at();
create trigger user_corrections_set_updated_at before update on public.user_corrections
for each row execute function public.set_updated_at();
create trigger revivals_set_updated_at before update on public.revivals
for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- Profile creation for new Supabase Auth users.
-- ---------------------------------------------------------------------------
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, display_name)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'displayName', new.raw_user_meta_data ->> 'display_name', '')
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

-- ---------------------------------------------------------------------------
-- Row Level Security: every application table is private to its owner.
-- ---------------------------------------------------------------------------
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

create policy "profiles own row" on public.profiles
for all using (auth.uid() = id) with check (auth.uid() = id);

create policy "documents own rows" on public.documents
for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "processing jobs own rows" on public.processing_jobs
for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "extraction runs own rows" on public.extraction_runs
for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "entities own rows" on public.entities
for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "entity mentions own rows" on public.entity_mentions
for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "relationships own rows" on public.relationships
for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "temporal events own rows" on public.temporal_events
for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "provenance records own rows" on public.provenance_records
for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "user corrections own rows" on public.user_corrections
for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "revivals own rows" on public.revivals
for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
