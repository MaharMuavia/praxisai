# Data model

All business records use UUID primary keys and UTC timestamps. Foreign keys and frequent filters are indexed. Financial amounts use integer minor units and one ISO currency per quote or ledger transaction.

```mermaid
erDiagram
  ORGANIZATION ||--o{ MEMBERSHIP : contains
  USER ||--o{ MEMBERSHIP : holds
  ORGANIZATION ||--o{ PROJECT : owns
  PROJECT ||--o{ SCOPE_VERSION : versions
  SCOPE_VERSION ||--o{ ACCEPTANCE_CRITERION : defines
  PROJECT ||--o{ QUOTE : prices
  PROJECT ||--o{ TRANSITION : audits
  PROJECT ||--o{ ASSIGNMENT_OFFER : offers
  ASSIGNMENT_OFFER ||--o| PROJECT_ASSIGNMENT : accepts
  PROJECT ||--o{ TASK : plans
  PROJECT ||--o{ DELIVERABLE : receives
  DELIVERABLE ||--o{ ARTIFACT : versions
  ARTIFACT ||--o{ QA_REVIEW : evaluated_by
  PROJECT ||--o{ LEDGER_ENTRY : accounts
  PROJECT ||--o{ APPEAL : permits
  PROJECT ||--o{ CREDENTIAL : proves
  CREDENTIAL ||--o| CREDENTIAL_REVOCATION : revokes
  UNIVERSITY ||--o{ UNIVERSITY_ENROLLMENT : includes_by_consent
  UNIVERSITY ||--o{ INSTITUTIONAL_AGREEMENT : authorizes
  OUTBOX_EVENT ||--o{ JOB_ATTEMPT : retries
  OUTBOX_EVENT ||--o{ OUTBOX_RECOVERY : recovers
  OUTBOX_EVENT ||--o{ NOTIFICATION : delivers
  USER ||--o{ NOTIFICATION_PREFERENCE : configures
  OUTBOX_EVENT ||--o{ PROVIDER_SYNCHRONIZATION : evidences
  AGENT_RUN ||--o{ AGENT_RUN_EVENT : records
```

Scope and quote versions become immutable when sent for approval. Scope-change requests snapshot the accepted quote and released artifact; accepted change orders add explicit funding and compensation entitlements. Offers freeze pay, hours, deadline, revision, lead, and portfolio terms. Audit, transition, payment event, ledger, consent, agent-run, reputation, credential, revocation, job-attempt, and recovery records are append-only; reversals add records instead of deleting evidence.
