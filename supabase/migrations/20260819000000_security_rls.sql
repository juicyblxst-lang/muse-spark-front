-- Muse security boundary: user-owned records are isolated by auth.uid().
-- Service-role operations remain server-only and bypass RLS by design.

create or replace function public.muse_is_owner(row_user_id uuid)
returns boolean
language sql
stable
as $$
  select auth.uid() = row_user_id;
$$;

alter table public.documents enable row level security;
alter table public.processing_jobs enable row level security;

-- These tables may not exist until their owning migrations are applied.
-- Policies are intentionally scoped to user_id and never use client-provided ownership claims.
drop policy if exists "documents_owner_select" on public.documents;
create policy "documents_owner_select" on public.documents
  for select using (public.muse_is_owner(user_id));

drop policy if exists "documents_owner_insert" on public.documents;
create policy "documents_owner_insert" on public.documents
  for insert with check (public.muse_is_owner(user_id));

drop policy if exists "documents_owner_update" on public.documents;
create policy "documents_owner_update" on public.documents
  for update using (public.muse_is_owner(user_id))
  with check (public.muse_is_owner(user_id));

drop policy if exists "documents_owner_delete" on public.documents;
create policy "documents_owner_delete" on public.documents
  for delete using (public.muse_is_owner(user_id));

drop policy if exists "processing_jobs_owner_select" on public.processing_jobs;
create policy "processing_jobs_owner_select" on public.processing_jobs
  for select using (public.muse_is_owner(user_id));

drop policy if exists "processing_jobs_owner_insert" on public.processing_jobs;
create policy "processing_jobs_owner_insert" on public.processing_jobs
  for insert with check (public.muse_is_owner(user_id));

drop policy if exists "processing_jobs_owner_update" on public.processing_jobs;
create policy "processing_jobs_owner_update" on public.processing_jobs
  for update using (public.muse_is_owner(user_id))
  with check (public.muse_is_owner(user_id));

drop policy if exists "processing_jobs_owner_delete" on public.processing_jobs;
create policy "processing_jobs_owner_delete" on public.processing_jobs
  for delete using (public.muse_is_owner(user_id));

-- Storage object paths must start with the authenticated user's UUID.
drop policy if exists "muse_documents_owner_select" on storage.objects;
create policy "muse_documents_owner_select" on storage.objects
  for select to authenticated
  using (bucket_id = 'muse-documents' and (storage.foldername(name))[1] = (select auth.uid()::text));

drop policy if exists "muse_documents_owner_insert" on storage.objects;
create policy "muse_documents_owner_insert" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'muse-documents' and (storage.foldername(name))[1] = (select auth.uid()::text));

drop policy if exists "muse_documents_owner_update" on storage.objects;
create policy "muse_documents_owner_update" on storage.objects
  for update to authenticated
  using (bucket_id = 'muse-documents' and (storage.foldername(name))[1] = (select auth.uid()::text))
  with check (bucket_id = 'muse-documents' and (storage.foldername(name))[1] = (select auth.uid()::text));

drop policy if exists "muse_documents_owner_delete" on storage.objects;
create policy "muse_documents_owner_delete" on storage.objects
  for delete to authenticated
  using (bucket_id = 'muse-documents' and (storage.foldername(name))[1] = (select auth.uid()::text));
