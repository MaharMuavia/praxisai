# XPRIZE readiness assessment

This is an evidence-based gap assessment of the repository as audited before the next implementation phase. It distinguishes code that exists from configuration that is merely declared and from capabilities that have not been tested against real external services.

## Executive status

The repository is a production-oriented modular-monolith MVP with a meaningful project-delivery core. It is not yet evidence-ready for the full competition claim. The largest gaps are real lead intake and admissions, a complete client-to-paid-student vertical slice, executable supervised agent actions, secure deployment configuration, same-origin API routing, and real provider smoke tests.

No repository evidence currently proves real customers, paying revenue, settled student earnings, production Gemini usage, Firebase deployment, or a live Google Cloud deployment. These must be recorded from real source systems before being presented as business evidence.

## Readiness matrix

| Area | Current evidence | Status | Required next action |
| --- | --- | --- | --- |
| Modular monolith | `apps/web`, `apps/api`, `packages/api-client`, Alembic migrations, PostgreSQL models | Implemented | Preserve boundaries while extending workflows |
| Project intake and scope | Project routes/services, scope versions, acceptance criteria, agent proposal, deterministic quote | Partial | Add lead intake, organization onboarding, explicit client acceptance, and a production funding gate |
| Staffing and offers | Staffing runs, candidates, immutable offers, accept/decline tests | Partial | Add evidence-linked scoring, conflict checks, final human squad approval, and student-facing offer lifecycle |
| Delivery and QA | Plans, tasks, milestones, deliverables, artifact hashes, QA findings, lead/client decisions | Partial | Add release gate, client completion acceptance, change-order completion path, and payout/credential end-to-end test |
| Billing evidence | Invoices, manual external funding, ledger, payout allocation/evidence | Partial | Add configured funding policy and provider/manual evidence smoke tests; never infer settlement |
| Credentials | Signed demo/KMS boundary, public verification, revocation, PDF/QR | Partial | Prove KMS signing and credential eligibility from the complete evidence chain |
| Learning | Learning paths/modules/enrollment/completion | Partial | Add applications, diagnostics, versioned rubrics, evidence submissions, readiness policy, appeals |
| CRM and lead qualification | No lead/contact/activity/opportunity/qualification aggregate or intake route | Missing | Add the first client lifecycle slice and lead qualification runtime contract |
| Shared agent runtime | Typed provider boundary and persisted `AgentRun`/`AgentRunEvent` models | Partial | Add common run contract, action registry, approvals, tool authorization, cost/latency, retries, and stale-result protection |
| AI execution | Fixture and Gemini structured generation produce proposals; mutation authority remains deterministic | Partial | Implement policy-checked low-risk action execution through outbox jobs and human approval for high-risk actions |
| Firebase | Firebase verification adapter and Terraform Identity Platform resource exist | Partial/unverified | Configure email verification, reset, revocation, disabled-user handling, membership checks, rate limits, and deployed smoke tests |
| Vertex AI Gemini | Gemini adapter and `aiplatform.googleapis.com` Terraform service declaration exist | Partial/unverified | Add Vertex service-account IAM, structured production smoke test, timeout/error redaction, and persisted audit proof |
| Same-origin API routing | Web config currently depends on API URL configuration; Terraform gives web an API Cloud Run URI | Missing | Route browser requests through relative `/api/v1` and configure Cloud Run ingress/routing |
| Demo isolation | `is_demo`, environment labels, fixture guards, frontend fallback tests, production config rejection | Partial | Add explicit `app_env=demo`, forbid fallback outside it, and test metric/demo isolation in staging/production configurations |
| Operations | Dashboard, jobs, queues, integrations, agent runs, audit, notifications, outbox recovery | Partial | Add agent action center, CRM/admissions/funding/release/payout/risk queues, and source-linked evidence metrics |
| XPRIZE evidence center | Analytics events and export jobs exist; no evidence-center contract or verified metric definitions | Missing | Add versioned metric definitions, source queries, demo exclusion, privacy-safe export, and audit trail |
| Observability | Structured logs, correlation IDs, provider sync records, basic monitoring Terraform | Partial | Add alert recipients, request/agent metrics, queue/dead-letter/payment/auth/DB health, and validated exporters |
| Security | Tenant authorization, CSRF middleware, rate-limit service, upload metadata controls, threat model docs/tests | Partial | Review IDOR, prompt/tool authorization, SSRF, file malware handling, webhook replay, mass assignment, concurrency, and production headers/rate limits |
| Public marketing | Landing and catch-all content pages exist; demo metrics are labeled | Partial | Add truthful pages and remove any unsupported outcome/customer claims |
| Deployment | Dockerfiles, Terraform, deployment docs | Unverified | Run Terraform validation, container builds, staging smoke tests, and configuration rejection checks |

## Current route and test evidence

The Next.js catch-all route currently serves public content and workspace metadata through a large `AppShell`. Existing route families include client, student, lead, operations/admin, university, project, learning, opportunity, credential verification, and login paths. Most role experiences are currently composed inside `apps/web/components/app-shell.tsx`, `student-career-workspace.tsx`, `employer-talent-workspace.tsx`, and `project-command-center.tsx`.

The API exposes approximately 77 route handlers across authentication, projects, scope control, offers, billing, credentials, operations, work, governance, notifications, university, workspaces, learning, and talent. Tests cover authorization, configuration, project transitions, pricing, matching, offers, funding/payout evidence, credentials, notifications, university reporting, outbox jobs, and selected frontend components. There are no tests proving the required lead-to-paid-student flow, real Vertex AI access, deployment routing, or tenant isolation across the entire vertical slice.

## Risk register

| Risk | Impact | Mitigation before production evidence |
| --- | --- | --- |
| Demo defaults or fallback leak into staging | Fictional business evidence is presented as real | Separate `demo` environment, fail closed outside it, add startup and metric tests |
| Browser uses localhost API URL in deployment | Users cannot complete workflows in public deployment | Same-origin `/api/v1` routing and bundle validation |
| AI output executes stale or unauthorized actions | Workflow, money, or access can be changed incorrectly | Typed action registry, policy checks, idempotency, concurrency version, approval records |
| Real Gemini provider is declared but untested | Competition claim is unsupported | Vertex IAM and real structured smoke test with redacted failures |
| Payment evidence is mistaken for settlement | Financial and legal misrepresentation | Provider/manual evidence state machine and explicit settlement evidence |
| Missing admissions/readiness lifecycle | Apprenticeship claims are not backed by product workflow | Build application, diagnostic, rubric, evidence, readiness, appeal slice |
| Large catch-all UI hides permissions and data loading | Role leakage and difficult maintenance | Split route-aware loaders, feature modules, and capability checks incrementally |
| External inputs contain prompt injection or malware | Agent and artifact compromise | Delimit untrusted data, authorized tools only, scan/quarantine artifacts, bounded URLs |
| Metrics lack definitions and exclusion policy | XPRIZE evidence cannot be audited | Versioned definitions with source tables, time windows, and demo filtering |

## Evidence policy

Until verified, the README and marketing copy must say that cloud deployment, Gemini, Firebase, email, payment, and real customer/revenue activity are unverified. Demo screenshots and fixtures are useful for product walkthroughs only and must remain visibly labeled.

