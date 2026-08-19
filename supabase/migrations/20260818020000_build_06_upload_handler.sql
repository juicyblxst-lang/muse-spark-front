-- Muse Build 06: upload-handler schema compatibility.
-- Build 03 omitted legacy .doc from documents.kind; Build 06 supports .doc uploads.

drop constraint if exists documents_kind_check on public.documents;
alter table public.documents
  add constraint documents_kind_check
  check (kind in ('pdf', 'doc', 'docx', 'txt', 'md'));
