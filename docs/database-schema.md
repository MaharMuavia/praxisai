# PraxisAI database schema

PraxisAI uses PostgreSQL as its transactional system of record. Supabase is supported as managed
PostgreSQL, but the schema is owned by SQLAlchemy models and Alembic migrations—not by dashboard
clicks or a separate SQL file.

Canonical sources:

- Models: `apps/api/app/domain/models.py`
- Migrations: `apps/api/alembic/versions/`
- Current migration head: `e2f3a4b5c6d7`
- Schema drift check: `npm run db:check`

The current metadata inventory contains 100 application tables. All application tables use UUID
primary keys. Mutable entities also carry creation and update timestamps. Money is stored as
integer minor units plus an ISO 4217 currency code. JSON columns hold typed snapshots or
provider-neutral metadata, never secrets.

## Identity, organizations, and policy

| Table                      | Purpose and principal relationships                                           |
| -------------------------- | ----------------------------------------------------------------------------- |
| `users`                    | Platform identity. External provider subjects and email addresses are unique. |
| `organizations`            | Client, university, and platform organizations. `slug` is unique.             |
| `organization_memberships` | User-to-organization roles. Unique by user, organization, and role.           |
| `student_profiles`         | Eligibility, age confirmation, biography, timezone, and workload capacity.    |
| `lead_profiles`            | Verified lead domains and workload capacity.                                  |
| `client_profiles`          | User-to-client-organization profile and verification state.                   |
| `client_verifications`     | Human-reviewed client verification evidence.                                  |
| `invitations`              | Expiring, revocable organization invitations. Only token hashes are stored.   |
| `skills`                   | Normalized skill catalog.                                                     |
| `student_skills`           | Student skill proficiency and evidence counts.                                |
| `availability_windows`     | Date-bounded student availability.                                            |
| `universities`             | Organization-backed university records.                                       |
| `institutional_agreements` | Versioned university terms and entitlements.                                  |
| `university_enrollments`   | University-to-student association with explicit consent.                      |
| `policy_versions`          | Versioned policy payloads and activation timestamps.                          |

Tenant isolation is enforced by FastAPI authorization-aware services using the active membership.
The browser never receives a database credential and never queries these tables directly.

## Public intake and privacy lifecycle

| Table                         | Purpose and principal relationships                                      |
| ----------------------------- | ------------------------------------------------------------------------ |
| `public_intake_submissions`   | Privacy-limited company lead intake, qualification, and retention state. |
| `public_intake_idempotencies` | Replay-safe request keys bound to normalized intake payload hashes.      |

## Learning and career readiness

| Table                         | Purpose and principal relationships                                          |
| ----------------------------- | ---------------------------------------------------------------------------- |
| `learning_paths`              | Published learning tracks, levels, prerequisites, hours, and skill outcomes. |
| `learning_modules`            | Ordered modules belonging to a learning path. Ordinals are unique per path.  |
| `learning_enrollments`        | A student's progress through a path. Unique per student and path.            |
| `learning_module_completions` | Evidence-backed module completion. Unique per enrollment and module.         |

Modules must be completed in sequence. Learning evidence is explicitly different from an
employer-verified credential.

## Internship learning and project execution

| Table                             | Purpose and principal relationships                                                |
| --------------------------------- | ---------------------------------------------------------------------------------- |
| `internship_programs`             | Version-policy, application-window, and completion-policy root.                    |
| `internship_tracks`               | Stable internship track identities.                                               |
| `internship_track_versions`       | Publishable track outcomes, prerequisites, workload, and learning-path bindings.   |
| `internship_cohorts`              | Capacity-, date-, and policy-bounded program cohorts.                              |
| `internship_cohort_tracks`        | Track versions offered within a cohort, including reviewer and instructor scope.   |
| `university_email_domains`        | Reviewed university-domain eligibility evidence.                                  |
| `allowed_student_emails`          | Cohort-specific invitation and eligibility exceptions.                            |
| `internship_applications`         | Versioned, consent-bound applications and human decisions.                        |
| `internship_cohort_enrollments`   | Student enrollment, progress, completion, and certificate eligibility state.      |
| `internship_phases`               | Ordered cohort-track execution phases.                                            |
| `internship_weeks`                | Date-bounded phase weeks and completion requirements.                             |
| `internship_units`                | Versioned learning units, release rules, resources, and exercises.                |
| `internship_unit_completions`     | Evidence-backed unit completion per enrollment.                                   |
| `internship_assignment_templates` | Versioned assignment scope, evidence requirements, rubric, and policy.            |
| `internship_cohort_assignments`   | Released assignment templates with cohort deadlines and reviewer pools.           |
| `internship_student_assignments`  | Per-student assignment state and the current-submission pointer.                  |
| `internship_uploads`              | Quarantined assignment artifact metadata and scan state.                          |
| `internship_submissions`          | Immutable submission attempts, artifact snapshots, hashes, and replay protection. |
| `internship_reviews`              | Human rubric decisions, conflicts, evidence, and idempotency state.               |
| `internship_certificates`         | Internship completion workflow state pending canonical credential integration.    |

Only one `DRAFT` submission may exist per student assignment; PostgreSQL and SQLite enforce that
invariant with the `uq_internship_submissions_one_active_draft` partial unique index. The
`internship_student_assignments.current_submission_id` foreign key is created after both assignment
and submission tables so metadata and migrations remain sortable without weakening referential
integrity.

## Employer opportunities and student proposals

| Table                   | Purpose and principal relationships                                                                                                                           |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `project_opportunities` | One published recruiting opportunity per client project, including the complete brief, skills, deliverables, effort, budget, deadline, and supervision level. |
| `student_proposals`     | Immutable student proposal terms, evidence, price, availability, employer decision, and idempotency records. Unique per student and opportunity.              |

A proposal cannot exceed the published budget or the student's remaining workload. Accepting one
proposal closes the opportunity and declines remaining proposals without reputation impact.
Selection does not authorize work: scope, contract, supervision, and funding guards still apply.

## Project lifecycle, scope, and approvals

| Table                    | Purpose and principal relationships                                       |
| ------------------------ | ------------------------------------------------------------------------- |
| `projects`               | Tenant-owned project aggregate with guarded state and optimistic version. |
| `project_scope_versions` | Versioned scope snapshots; accepted versions become immutable.            |
| `acceptance_criteria`    | Ordered, testable criteria belonging to a scope version.                  |
| `quotes`                 | Versioned quote snapshots tied to a project and scope.                    |
| `quote_line_items`       | Deterministic quote calculation details.                                  |
| `project_transitions`    | Append-only project state transitions and actor evidence.                 |
| `approvals`              | Human approval decisions and immutable decision snapshots.                |
| `audit_events`           | Append-only actor, tenant, resource, correlation, and payload evidence.   |

Project routes cannot write `projects.state` directly. The transition service owns state changes,
permissions, guards, row locking, version increments, audit records, and follow-up outbox events.

## Agents, staffing, offers, and planning

| Table                     | Purpose and principal relationships                                                         |
| ------------------------- | ------------------------------------------------------------------------------------------- |
| `prompt_versions`         | Versioned prompts and output contract metadata.                                             |
| `agent_runs`              | Provider, input/output snapshots, latency, retries, status, and stale-result evidence.      |
| `agent_run_events`        | Append-only run timeline.                                                                   |
| `staffing_runs`           | Reproducible matching execution for a project.                                              |
| `staffing_candidates`     | Ranked candidate evidence and eligibility result.                                           |
| `assignment_offers`       | Immutable student/lead offers with pay, hours, revisions, expiry, and decision idempotency. |
| `project_assignments`     | Accepted participant-to-project roles.                                                      |
| `plan_runs`               | Proposed project plan snapshot awaiting approval.                                           |
| `rate_cards`              | Versioned country-neutral pilot rates.                                                      |
| `matching_configurations` | Versioned matching filters and weights.                                                     |

AI runs only produce proposals. Deterministic services validate freshness and own all mutations.

## Delivery, evidence, QA, and scope control

| Table                   | Purpose and principal relationships                              |
| ----------------------- | ---------------------------------------------------------------- |
| `milestones`            | Approved project phases and due dates.                           |
| `tasks`                 | Assignment-aware delivery tasks and state.                       |
| `check_ins`             | Non-invasive structured progress check-ins.                      |
| `project_risks`         | Delivery risk, severity, ownership, and resolution state.        |
| `project_comments`      | Role-aware project communication records.                        |
| `work_logs`             | Participant work evidence and verified duration.                 |
| `deliverables`          | Project deliverable review state.                                |
| `deliverable_artifacts` | Immutable artifact versions and storage references.              |
| `qa_reviews`            | Deterministic and AI-assisted QA evidence for an exact artifact. |
| `qa_findings`           | Structured findings belonging to a QA review.                    |
| `lead_reviews`          | Compensated lead review recommendations and conflicts.           |
| `client_decisions`      | Client acceptance/revision decisions for released artifacts.     |
| `scope_change_requests` | Classification and evidence for requested scope changes.         |
| `change_orders`         | Accepted, compensated commercial changes.                        |

Artifacts are versioned, and review decisions bind to exact artifact and scope versions. New scope
cannot be silently added to an accepted project.

## Funding, ledger, payouts, and fairness

| Table                | Purpose and principal relationships                                    |
| -------------------- | ---------------------------------------------------------------------- |
| `invoices`           | Project funding requirements and externally verified settlement state. |
| `payment_events`     | Append-only external funding/refund evidence and replay protection.    |
| `ledger_entries`     | Append-only debit/credit entries in integer minor units.               |
| `payout_allocations` | Participant allocation snapshot for accepted work.                     |
| `payouts`            | Payout approval, execution evidence, failure, and reversal state.      |
| `appeals`            | Consequential decision appeal and resolution snapshot.                 |
| `appeal_evidence`    | Evidence attached to an appeal.                                        |
| `disputes`           | Project or financial dispute record.                                   |
| `reputation_events`  | Evidence-only, append-only reputation changes.                         |

PraxisAI currently records manually verified external funding and payout evidence. No Stripe or
other payment processor is integrated. Payout approval and execution are separate permissions.

## Consent, portfolio, and credentials

| Table                    | Purpose and principal relationships                                            |
| ------------------------ | ------------------------------------------------------------------------------ |
| `consent_records`        | Append-only consent version, purpose, and decision evidence.                   |
| `portfolio_permissions`  | Granular project contribution sharing permissions.                             |
| `credentials`            | Canonical signed credential payload, hash, signature, issuer, and public slug. |
| `credential_evidence`    | Accepted project evidence included in a credential.                            |
| `credential_revocations` | Append-only revocation history.                                                |

Public verification uses a privacy-redacted response schema. It does not expose an internal row
with fields removed at runtime.

## Operations, notifications, analytics, and reliability

| Table                       | Purpose and principal relationships                                          |
| --------------------------- | ---------------------------------------------------------------------------- |
| `feature_flags`             | Environment-aware feature configuration.                                     |
| `analytics_events`          | Privacy-safe product and operational events.                                 |
| `export_jobs`               | Purpose-limited, expiring data exports with idempotency.                     |
| `retention_configurations`  | Versioned retention rules.                                                   |
| `notifications`             | In-app delivery, read state, and provider synchronization evidence.          |
| `notification_preferences`  | User notification choices; mandatory fairness categories cannot be disabled. |
| `outbox_events`             | Transactional post-commit job queue with deduplication and retry state.      |
| `job_attempts`              | Append-only handler attempt evidence.                                        |
| `outbox_recoveries`         | Audited dead-letter recovery requests.                                       |
| `provider_synchronizations` | External provider health and synchronization state.                          |
| `rate_limit_buckets`        | Persistent cross-instance rate limiting.                                     |

## Principal relationship flow

```text
users -> organization_memberships -> organizations
  |                                  |
  +-> student_profiles               +-> projects -> project_opportunities
  |        |                                        |          |
  |        +-> learning_enrollments                 |          +-> student_proposals
  |        +-> student_skills                       |
  |        +-> student_proposals                    +-> scopes -> quotes
  |                                                 +-> assignments -> tasks/work logs
  |                                                 +-> deliverables -> artifacts -> QA
  |                                                 +-> invoices -> ledger -> payouts
  |                                                 +-> credentials/reputation/appeals
  +-> lead_profiles
  +-> client_profiles
```

## Applying the schema to Supabase

Set `DATABASE_URL`, `DATABASE_MIGRATION_URL`, and `DATABASE_POOL_MODE` as described in
`docs/supabase-setup.md`, then run:

```powershell
npm run db:migrate
npm run db:check
```

`db:migrate` applies the full chain from an empty PostgreSQL database. `db:check` compares the
database at the configured migration URL with current model metadata and fails if a model change is
missing an Alembic migration.

Do not create or edit production tables manually in the Supabase dashboard. Every schema change
must update the model, add an Alembic migration, regenerate OpenAPI when necessary, and pass the
schema drift check.
