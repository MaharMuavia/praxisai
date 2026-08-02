# Demo walkthrough

All names, projects, payments, agent output, and metrics in this walkthrough are **Demo data**.

1. Start PostgreSQL, apply migrations, run the deterministic seed command, then run `npm run worker:once`.
2. Open `/login` and choose Amina Noor. Use **Learn** to inspect the sequenced frontend-delivery curriculum, exercises, and recorded practice evidence.
3. Open **Paid projects** to compare complete employer briefs, then inspect the proposal builder and its approach, milestone, evidence, availability, timing, and fixed-price fields.
4. Switch to Maya Chen. Open **Student proposals** to compare Amina's submission and see the required, audited accept/reject reason. Do not accept it if you want to preserve the seeded state.
5. Use **Publish opportunity** to inspect the employer brief and commercial-term requirements; publishing is optional during a standard demo.
6. Switch to Sara Malik to review the operational project queue and stored agent evidence.
7. Switch to Leo Martins to inspect a downstream assignment offer containing fixed pay, hours, deadline, revision, and no-penalty decline terms.
8. Switch back to Amina Noor to inspect the active project record, supervised delivery path, earnings boundary, and consent controls.
9. Use `/verify` with an issued demo credential slug to check its signature and privacy-safe payload.
10. Switch to the Westbridge University viewer to inspect consent-safe aggregate outcomes; revoke one demo enrollment consent to see threshold suppression.
11. Use the operations job queue to inspect append-only retry evidence and recover a dead-letter job with a reason and idempotency key.
12. Open the notification bell and a workspace settings route to inspect delivered events and category controls. Payment, credential, and appeal notices remain mandatory.

The shortest API proof is: create project → transition to scoping → run fixture scoping → create deterministic quote → record approved demo funding → create and accept offers → activate → submit evidence → release/accept → approve payout → issue credential.
