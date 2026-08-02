# Premium UI upgrade plan

## Intent

Make PraxisAI feel like one coherent, operational technology company across the public site and authenticated workspaces while preserving the existing teal identity, truthful claims, API contracts, demo isolation, and accessibility protections.

## Current constraints

- The public site is statically rendered except for the interactive workflow and navigation.
- Public contact pages do not have a production lead endpoint, so they must continue to explain the supported authenticated next step rather than claim a submission.
- Workspace data is loaded through the existing `praxisFetch` and demo fallback boundary. This upgrade will not move business decisions into UI components or invent metrics.
- No real customer logos, testimonials, or outcome numbers are available; credibility content will use product principles and evidence states.

## Delivery slices

1. **Foundation and navigation**
   - Add reusable motion-safe primitives and shared operational UI primitives.
   - Add a sticky marketing header with structured menus, keyboard behavior, focus restoration, and mobile scroll locking.
   - Add shared workspace layout pieces for sidebar, header, breadcrumbs, environment status, notifications, and user menu.

2. **Public experience**
   - Keep the current homepage claims, but split interactive sections into focused client components.
   - Add the operating-system visualization, product previews, governance matrix, evidence chain, role pathways, and an honest case-study framework.
   - Give important content pages a page-specific visual treatment and CTA instead of one interchangeable body.

3. **Authenticated experience**
   - Use the extracted workspace pieces in `AppShell` without changing API loading or authorization behavior.
   - Improve hierarchy, next-action visibility, demo labeling, responsive navigation, and motion-safe state transitions.

4. **Verification**
   - Add tests for dropdowns, mobile navigation, workflow keyboard controls, product preview tabs, reduced motion, and narrow layouts.
   - Run format, lint, typecheck, unit tests, build, and Playwright. Lighthouse scores will only be reported if measured.

## Deferred or backend-blocked

- Public lead forms remain blocked until a real unauthenticated lead-intake endpoint, spam/rate-limit policy, and server confirmation contract exist.
- Real case studies, customer logos, testimonials, traction metrics, and impact numbers remain intentionally absent until approved evidence exists.
- Route-scoped data loaders and query hooks require a larger data-fetching refactor; this slice extracts the visible shell responsibilities without changing request behavior.
