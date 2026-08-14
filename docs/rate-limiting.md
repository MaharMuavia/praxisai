# Hosted rate-limiting boundary

PraxisAI treats database-backed limits as application abuse controls, not as the
network edge. Browser requests use the Next.js same-origin proxy, which removes
browser-supplied forwarding and service-authentication headers before calling the
private Cloud Run API with the web service identity. That identity authenticates
the proxy service; it does not cryptographically attest the visitor's IP address.

The API therefore never uses `request.client.host`, `Forwarded`,
`X-Forwarded-For`, `X-Real-IP`, or similar request headers as a quota identity.
The direct API peer is a Cloud Run intermediary, and the external load balancer
can preserve unverified caller-supplied values before its own appended addresses.
Inventing an unsigned proxy header would restore the spoofing vulnerability.

## Application policies

All identifiers below are SHA-256 fingerprinted before they enter the limiter,
and the complete bucket key is hashed again before database storage.

| Boundary | Partition | Limit | Ordering |
| --- | --- | --- | --- |
| Local/demo session creation | Membership-validated user UUID | 20/minute | A 300/minute global check runs before the membership lookup; this route is unavailable in hosted production. |
| Supabase session exchange | Presented token fingerprint, then global, then verified Supabase subject | 10/minute per token, 300/minute global, 10/minute per subject | The token and global checks protect the provider call. The subject check runs only after Supabase verification. |
| Scope, planning, and QA agents | Signed-session, database-validated user UUID | 10/minute per user and category | FastAPI resolves `Principal`/role dependencies first. Invalid project/resource state is rejected before QA quota is spent. |
| Deliverable submission | Signed-session, database-validated user UUID | 20/minute per user | Project access, role, and state are validated before quota is spent. |
| Public credential JSON and QR | Public credential slug fingerprint | 60/minute per resource plus 3,000/minute global | Resource partitioning prevents unrelated credentials sharing a browser/NAT quota; the global bucket bounds randomized-slug scanning. |
| Public intake | Normalized contact-email fingerprint | 3/24 hours per email plus 1,000/hour global | Idempotency is resolved first. The global bucket bounds randomized-email submissions. |

Authenticated project limits participate in the route's database transaction, so
the limiter does not commit and release a project row lock early. Successful and
recorded-failure agent runs commit their quota with the run; rejected authorization
or invalid resource-state requests roll it back.

## Required edge control

Production still requires a public load-balancer or Cloud Armor policy for
connection-IP throttling, bot management, and volumetric attacks against the web
service. Google documents that an external Application Load Balancer appends its
addresses to existing `X-Forwarded-For` content and does not verify preceding
values. Configure edge policy from the connection metadata available at that
boundary rather than parsing the first application header value. See
[Google Cloud's `X-Forwarded-For` contract](https://cloud.google.com/load-balancing/docs/https#x-forwarded-for_header).
