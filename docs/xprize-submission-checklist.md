# XPRIZE Build with Gemini — Devpost Submission Checklist

**Deadline:** August 17, 2026  
**Category:** Education & Human Potential  
**Target prize tier:** 3rd–5th place ($100,000 each) or Category Prize ($50,000)

---

## Required Submission Artifacts

### 1. Source Code Repository
- [x] GitHub repository exists
- [x] MIT LICENSE file added
- [ ] Share access with `testing@devpost.com` (add as collaborator)
- [ ] Share access with `judging@hacker.fund` (add as collaborator)
- [ ] Repository is clean (no uncommitted changes, CI green)

### 2. 3-Minute Video Pitch
- [ ] Record technical walkthrough showing AI agents in action
- [ ] Show product functioning in web browser
- [ ] Demonstrate live Gemini API calls (not fixture mode)
- [ ] Keep under 3 minutes (judges won't watch beyond)
- [ ] Upload to YouTube/Vimeo (unlisted) or attach directly
- [ ] See `docs/xprize-video-script.md` for the script

> **To show LIVE Gemini calls without deploying:** run locally with a real key —
> set `GEMINI_PROVIDER=gemini` and `GEMINI_API_KEY=<key>` (or `GOOGLE_CLOUD_PROJECT`
> for Vertex AI) in `.env`, restart the API, and drive a real scoping or multimodal
> QA action. The `agent_runs` record will show a real model id and non-zero token
> usage (not `fixture`). This satisfies the "AI live" requirement for the video
> even before full Cloud Run deployment.

### 3. Written Narrative (500–1000 words)
- [ ] Case study explaining daily operational workflows
- [ ] Human vs. AI task division
- [ ] Economic opportunities created
- [ ] See `docs/xprize-submission-narrative.md` for the draft

### 4. Financial Documentation
- [ ] P&L statement (see `docs/xprize-pnl-statement.md`)
- [ ] Revenue evidence (Stripe dashboard, bank statements, or invoices)
- [ ] Note: Even $0 revenue must be documented honestly

---

## Technical Requirements

### Google Cloud Integration (mandatory)
- [ ] Gemini API / Vertex AI actively used in production
- [ ] At least one core Google Cloud product integrated
- [ ] Evidence of AI agents executing key business decisions

### Deployment
- [ ] Product deployed and accessible via public URL
- [ ] Supabase database migrated to current Alembic head
- [ ] Gemini provider set to `gemini` (not `fixture`)
- [ ] All environment variables configured for production/staging

---

## Pre-Submission Verification

```powershell
# Run from project root
npm run format
npm run lint
npm run typecheck
npm test              # 230 pass locally (74 web + 156 API)
npm run build
npm run db:migrate    # applies new migration d5e6f7a8b9c0 (outbox correlation_id NOT NULL)
npm run db:check      # must pass after the migration above
npm run test:e2e -- --update-snapshots   # refresh stale visual baselines (run on the CI OS), then commit the PNGs
npm run eval:agents
npm audit --audit-level=high
```

**Known CI status (2026-08-16):** local tests pass; CI needs the migration above
applied and visual baselines refreshed. Terraform validate/fmt verified green.

---

## Devpost Page Content

- [ ] Project name: PraxisAI
- [ ] Tagline: AI-operated apprenticeship studio — real preparation, paid projects, verified careers
- [ ] Category: Education & Human Potential
- [ ] Description: (use submission narrative)
- [ ] Screenshots: Homepage, judge walkthrough, workspace, evidence page
- [ ] Video: (link to 3-min pitch)
- [ ] GitHub link: (repository URL)
- [ ] Live demo URL: (deployed URL)
- [ ] Team members listed

---

## After Submission

- [ ] Verify submission is complete on Devpost
- [ ] Confirm video plays correctly
- [ ] Confirm repository access works for judge emails
- [ ] Save confirmation/receipt
