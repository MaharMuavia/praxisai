# MVP assumptions and risks

- The pilot uses country-neutral USD demo policy. Taxes, rate cards, provider fees, regions, appeal windows, and cohort thresholds are versioned settings.
- Supabase Auth/Storage, Gemini, Google Cloud runtime/storage/scheduling, KMS, and the private ClamAV endpoint require operator-owned credentials and onboarding. No fallback claims provider work occurred.
- Payment processing is outside this build. Funding records are operator-approved evidence of external settlement and never initiate a transfer.
- Local artifact URLs represent external evidence; untrusted student code is not executed inside the API process.
- Labor classification, worker protections, tax, payment availability, credential wording, privacy terms, and retention require jurisdiction-specific legal review.
- This repository implements a working core lifecycle and route surface, but full production acceptance requires live-provider integration testing, complete role-specific interaction coverage, accessibility audit, and all specified end-to-end scenarios.
