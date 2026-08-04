# Internship data and retention

Internship data is purpose-limited to admissions, learning delivery, review,
support, and certificate verification. The system must not copy private
application answers or uploaded artifact contents into generic logs.

## Access

- Students can read only their own application, enrollment, assignments,
  submissions, feedback, and certificate records.
- Reviewers can read only assignments explicitly assigned to them or to their
  scoped reviewer pool.
- Coordinators and platform administrators can operate cohort records subject
  to the internship capabilities and audit trail.
- Accessibility requirements are restricted to authorized operations staff.
- Public verification contains only privacy-safe certificate payload fields.

## Retention defaults

| Record | Default retention | Disposal behavior |
|---|---:|---|
| Abandoned upload metadata | 24 hours after expiry | Delete private object and mark upload `EXPIRED`. |
| Rejected/withdrawn applications | 12 months after decision/withdrawal | Anonymize application text and retain only legally necessary audit facts. |
| Accepted learning records | 3 years after cohort completion | Retain completion evidence summary; remove unnecessary personal context. |
| Submission artifacts | 3 years after cohort completion | Remove private objects unless an explicit portfolio consent or certificate evidence requires a derived reference. |
| Reviewer notes | 3 years after final decision | Keep student-visible feedback separate from private notes; anonymize on approved deletion request. |
| Certificates and public verification payloads | Certificate lifetime plus 7 years | Revocation remains append-only; public payload excludes email, university-private data, and private artifacts. |
| Audit events | 7 years or the applicable legal minimum | Keep action/resource/correlation facts only; never raw submissions or full feedback. |

These are documented defaults, not legal advice. Operators must configure a
jurisdiction-specific retention schedule before production use.

## Deletion and export

Deletion or export requests require authenticated identity, authorization, a
correlation id, and an audit event. Certificate and security/audit evidence may
be retained where required by law or explicitly disclosed policy. Signed access
URLs are private and short-lived; storage bucket paths are never exposed.

## Provider boundary

Local/demo environments use database metadata and local/temporary storage.
Production requires a private object store, malware scanning/quarantine
adapter, lifecycle deletion policy, and an email provider. None of those
provider capabilities are treated as verified by local tests alone.
