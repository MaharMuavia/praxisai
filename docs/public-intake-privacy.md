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

Only proxy addresses explicitly listed in `TRUSTED_PROXY_IPS` may supply the
first `X-Forwarded-For` address for public-intake rate limiting. All other
requests use the direct peer address. Bucket keys are hashed before storage.

Production operators must configure `TRUSTED_PROXY_IPS` to the fixed ingress
proxy addresses and must not expose anonymization, withdrawal, or deletion
endpoints outside the operations capability boundary.
