# Architecture

PraxisAI is a transactional modular monolith with separate web and API deployables. PostgreSQL is the source of truth. The API commits business state and an outbox record in one transaction; provider calls, notifications, PDF generation, and analytics export occur afterward in retryable handlers.

```mermaid
flowchart LR
  Browser --> Web[Next.js web]
  Web --> API[FastAPI API]
  API --> DB[(PostgreSQL)]
  API --> Storage[Private object storage]
  DB --> Outbox[Outbox worker]
  Outbox --> Gemini[Gemini / Vertex AI]
  Outbox --> Tasks[Cloud Tasks]
  Outbox --> Analytics[BigQuery]
  ExternalEvidence[Approved external funding and payout evidence] --> API
  API --> KMS[Credential signing key]
```

Routes authorize the active membership and call domain services. Domain services own workflow guards, version checks, immutable snapshots, audit records, ledger entries, and outbox events. Agents consume typed inputs and produce typed proposals; they receive no mutation tools.

The MVP remains a modular monolith because the lifecycle shares transactional invariants. Provider protocols are the only distributed boundaries. This avoids premature services without preventing later extraction of agents, files, or analytics workers.
