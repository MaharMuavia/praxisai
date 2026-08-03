# Core product finalization plan

This document records the remaining product, security, privacy, and operational blockers being closed on `agent/core-product-finalization`. The branch is based on the latest `agent/core-product-hardening` branch. The final pull request targets that branch and is intentionally not merged by automation.

## Intake integrity and privacy

| Severity | Issue and impact | Root cause and approach | Verification |
| --- | --- | --- | --- |
| Critical | Consent could be submitted as false, weakening the processing boundary. | The discriminated request schema used `bool`; constrain it to `Literal[True]` and test rejected false, missing, and malformed values. | API validation tests and OpenAPI inspection. |
| High | Expert submissions fabricated one year of experience and omitted the experience narrative. | The public form did not collect the backend-required value. Add explicit typed fields and map them without inference. | Frontend contract tests and API validation tests. |
| Critical | Idempotency and rate-limit charging could diverge under concurrent retries. | Reserve an idempotency key before consuming limits and complete or fail that reservation exactly once; retain the submission unique constraint as a final integrity guard. | Sequential replay, conflicting payload, and concurrent reservation tests. |
| Critical | Review version checks were not serialized. | Lock the authoritative row before checking the expected version and commit the audit event with the mutation. | Stale-version and transition tests. |
| High | Queue responses exposed contact email and raw payload broadly. | Add a privacy-safe summary queue contract with validated filters and cursor pagination; keep sensitive payload detail behind the detail route. | Schema/API contract tests and UI tests. |
| High | Retention anonymization left identifiers, owner data, and review text behind and used a fake email. | Clear direct and indirect personal fields, use nullable contact data, make anonymization idempotent, and make anonymized/deleted records terminal. | Privacy lifecycle tests. |
| High | Withdrawal and deletion had no complete operator workflow. | Add explicit request/approve and terminal deletion endpoints with audit events and authorization. | API tests and audit assertions. |

## Review UX and accessibility

| Severity | Issue and impact | Approach | Verification |
| --- | --- | --- | --- |
| High | Review UI offered invalid transitions and sent unrelated fields. | Return authoritative allowed transitions and render transition-specific forms. | API and component tests. |
| High | Owners and audit history were unavailable in the review surface. | Add privacy-safe owners and audit timeline endpoints and render both in detail. | API/component tests. |
| High | Conflict and API errors were reduced to opaque status text. | Parse the shared error envelope, preserve correlation IDs, and offer reload/retry recovery on 409. | Error parser and conflict tests. |
| High | Public intake errors were not consistently linked to controls. | Add a focusable error summary, `aria-invalid`, and `aria-describedby` for each field. | Accessibility-focused component tests and E2E. |
| High | Successful public intake remained editable and could be resubmitted accidentally. | Keep the idempotency key stable through retries, lock the successful receipt view, and require an explicit reset to submit again. | Component tests. |

## Operations and architecture

| Severity | Issue and impact | Approach | Verification |
| --- | --- | --- | --- |
| High | Retention had a callable function but no scheduled production job. | Register a retention outbox event and process it through the existing worker with bounded batches, retry, and dead-letter behavior; add deployment scheduling configuration. | Worker tests and Terraform/config checks. |
| Medium | High-risk routes inherited broad AppShell queries and mutation state. | Move jobs, offers, exports, approvals, and risks into route-owned feature modules and disable unrelated workspace queries for those paths. | Route tests, typecheck, and E2E. |
| High | Contracts were not all aligned between frontend and backend. | Regenerate the API client after the intake contract changes and test company, student, expert, and university payloads. | OpenAPI generation and full test suite. |

## Verification gate

Before handoff run `npm run format`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`, the API migration/OpenAPI checks, and the frontend E2E suite. Report any unavailable check as unverified rather than inferring success.
