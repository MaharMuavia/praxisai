# PraxisAI — Final Submission Steps (do-this-now)

**Deadline:** 2026-08-17, 1:00 pm PDT. This is the single source of truth for finishing the
Build with Gemini XPRIZE submission. Items marked **[ONLY YOU]** cannot be done for you.

---

## Status of the 7 required items

| # | Requirement | Status | Owner |
|---|---|---|---|
| 1 | Repo shared with `testing@devpost.com` + `judging@hacker.fund` | ⚠️ Collaborators added, **but honest code NOT yet on public `main`** | **[ONLY YOU]** push (Step A) |
| 2 | 3-minute video (AI live in production, executing decisions) | Script ready | **[ONLY YOU]** record (Step B) |
| 3 | Written narrative (500–1000 words) | ✅ Done — `docs/xprize-submission-narrative.md` (~950 words, honest) | Paste into Devpost |
| 4 | Revenue evidence + simple P&L | ✅ Done — `docs/PraxisAI-PnL.xlsx` + statement below | Upload |
| 5 | Hackathon expenses in P&L (incl. marketing/CAC, even if $0) | ✅ Done — P&L discloses **$0** marketing/CAC | Upload |
| 6 | Product evidence (agent logs, API usage, dashboards) | Runbook ready | **[ONLY YOU]** capture (Step C) |
| 7 | Customer evidence (real customers / testimonials) | ✅ Honest disclosure — see below | Paste |

---

## Step A — Make the honest code public **[ONLY YOU] — CRITICAL, DO FIRST**

Right now your public `main` is still the OLD pre-audit commit with no LICENSE. The push is
blocked by branch protection. You must lift it in the GitHub UI (I cannot bypass a security
setting from git):

1. Open **https://github.com/MaharMuavia/praxisai/settings/branches**
   (if empty, try **Settings → Rules → Rulesets**).
2. On the rule protecting `main`, click **Edit** → uncheck **"Require a pull request before
   merging"** and **"Require status checks to pass before merging"** → **Save**. (Or just
   **Delete** the rule.)
3. Push:
   ```bash
   git push origin main
   ```
   Success looks like `d8e4156..febcb8f  main -> main`.
4. Confirm:
   ```bash
   git ls-remote origin refs/heads/main
   ```
   It must now show `febcb8f…`. Then re-enable the protection rule if you want.

**Fallback (keep protection on):** push `release/xprize-2026` (not protected), open a PR into
`main`, and use the admin **"Merge without waiting for requirements to be met"** button.

---

## Step B — Record the 3-minute video **[ONLY YOU]**

Follow `docs/xprize-video-script.md` verbatim (timed to 3:00). To satisfy "AI is live and
executing decisions" **without deploying**, show a real Gemini run captured in Step C on screen
(the `/ops/agent-runs` record with a real model id + token usage), not the illustrative `/judge`
page. Upload unlisted to YouTube/Vimeo and keep the link.

---

## Step C — Capture live product evidence **[ONLY YOU]**

**Config is already done and verified this session:** `GEMINI_PROVIDER=gemini`, the placeholder
`GOOGLE_CLOUD_PROJECT` was removed (it was hijacking the Vertex path), and your API key was
confirmed to make real Gemini calls. A backup of the old `.env` is at `.env.env.bak`.

> ⚠️ Note: `npm run eval:agents` is **fixture-only by design** (it hardcodes the fixture
> provider so it can never silently go live) — it does NOT produce real Gemini traffic. Use the
> script below instead.

1. **Run one real, live agent workflow** (drafts a real project scope via Gemini, prints token
   usage + audit metadata, and saves an evidence artifact):
   ```bash
   uv run --project apps/api python scripts/live_agent_demo.py
   ```
   This already produced `docs/evidence/live-scoping-run.json` — a genuine `gemini-2.5-flash`
   run: `is_demo: false`, ~3,800–4,200 tokens, schema-enforced `ScopeDraft` output, with
   correlation_id, input hash, and prompt version. **Screenshot this terminal output** — it is
   your strongest "AI is live and executing decisions" evidence, and it's what to run on camera.
2. *(Optional, needs local Postgres migrated)* Bring up the full app and view the recorded run
   in the UI:
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000/ops/agent-runs`, open the run, and screenshot the inspector.
3. In **https://aistudio.google.com** (or https://console.cloud.google.com), screenshot the
   **API usage** graph showing your request count — your third-party "API usage record."

Collect the terminal screenshot + `docs/evidence/live-scoping-run.json` + the usage graph as
your product evidence.

---

## Step D — Fill in the Devpost page — copy/paste blocks

- **Project name:** PraxisAI
- **Tagline:** AI-operated apprenticeship studio — real preparation, paid projects, verified careers
- **Category:** Education & Human Potential
- **Description / narrative:** paste `docs/xprize-submission-narrative.md`
- **GitHub:** https://github.com/MaharMuavia/praxisai
- **Video:** (your Step B link)
- **P&L / financials:** attach `docs/PraxisAI-PnL.xlsx`
- **Product evidence:** attach Step C screenshots
- **Corporate ID:** N/A — not yet incorporated (sole founder, pre-incorporation)

### Revenue evidence (paste as-is)

> PraxisAI is pre-revenue: **$0 revenue** for the competition window (May 19 – Aug 17, 2026).
> No payment processor is integrated (`PAYMENT_PROVIDER=manual_external`), so there is no Stripe
> dashboard or bank revenue to export. The attached P&L (`docs/PraxisAI-PnL.xlsx`) is the revenue
> evidence: $0 revenue against ≈$113 in estimated costs. Marketing & customer-acquisition spend
> during the hackathon period was **$0**.

### Customer evidence (paste as-is)

> PraxisAI has **no paying customers and no signed partners yet** — it is pre-revenue, pilot
> stage. We are not submitting fabricated customers or testimonials. Our target customers
> (universities/CS departments, regional workforce boards, non-profits/civic tech, and SMBs with
> internal-tooling gaps) and the commercial model are documented in `docs/pilot-pipeline.md`,
> which states plainly that zero organizations have been approached, signed, or committed.
> Commercial validation is our next milestone; the delivery, escrow, credentialing, and
> agent-supervision engineering that makes it possible is built and tested today.

> _If you have had any real early conversations, demo testers, or waitlist signups, add them
> here truthfully with their permission (name, email, phone, and what they said). Do not invent
> any._

---

## What's already prepared for you (in this repo)

- `docs/xprize-submission-narrative.md` — the 500–1000 word narrative (honest, complete)
- `docs/PraxisAI-PnL.xlsx` — simple P&L, formulas + required marketing/CAC disclosure
- `docs/xprize-pnl-statement.md` — the P&L written up in prose
- `docs/pilot-pipeline.md` — go-to-market + honest "zero customers" traction disclosure
- `docs/xprize-video-script.md` — the 3-minute script
- `docs/xprize-submission-checklist.md` — full checklist
