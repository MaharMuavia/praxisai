# PraxisAI implementation plan

This plan follows the Phase 0 audit and preserves the existing modular monolith. It prioritizes a real, testable client-to-paid-student workflow over additional dashboard breadth.

## Existing code map

| Requirement | Reuse | Modify | New or split |
| --- | --- | --- | --- |
| Identity and memberships | `auth/dependencies.py`, `auth/service.py`, `api/auth.py`, `User`, `OrganizationMembership` | Capability checks and Firebase lifecycle | Authentication-sensitive audit events and rate-limit coverage |
| Project delivery | `projects/service.py`, `api/projects.py`, project models/schemas | Add client acceptance, funding policy, release/completion guards | Route-level loaders and feature modules |
| Scope and pricing | `ProjectScopeVersion`, `AcceptanceCriterion`, `Quote`, `domain/pricing.py`, scope routes | Add project-category boundaries and quote approval/acceptance terms | Versioned service-category configuration |
| Staffing | `staffing/service.py`, `talent/service.py`, `StaffingRun`, `StaffingCandidate`, offers | Add evidence-linked scoring, conflict checks, final squad approval | Explainable matching contract and review UI |
| Learning | `learning/service.py`, learning models/routes | Add application, diagnostic, rubric, evidence, readiness policy | Admissions and readiness modules |
| Delivery evidence and QA | deliverable/artifact/QA/lead/client models and project routes | Add provenance validation and release gate | Evidence viewer and approval panel |
| Funding and payout | billing service/routes, invoice/payment/ledger/payout models | Add configured funding policy and verified settlement states | Provider adapter only where tested |
| Credentials | credentials lifecycle/service/routes, consent and credential models | Require complete evidence and human approval | Production KMS smoke test |
| AI proposals | `agents/provider.py`, `AgentRun`, `AgentRunEvent`, `PromptVersion` | Common run contract, versioned schemas, risk class, cost/latency | Shared runtime, action registry, approval executor |
| Reliability | outbox services, Cloud Tasks adapter, rate-limit service, provider sync | Add agent action retries and stale-result guards | Alert recipients and metric definitions |
| Frontend | existing `AppShell`, workspaces, demo boundary, API client types | Same-origin API adapter, capability-driven navigation, live/error states | Split route modules and internal primitives |
| Infrastructure | Terraform Cloud Run, SQL, Storage, Tasks, IAM, Identity Platform, KMS | Add complete env injection, Vertex IAM, routing, monitoring recipients | Deployment validation and smoke-test scripts |

## Phase 0: audit and truthfulness

Completed by this document set:

- architecture, domain, route, model, test, and deployment map;
- implemented/partial/missing readiness assessment;
- unsupported claims and risk register;
- reuse/modify/new migration plan.

Exit criteria: documentation accurately describes the current repository and does not claim real deployment, customers, revenue, Gemini, Firebase, or payment success without evidence.

## Phase 1: competition-critical production repair

### 1. Environment contract

Extend the typed settings contract with explicit `local`, `test`, `demo`, `staging`, and `production` semantics. Require production/staging values for identity, Gemini, Google Cloud, secure cookies, CORS, public URLs, KMS, payment/manual-settlement, email, and telemetry. Reject localhost URLs, demo identity, fixture AI, demo signing, and unsafe fallback outside `demo`.

Acceptance tests must cover startup rejection, safe error messages, and no fictional records in staging/production data paths.

### 2. Same-origin web routing

Introduce one typed browser API adapter that uses relative `/api/v1` in deployed web builds and a documented local override only for local development. Add a build/startup check that fails if a public bundle points at localhost. Configure Cloud Run routing so `/api/*` reaches the API service.

### 3. Firebase and Vertex AI

Complete the Firebase adapter and deployment configuration for verification, reset, revocation, disabled users, organization membership, secure cookies, CSRF, rate limits, and audit events.

Complete Vertex AI service-account access with the minimum IAM permission. Add a real structured Gemini smoke test that validates schema, persists an agent run and audit metadata, redacts errors, and verifies timeout behavior. The smoke test requires operator-owned credentials and must be reported as unverified when unavailable.

### 4. Health, readiness, and observability

Keep `/health` lightweight. Make `/ready` verify required dependencies without leaking connection details. Add structured request and agent metrics, queue/dead-letter, payment exception, authentication failure, database pool, token/cost, and business-funnel metrics. Every alert policy must have a configured notification channel.

Phase 1 exit criteria: production/staging config validation, same-origin routing, container build, Terraform validation, and provider smoke tests pass in an operator-owned environment.

## Phase 2: thinnest complete vertical slice

Build one constrained category first: AI workflow automation. Reuse project and scope entities; add only the missing aggregates required for lead, admissions, diagnostic/readiness, and evidence.

### Client path

1. Public lead intake stores a normalized lead and contact with consent and correlation metadata.
2. Lead qualification produces a typed proposal: need, urgency, budget band, category, missing data, risk flags, and recommendation.
3. Low-risk leads receive an approved follow-up task; uncertain/high-risk leads enter operations.
4. Verified client organization creates a structured project brief.
5. Scope and pricing agents propose bounded deliverables; deterministic services calculate the quote.
6. Operations approves or edits scope and quote.
7. Client accepts scope, commercial, IP, communication, revision, and cancellation terms.
8. Invoice/payment request requires verified funding evidence before activation.

### Student path

1. Student application stores target track and required policy consent.
2. Diagnostic submission references versioned rubric criteria and evidence.
3. Diagnostic agent produces findings; deterministic policy assigns readiness and complexity ceiling.
4. Learning coach proposes a plan; modules and evidence submissions update progress.
5. Human review is required for admission, high-stakes readiness, suspension, and credential access.
6. Eligible students receive explainable offers with pay, hours, deadline, supervision, revisions, portfolio terms, and decline-without-penalty language.

### Delivery and outcome

1. Matching filters eligibility, conflicts, workload, availability, and complexity before AI ranking.
2. Operations approves the final squad; accepted offers create assignments.
3. Orchestrator proposes an approved plan and executes only low-risk task/reminder/defect actions.
4. Students submit versioned artifacts with hashes and provenance.
5. QA agent evaluates against deterministic criteria; lead approves release; client accepts.
6. Completion creates payout approval; verified payout evidence creates earnings; complete evidence enables a credential.

Phase 2 exit criteria: one end-to-end test covers lead -> approved project -> funded work -> student offer -> accepted assignment -> deliverable -> QA -> release -> client acceptance -> payout evidence -> credential verification. Failures require human recovery paths.

## Phase 3: supervised agent control plane

Create a shared agent runtime around the existing provider protocol. Add typed agent definitions, prompt versions, input/output hashes, context references, action classes, tool authorization, approval requirements, idempotency, concurrency/version checks, retries, stale-result rejection, and run timeline persistence.

The action executor uses existing domain services and outbox/Cloud Tasks boundaries. AI never gets a raw database session, unrestricted HTTP client, credential, payment action, or authority to bypass a policy.

Add contract tests for every agent schema, action authorization tests, redacted failure tests, replay/idempotency tests, and human override/recovery tests.

## Phase 4: professional role experiences

Split `AppShell` into role-aware layout, navigation, header/notifications/search, route-level data loaders, feature modules, and mutation hooks. Split student, employer, and command-center components by domain only as routes gain live data. Add reusable internal primitives for forms, dialogs, drawers, tabs, cards, tables, states, timelines, evidence, approvals, agent runs, money, and dates.

Expand pages only where a backed workflow exists: student admissions/learning/evidence, client onboarding/scope/funding/review, expert lead review, operations queues, university privacy-safe reporting, and admin configuration. Do not hard-code production curriculum or business metrics in the frontend.

## Phase 5: business evidence center

Create versioned metric definitions backed by transactional source tables. Each definition records meaning, source tables, time window, demo exclusion, privacy rule, and calculation timestamp. Add a privacy-safe export job and audit trail. Only real records from configured environments count as competition evidence.

## Phase 6: hardening and operating readiness

Run tenant-isolation, IDOR, capability, CSRF, session, prompt injection, tool authorization, file validation/malware, signed URL, SSRF, webhook replay, CSV injection, mass assignment, race, duplicate payout, stale-agent, backup/restore, migration, performance, accessibility, 200% zoom, reduced-motion, and failure-injection tests. Add data export/deletion workflows, incident and production runbooks, and a staging smoke test with operator credentials.

## Verification gates

For each phase, run the applicable repository commands and report exact results:

```text
npm run format
npm run lint
npm run typecheck
npm test
npm run build
npm run test:e2e
npm run db:check
terraform fmt -check
terraform validate
```

No deployment, Gemini, Firebase, email, payment, or cloud capability is considered complete until it has been exercised in the target environment and its evidence is retained.

