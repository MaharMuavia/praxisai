# Security and privacy

## Controls

- API service-layer authorization scopes every project and artifact to active memberships or accepted assignments.
- Secure session cookies, CSRF tokens, explicit CORS origins, correlation IDs, safe errors, input limits, and database-backed rate limits protect HTTP boundaries.
- Upload adapters enforce size/type rules, private storage, authorization before signed URLs, and an explicit malware-scan state.
- Manual funding evidence is canonically hashed, keyed idempotently, audited, and posted through balanced ledger entries. It does not assert that PraxisAI processed a payment.
- Secrets never enter frontend bundles, prompts, fixtures, logs, or audit payloads. Production rejects demo identity, fixture AI, disposable signing keys, insecure cookies, and live-payment flags.
- Public credentials use a dedicated consented schema and verify their signature on every lookup.

## Threat model

| Threat | Required control |
| --- | --- |
| One client or student requests another tenant's project | Organization and assignment predicates return not found; cross-tenant tests cover both roles. |
| Prompt injection in a brief or README | Treat content as delimited untrusted data; no agent receives mutation tools or secrets. |
| Malicious artifact | Private quarantine, type/size validation, scan state, isolated CI; never execute it in the API process. |
| Duplicate funding record or payout approval | Idempotency keys, evidence hashes, row locks, balanced ledger checks, and separated approval/execution. |
| Agent hallucinates successful QA | Deterministic evidence precedes AI; lead and coordinator decisions are separately required and audited. |
| Credential leaks client IP or is forged | Consent snapshot, purpose-built public schema, random slug, canonical hash, asymmetric signature, and revocation record. |
| Coordinator misuse or appeal conflict | Immutable audit events, reason capture, least privilege, and reviewer conflict checks. |
| Client pressures unpaid scope expansion | Scope classification, escalation, deadline pause policy, and accepted compensated change order before new work. |
| AI flag harms reputation | Only resolved evidence approved by a human can create a reputation event; reversals preserve history. |
| University accesses earnings or private evidence | Active agreement, association, consent, purpose limitation, cohort suppression, and audited expiring exports. |
| Invitation or public action replay | Random tokens stored only as hashes, expiration, revocation, rate limiting, and single-use state. |

Legal terms, retention periods, jurisdictional employment/payment treatment, and breach procedures require qualified review before production.
