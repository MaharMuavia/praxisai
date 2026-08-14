# Public intake privacy operations

Public intake records are collected only for the pathway selected by the
visitor. The API stores contact details separately from the role-specific
payload, records the consent purpose and version, and assigns a 180-day
retention deadline at creation. Rejected submissions are shortened to a
30-day deadline when the rejection is recorded.

Operations coordinators can anonymize a record through the protected
`POST /api/v1/ops/intake/{submission_id}/anonymize` endpoint. The operation
sets contact data to null, clears source, campaign, owner, review notes, and
conversion evidence, replaces the payload and consent snapshot with redacted
markers, and writes an audit event containing no submitted content. An
anonymized or deleted record is terminal and cannot re-enter review. Operators
can record a withdrawal request through
`POST /api/v1/ops/intake/{submission_id}/withdraw`; terminal deletion uses the
protected delete endpoint and retains only the audit tombstone.

The retention worker creates and processes a `RetentionSweepRequested` outbox
job through `scripts/run_worker.py`. The existing outbox retry policy provides
bounded attempts, backoff, and dead-letter status. The sweep uses a bounded
row lock batch, so repeated worker runs are safe.

Public intake does not trust `Forwarded`, `X-Forwarded-For`, `X-Real-IP`, or the
API socket peer as a browser identity. The hosted request reaches the API through
the same-origin Next.js service and Cloud Run, so the API peer identifies an
intermediary rather than the original visitor. New submissions are limited by a
privacy-safe hash of the normalized contact email (3 per 24 hours) and a shared
high-capacity safeguard (1,000 per hour). Idempotent replay is resolved before
these limits and does not spend another quota slot. Bucket keys are hashed before
storage.

This application-layer policy is not a volumetric DDoS control. Production must
enforce client-address, bot, and request-volume policy at the public load balancer
or Cloud Armor boundary, where the connection address is available. Google warns
that values preceding the load balancer-appended addresses in
`X-Forwarded-For` are not verified; the API therefore does not parse that header.
See the [Google Cloud load-balancer header contract](https://cloud.google.com/load-balancing/docs/https#x-forwarded-for_header).

Operators must not expose anonymization, withdrawal, or deletion endpoints
outside the operations capability boundary.
