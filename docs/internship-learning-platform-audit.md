# Internship learning platform audit

Audit baseline: `agent/exceptional-judge-experience` at `dd25da1`, before the
internship feature branch changes.

## Capability review

| Capability | What exists | Reuse/change/separation | Security and integrity risk | User impact | Affected files | Required tests | Result |
|---|---|---|---|---|---|---|---|
| Identity and membership | `User`, `OrganizationMembership`, local sessions, Supabase access-token verification | Reuse identity and membership tables. Add a dedicated student-provisioning service; do not use the local session as signup authority. | Existing Supabase login rejects users without an account; email verification is checked in the provider but there is no signup path. | New students cannot apply without operator provisioning. | `app/auth/service.py`, `app/api/auth.py`, `domain/models.py` | verified/unverified token, duplicate email, enumeration-safe errors | Internship signup provisions the existing user/profile/membership boundary; the Supabase production flow remains provider-gated and requires real credentials. |
| Roles and capabilities | Role enum and capability map in auth routes | Reuse roles and extend capability map with `internships:*`. Keep capability checks in internship dependencies/services. | Role-name checks are currently centralized but not fine-grained for internship records. | Reviewers need cohort/assignment scoping. | `app/domain/enums.py`, `app/api/auth.py`, new internship routes | student/coordinator/reviewer/admin matrix, cross-student 404 | Added internship capability vocabulary and scoped checks in the new domain. |
| University identity | `University`, `UniversityEnrollment`, institutional agreements | Reuse `University`; add normalized approved email domains and invite-only allow-list entities. | `.edu` inference would accept unapproved institutions; no disposable-domain policy exists. | Legitimate students need a reviewable personal-email exception. | `domain/models.py`, new `internships/policies.py` | exact domain, allowed/disallowed subdomain, blocked/disposable, invitation expiry | Domain matching is explicit, IDNA-normalized, exact by default, and policy-driven. |
| Learning | `LearningPath`, `LearningModule`, enrollment, text evidence completion API | Preserve generic commercial/skill learning API. Internship content is linked through versioned track content and has structured requirements. | Existing completion accepts free text only and is not tied to a cohort/week policy. | Students need official internship deadlines and evidence. | `app/learning/*`, new internship curriculum service | ordered weeks, unlock, completion requirement, version stability | Dedicated internship curriculum entities provide authoritative progress without altering commercial learning behavior. |
| Projects and evidence | Commercial `Project`, `Deliverable`, artifact storage/evidence, credentials | Keep internship assignments separate from `Project`; share only audit/hash/evidence conventions. | Reusing commercial project state would mix paid-work and learning policy. | Internship review can remain non-commercial and privacy-safe. | `domain/models.py`, `app/operations/artifacts.py`, credentials | separation, immutable artifacts, hash, privacy | Internship assignment/submission tables are separate; evidence source is labelled `internship_learning` or `internship_project`. |
| Storage/uploads | Existing artifact boundary and configured cloud-storage setting | Add an internship upload lifecycle with local/demo and Supabase Storage providers. | A normal JSON upload would bypass size/hash/quarantine controls. | Students need incremental private uploads. | `app/operations/artifacts.py`, new internship submission service | owner binding, size/type/hash, expiry, cross-student isolation | Upload metadata and submission hashes are server-owned; production bytes use a private Supabase bucket when configured. |
| Credentials | Signed commercial credentials and public verification | Add internship certificate eligibility/approval records; do not force an internship into a commercial project credential. | Credential issuance must remain human controlled and public payload privacy-safe. | Students see deterministic eligibility, not an automatic certificate. | `app/credentials/*`, `domain/models.py`, new internship credentials service | eligibility, one issuance, revocation, public privacy | Internship certificate records have explicit approval and revocation states. |
| Audit/notifications/outbox | Append-only `AuditEvent`, notifications, outbox worker | Reuse audit/outbox primitives; emit minimal internship events. | Raw application text or artifact contents must not enter logs. | Staff can explain transitions without exposing private content. | `domain/models.py`, `app/outbox/*`, new internship services | event action/resource/payload minimization | Domain services emit transition audits; notifications are optional follow-up work. |
| Frontend/student routes | Shared app shell and generic student career workspace | Keep the generic workspace intact. Add route-owned internship feature pages and queries. | Putting internship state in the shared shell would leak commercial opportunities and make authorization unclear. | Students get a distinct operating-system workflow. | `apps/web/app`, `features/internships`, `lib/queries/internships` | loading/error/permission/mobile/reduced motion | Added dedicated public and student internship surfaces; generic student workspace remains unchanged. |
| Operations | Operations workspace pages and role routes | Reuse shell/session and add internship operations endpoints/UI. | Every student record must be cohort/assignment scoped. | Coordinators can review admissions and workload. | `app/api/operations.py`, new internship operations route/UI | access matrix, pagination, stale updates | Core admission/progress/review operations endpoints are separated from commercial operations. |
| Demo and verification | Deterministic seed, demo fallback, judge walkthrough/evidence pages | Extend demo seed with Amina’s internship scenario; label every fictional record. | Demo data can be mistaken for live partner or credential evidence. | Judge can follow a realistic path without paid providers. | `scripts/seed_demo.py`, `apps/web/lib/demo-data.ts`, new docs/UI | demo labels, locked project, draft/review sample | Demo fixtures are labelled and intentionally non-credentialed. |

## Implementation boundary

This branch implements the reusable domain foundation and a complete admissions,
curriculum, assignment, submission-draft, review, and certificate-eligibility
vertical slice. Production Supabase account provisioning, malware scanning,
Supabase connectivity, transactional email, and external PR automation remain
deployment/provider integrations and are reported as unverified unless exercised
with real credentials.

## Integrity rules preserved

- Internship assignments never reference commercial client projects.
- Submitted application and submission versions are immutable by service policy.
- Server responses, not browser calculations, determine status and progress.
- AI providers are not given admission, review, completion, or certificate authority.
- Existing commercial project, credential, demo, judge, and marketing routes are unchanged.
