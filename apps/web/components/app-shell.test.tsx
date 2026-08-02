import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AppShell } from "./app-shell";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AppShell university workspace", () => {
  it("uses privacy-safe university endpoints and renders cohort suppression", async () => {
    const requestedUrls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = input.toString();
        requestedUrls.push(url);
        if (url.endsWith("/auth/me")) {
          return Response.json({
            user_id: "11111111-1111-1111-1111-111111111111",
            display_name: "University Viewer",
            email: "viewer@example.test",
            active_membership: {
              organization_id: "22222222-2222-2222-2222-222222222222",
              organization_name: "Fictional University",
              role: "university_viewer",
            },
            capabilities: [],
            onboarding_state: "COMPLETE",
            notification_count: 0,
            environment_label: "demo",
            required_consent_versions: {},
          });
        }
        if (url.endsWith("/university/metrics")) {
          return Response.json({
            suppressed: true,
            minimum_cohort_size: 5,
            consented_cohort_size: null,
            participating_students: null,
            completed_projects: null,
            credentials_issued: null,
            verified_work_minutes: null,
            as_of: "2026-07-30T00:00:00Z",
          });
        }
        if (url.endsWith("/university/exports")) return Response.json([]);
        if (url.endsWith("/notifications")) {
          return Response.json([
            {
              id: "33333333-3333-3333-3333-333333333333",
              kind: "operations",
              title: "Cohort report available",
              body: "Privacy-safe metrics are ready.",
              resource_path: "/university",
              read_at: null,
              created_at: "2026-07-30T00:00:00Z",
            },
          ]);
        }
        if (url.endsWith("/notifications/preferences")) {
          return Response.json([
            { category: "projects", enabled: true },
            { category: "payments", enabled: true },
          ]);
        }
        return Response.json({}, { status: 404 });
      }),
    );

    render(
      <AppShell
        path="/university"
        title="Outcomes"
        description="Privacy-safe outcomes"
      />,
    );

    expect(
      await screen.findByText(/Aggregate outcomes are suppressed/i),
    ).toBeInTheDocument();
    await waitFor(() => expect(requestedUrls).toHaveLength(5));
    expect(requestedUrls.some((url) => url.endsWith("/projects"))).toBe(false);
    const notificationButton = screen.getByRole("button", {
      name: "1 unread notifications",
    });
    fireEvent.click(notificationButton);
    expect(screen.getByText("Cohort report available")).toBeInTheDocument();
  });
});
