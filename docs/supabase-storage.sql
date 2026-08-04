-- Private storage for server-authorized PraxisAI artifacts.
-- Run once in the Supabase SQL Editor. This does not expose the bucket publicly.

insert into storage.buckets (
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types
)
values (
  'internship-submissions',
  'internship-submissions',
  false,
  104857600,
  array[
    'application/pdf',
    'application/json',
    'application/zip',
    'image/png',
    'image/jpeg',
    'image/webp',
    'image/svg+xml',
    'text/plain',
    'text/markdown'
  ]::text[]
)
on conflict (id) do update
set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;
