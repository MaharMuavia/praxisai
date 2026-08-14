# Staging smoke report

Run date: 2026-08-08  
Repository: `release/xprize-2026`  
Commit under review: `6cab5d40444c5f4a8f01494f26e042ecd91cfe39`

This report is intentionally conservative. No staging credentials, hosted URL,
Cloud Run revision, Supabase project, or provider response evidence was
available in the workspace, so every external check is `blocked` or
`unverified`; no provider success is inferred from Terraform or adapters.

| Check | Status | Evidence required to close |
| --- | --- | --- |
| Supabase Auth email verification/reset/revocation | Blocked | Staging project logs and authenticated browser/API smoke output |
| Gemini/Vertex structured generation | Blocked | Redacted request/result, model, latency, and persisted run audit |
| KMS credential signing and public verification | Blocked | Key version, signer audit record, and verification response |
| In-app notification worker | Blocked | Persisted notification, completed outbox event, and failed-event retry evidence |
| ClamAV quarantine/scan | Blocked | Staging scan result for clean and EICAR samples, without releasing malware |
| Monitoring and alert delivery | Blocked | Cloud Monitoring policy evidence and a delivered test alert |
| Cloud Scheduler and worker job | Blocked | Successful scheduled execution plus forced-failure exit and alert evidence |
| Same-origin web-to-API routing | Blocked | Hosted browser network trace showing relative `/api/v1` and no public API bypass |
| PostgreSQL migrations and vertical slice | Blocked | Fresh staging database upgrade and client-to-paid-student test output |
| Rollback | Unverified | Revision rollback command/output and post-rollback health check |

local code checks are recorded in
[`docs/release-readiness.md`](release-readiness.md) and do not close these
staging gates. Notification, malware-scan, and short-term retention handlers are
implemented in the worker, but hosted provider and failure-path evidence is
still required before those workflows are claimed operational.

## Actionable Steps for the Operator
1. Explicitly authorize the maintenance window and `npm run db:migrate`.
2. Configure protected GitHub Environments and Google Workload Identity.
3. Deploy staging and capture the hosted/provider evidence listed above, including a restore/rollback drill and alert delivery.
