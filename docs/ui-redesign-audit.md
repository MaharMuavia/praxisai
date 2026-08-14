# PraxisAI UI redesign audit

Date: 2026-08-02

Scope: frontend audit before Phase 1 (foundation) and Phase 2 (public marketing). This document describes the repository as inspected on the current working tree; it does not claim that authenticated application refactors are complete.

## Current route map

The Next.js App Router currently contains:

- `/`: `LandingPage`.
- `/login`: branded local/demo login surface.
- `/verify/[...slug]`: public credential verification surface.
- `/[...slug]`: one catch-all for public content, account/onboarding placeholders, and all role workspaces.
- `/api/v1/[...path]`: same-origin API proxy.

The catch-all recognizes public paths such as `/pricing`, `/trust`, `/privacy`, and `/how-it-works/clients`, and role roots `/client`, `/student`, `/lead`, `/ops`, `/admin`, and `/university`. Major authenticated pages are selected by `path` inside `AppShell`, not by explicit route-level page modules.

## Component map

| Area | Current implementation | Finding |
| --- | --- | --- |
| Public header | `components/marketing-nav.tsx`, `components/brand.tsx` | Small and reusable, but desktop-only information architecture; no mobile menu, footer, or role-specific CTA hierarchy. |
| Public home | `components/landing-page.tsx` | Interactive client component with a useful learning-to-delivery story, but contains invented sample metrics and a demo badge in the primary marketing flow. |
| Public content | `components/content-page.tsx` plus the catch-all config | Truthful points and legal review labels exist, but pages are too generic for the requested company platform. |
| Authenticated shell | `components/app-shell.tsx` | 1,000+ lines; fetches session, notifications, projects, operations, university, billing, credentials, offers, and project workspace data from one effect. It also owns navigation, mutations, toasts, and rendering decisions. |
| Student workspace | `components/student-career-workspace.tsx` | Domain-specific UI exists and is demo-aware, but is mounted through `AppShell` and lacks route-level query boundaries. |
| Employer workspace | `components/employer-talent-workspace.tsx`, `components/client-project-intake.tsx` | Real API-connected slices exist for proposal review, opportunity publishing, and intake. |
| Project workspace | `components/project-command-center.tsx` | Real project/work-management surface exists; it is selected from the catch-all. |
| Shared states | `components/states.tsx`, `status-badge.tsx`, `money-amount.tsx` | Useful seeds, but state primitives need accessible loading, permission, retry, stale, and environment variants. |

## Data-fetching map

The browser API helper is centralized in `lib/api.ts` and generated types are imported from `@praxisai/api-client`. `AppShell` calls `praxisFetch` directly from a single `useEffect` and uses `withDemoFallback` for several reads. The current reads include:

- Auth: `/auth/me`.
- Notifications: `/notifications`, `/notifications/preferences`.
- Projects: `/projects` and `/projects/{id}/workspace`.
- Operations/admin: `/ops/dashboard`, `/ops/jobs`, `/ops/integrations`.
- University: `/university/metrics`, `/university/exports`.
- Client: `/client/invoices`.
- Student/participant: `/students/me/credentials`, `/participants/me/earnings`, `/assignment-offers`.
- Lead/operations queues: `/leads/me/review-queue`, `/ops/approval-queue`, `/ops/risk-queue`.
- Marketplace: the dedicated student/employer components use talent and learning endpoints.

React Query is installed but is not the dominant pattern in the shell. Stable query keys, route-scoped invalidation, cancellation, and typed error classification are therefore not yet consistently implemented. The public site has no API-backed conversion form; public CTAs must remain informational or route to existing authenticated workflows.

## Role and capability map

The API exposes session memberships and capabilities. The frontend currently maps URL prefixes to six workspace roots and renders navigation for client, student, lead, operations, admin, and university roles. Authorization is enforced by the API, but the shell does not yet provide a first-class capability-driven navigation model or a reusable permission-denied state. University endpoints correctly suppress privacy-sensitive cohorts in the existing test coverage.

## Current design tokens and responsive behavior

`globals.css` contains the visual system as hand-authored CSS variables and approximately 2,700 lines of selectors. Existing colors are deep navy, warm paper, cyan, lime, and semantic colors. The current look is bold and dark-led, with rounded cards and oversized display type. It does not yet expose the requested complete token categories for surfaces, AI accent, focus, radii, shadows, layout widths, motion, or reduced motion.

Responsive rules exist at 900px, 720px, and 520px. The authenticated sidebar becomes a fixed drawer below 900px. Marketing navigation currently does not collapse into an accessible mobile menu, and the home hero/workflow grid needs deliberate behavior at 320px and 375px. No evidence of a formal 200% zoom or high-contrast audit was found in the current frontend tests.

## Accessibility issues found

- No skip link or explicit main/landmark strategy in the shared marketing shell.
- Marketing navigation has no mobile menu and no menu state announcements.
- The homepage uses buttons for stage selection but has no tablist/tabpanel semantics or visible selected styling contract.
- Interactive controls and forms rely on global CSS rather than shared labeled primitives.
- `ErrorState` accepts a retry callback but does not expose correlation IDs, support links, or a standardized heading.
- There is no shared dialog/drawer primitive with focus management.
- Loading, stale, permission-denied, offline, and environment states are not consistently represented.
- Automated tests cover selected workspace behavior but do not cover keyboard navigation, mobile navigation, or marketing form/CTA accessibility.

## Duplicated UI patterns and hard-coded metrics

Buttons, badges, page headings, banners, cards, and error blocks are repeated across components and styles. `AppShell` also repeats API loading and mutation handling by route. `landing-page.tsx` currently displays `126`, `84`, `91%`, and `0` as fictional/sample metrics; these are not acceptable as public company claims even though their labels mention fictional/sample data. The demo snapshot contains intentional fixture records and trends, and must remain behind explicit demo-mode detection.

## Demo-only behavior

`lib/api.ts` limits demo fallback to test or explicit demo mode. `lib/demo-data.ts` contains clearly identifiable fixture records and `AppShell` labels demo fallback in the workspace. Production must continue to fail visibly when required APIs are unavailable. Marketing content should use no traction, customer, revenue, outcome, payment, or AI-performance claims.

## Large responsibilities

- `AppShell` is the main refactor target: layout, navigation, session loading, notifications, data reads, mutations, demo state, route selection, and feature rendering should be separated.
- `globals.css` mixes tokens, marketing styles, workspace styles, feature styles, responsive behavior, and animation rules.
- `landing-page.tsx` combines home page content, workflow interaction, and presentation logic; the home content can be split into focused sections while keeping only the workflow selector client-side.
- The catch-all route combines content-page selection, workspace metadata, account placeholders, and not-found behavior.

## Backend support classification

| Planned surface | Classification | Current support |
| --- | --- | --- |
| Home, how it works, role explainers, solutions, trust, impact, about, accessibility | Static truthful marketing content | Safe to implement without invented claims. |
| Pricing | Static/partial | Existing pricing language is truthful; live quote calculation exists only in authenticated project flows. |
| Student application start, expert lead interest, university inquiry, general contact | Blocked by missing public intake endpoints | Do not simulate submission; provide truthful information and a supported contact/identity route. |
| Company project submission | Partially supported | Authenticated client intake and project APIs exist; public pre-auth submission does not. |
| Login and local/demo session | Partially supported | Existing login and API session flow exist; Supabase and production auth paths need explicit error-state coverage. |
| Credential verification | Fully supported | Public verification and QR/PDF endpoints exist. |
| Student learning, opportunities, proposals, offers, earnings, credentials | Partially supported | Multiple typed API endpoints exist; route-level query modules are still needed. |
| Client proposals, projects, invoices | Partially supported | Existing client components and API routes cover slices of these workflows. |
| Lead reviews, operations queues, agent runs, audit | Partially supported | API endpoints exist; current shell presentation is broad and needs dedicated route architecture. |
| Admin access, integrations, jobs | Partially supported | Integration and job reads exist; broader configuration surfaces lack equivalent frontend/API coverage. |
| University reporting and exports | Partially supported | Privacy-safe metrics and exports exist and are tested. |
| Full XPRIZE evidence center | Blocked/partial | Some operational evidence APIs exist, but the requested metric definitions, export links, and longitudinal evidence view are not one complete API surface. |

## Exact implementation sequence

1. Add the audit and preserve the current API/client boundaries.
2. Establish a compact token layer, accessible shared primitives, and a responsive marketing shell with footer and mobile navigation.
3. Rebuild the homepage around the truthful positioning: preparation, assessment, matching, supervised delivery, verification, and pay. Remove public traction/sample metrics.
4. Expand the shared public content template into explicit, truthful marketing page configurations for all required Phase 2 paths, including legal review notices where applicable.
5. Add tests for the marketing shell, homepage CTA destinations, no-traction-claim constraint, mobile menu keyboard behavior, and shared states.
6. In Phase 3, split `AppShell`, introduce route-scoped React Query modules, and replace major authenticated catch-all pages with explicit route files.
7. In later phases, connect supported role workflows, then document backend-blocked conversion forms and remaining unverified behavior.

## Phase 1/2 acceptance boundary

This pass can truthfully claim a public marketing foundation and public content surface. It cannot claim that the authenticated workspaces have been fully decomposed, that blocked public forms submit, or that all requested role dashboards and end-to-end flows are complete.
