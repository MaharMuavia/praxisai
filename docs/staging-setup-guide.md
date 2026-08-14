# PraxisAI staging setup and cost controls

Staging uses Supabase PostgreSQL/Auth/Storage and the Google Cloud resources in
`infra/terraform`. The exact deployment sequence is in `docs/deployment.md`.
Do not treat this document as pricing advice; review the provider calculators
and configure project budgets before applying a plan.

## Bounded staging resources

- Web and API Cloud Run services scale to zero and cap at five instances.
- The worker is a single-task Cloud Run job with no platform retry; Cloud
  Scheduler starts it every two minutes and application retries are bounded.
- Worker Direct VPC egress sends only private-address traffic through the
  operator-supplied subnet to an RFC1918 ClamAV address.
- The error-log bucket is versioned and expires objects after 365 days. The API
  has no read or delete permission on this bucket.
- Artifact Registry uses immutable tags. Retain approved release digests and
  remove rejected/unneeded images through an operator-reviewed registry policy.
- Secret Manager references use explicit numeric versions. Rotation creates a
  new version, updates the reviewed tfvars value, and rolls a new revision; it
  never uses `latest`.
- The KMS signing key and version, secret containers, state bucket, and release
  repository are protected from routine Terraform destruction.

## Charge-bearing dependencies

Review usage and budget alerts for Supabase, Cloud Run services/job, Cloud
Scheduler, Secret Manager versions, the private VPC/ClamAV service, Cloud
Storage, Artifact Registry, KMS, Cloud Logging/Monitoring, and Gemini/Vertex.
No BigQuery export or email-delivery provider is implemented or provisioned.

## Teardown boundary

There is intentionally no one-command teardown. Protected state, signing keys,
secrets, evidence logs, and immutable release images require separate retention
decisions. To retire staging, first stop Scheduler and Cloud Run traffic using a
reviewed saved plan, preserve required database/log/release evidence, then
prepare a second plan for individually approved resources. Never remove
`prevent_destroy` controls or delete Supabase data as part of an unreviewed
bulk destroy.
