# Public intake privacy operations

Public intake records are collected only for the pathway selected by the
visitor. The API stores contact details separately from the role-specific
payload, records the consent purpose and version, and assigns a 180-day
retention deadline at creation. Rejected submissions are shortened to a
30-day deadline when the rejection is recorded.

Operations coordinators can anonymize a record through the protected
`POST /api/v1/ops/intake/{submission_id}/anonymize` endpoint. The operation
replaces the email, payload, and consent snapshot with redacted markers and
writes an audit event containing no submitted content. The same operation is
available to the retention worker through
`anonymize_expired_submissions`, which is intended to run daily.

Only proxy addresses explicitly listed in `TRUSTED_PROXY_IPS` may supply the
first `X-Forwarded-For` address for public-intake rate limiting. All other
requests use the direct peer address. Bucket keys are hashed before storage.

Production operators must configure `TRUSTED_PROXY_IPS` to the fixed ingress
proxy addresses and must not expose the anonymization endpoint outside the
operations capability boundary.
