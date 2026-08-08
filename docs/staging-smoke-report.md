# Staging smoke report

Run date: 2026-08-08  
Repository: `release/xprize-2026`  
Commit under review: `6cab5d40444c5f4a8f01494f26e042ecd91cfe39`

This report is intentionally conservative. No staging credentials, hosted URL,
Cloud Run revision, Firebase project, or provider response evidence was
available in the workspace, so every external check is `blocked` or
`unverified`; no provider success is inferred from Terraform or adapters.

| Check | Status | Evidence required to close |
| --- | --- | --- |
| Firebase email verification/reset/revocation | Blocked | Staging project logs and authenticated browser/API smoke output |
| Gemini/Vertex structured generation | Blocked | Redacted request/result, model, latency, and persisted run audit |
| KMS credential signing and public verification | Blocked | Key version, signer audit record, and verification response |
| Email delivery | Blocked | Provider message ID, delivery result, and redacted notification audit |
| ClamAV quarantine/scan | Blocked | Staging scan result for clean and EICAR samples, without releasing malware |
| Telemetry and alert delivery | Blocked | Dashboard/alert screenshots or exported events with correlation IDs |
| Cloud Tasks OIDC and retry behavior | Blocked | Hosted task request, rejected-identity test, and retry/dead-letter evidence |
| Same-origin web-to-API routing | Blocked | Hosted browser network trace showing relative `/api/v1` and no public API bypass |
| PostgreSQL migrations and vertical slice | Blocked | Fresh staging database upgrade and client-to-paid-student test output |
| Rollback | Unverified | Revision rollback command/output and post-rollback health check |

Local code checks are recorded in
[`docs/release-readiness.md`](release-readiness.md) and do not close these
staging gates. The task endpoint currently has a registered notification
handler only; other outbox event types must be registered and smoke-tested
before hosted workflow claims are made.
