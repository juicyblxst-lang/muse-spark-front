-- Muse Build 04: private document file storage.
-- Original uploaded files live in Supabase Storage; metadata remains in public.documents.
-- Path convention: <auth.uid>/<document_id>/<filename>

insert into storage.buckets (id, name, public, file_size_limit)
values (
  'muse-documents',
  'muse-documents',
  false,
  52428800
)
on conflict (id) do update
set public = false,
    file_size_limit = excluded.file_size_limit;

create policy "Muse users can view their document files"
on storage.objects
for select
to authenticated
using (
  bucket_id = 'muse-documents'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);

create policy "Muse users can upload their document files"
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'muse-documents'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);

create policy "Muse users can update their document files"
on storage.objects
for update
to authenticated
using (
  bucket_id = 'muse-documents'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
)
with check (
  bucket_id = 'muse-documents'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);

create policy "Muse users can delete their document files"
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'muse-documents'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);
