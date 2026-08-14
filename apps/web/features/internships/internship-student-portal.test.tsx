import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { InternshipStudentPortal } from "./internship-student-portal";

describe("InternshipStudentPortal", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders an authoritative demo timeline from the dashboard response", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          enrollment_id: "enrollment-1",
          program_name:
            "InventaCore Technology Internship — Cohort 2 (Demo data)",
          cohort_name: "Cohort 2",
          track: {
            name: "AI Engineer",
            title: "AI Engineer v1",
            skill_outcomes: ["Evaluation"],
          },
          enrollment_status: "LEARNING",
          certificate_eligibility: "NOT_ELIGIBLE",
          completed_units: 2,
          required_units: 8,
          passed_assignments: 0,
          required_assignments: 2,
          progress_percent: 20,
          timeline: [
            { label: "Application", state: "COMPLETE" },
            { label: "Admission", state: "COMPLETE" },
            { label: "Foundations", state: "CURRENT" },
          ],
          is_demo: true,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={queryClient}>
        <InternshipStudentPortal view="dashboard" />
      </QueryClientProvider>,
    );
    expect(
      await screen.findByText(/InventaCore Technology Internship/),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Demo data · fictional records"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Make the next accountable step visible."),
    ).toBeInTheDocument();
  });

  it("creates the first application instead of leaving the student in a loading state", async () => {
    let created = false;
    const application = {
      id: "application-1",
      program_id: "program-1",
      cohort_id: "cohort-1",
      applicant_user_id: "student-1",
      status: "DRAFT",
      version: 1,
      primary_track_id: null,
      secondary_track_id: null,
      education_status: "",
      university_id: null,
      degree_program: "",
      semester_status: "",
      country: "",
      timezone: "UTC",
      weekly_availability_hours: null,
      technical_background: "",
      motivation: "",
      portfolio_url: null,
      github_url: null,
      linkedin_url: null,
      accessibility_requirements: null,
      submitted_at: null,
      decision_at: null,
      decision_reason: null,
      is_demo: false,
    };
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockImplementation(async (input, init) => {
        const url = String(input);
        if (url.endsWith("/internships/me/dashboard")) {
          return new Response(JSON.stringify({}), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        if (url.endsWith("/internships/me/applications")) {
          if (init?.method === "POST") {
            created = true;
            return new Response(JSON.stringify(application), {
              status: 201,
              headers: { "Content-Type": "application/json" },
            });
          }
          return new Response(
            JSON.stringify(
              created
                ? [
                    {
                      id: application.id,
                      program_id: application.program_id,
                      cohort_id: application.cohort_id,
                      status: application.status,
                      version: application.version,
                      submitted_at: null,
                      decision_at: null,
                      is_demo: false,
                    },
                  ]
                : [],
            ),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        if (url.endsWith("/internships/programs")) {
          return new Response(
            JSON.stringify([
              {
                id: "program-1",
                slug: "engineering-program",
                name: "Engineering Internship",
                public_description: "A supervised engineering internship.",
                status: "APPLICATIONS_OPEN",
                duration_weeks: 8,
                default_timezone: "UTC",
                is_demo: false,
              },
              {
                id: "program-closed",
                slug: "closed-program",
                name: "Closed Internship",
                public_description: "Applications have closed.",
                status: "CLOSED",
                duration_weeks: 8,
                default_timezone: "UTC",
                is_demo: false,
              },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        if (url.endsWith("/internships/programs/engineering-program")) {
          return new Response(
            JSON.stringify({
              id: "program-1",
              slug: "engineering-program",
              name: "Engineering Internship",
              public_description: "A supervised engineering internship.",
              status: "APPLICATIONS_OPEN",
              duration_weeks: 8,
              default_timezone: "UTC",
              is_demo: false,
              cohorts: [
                {
                  id: "cohort-1",
                  name: "September cohort",
                  slug: "september",
                  status: "APPLICATIONS_OPEN",
                  starts_at: "2026-09-01T00:00:00Z",
                  ends_at: "2026-10-31T00:00:00Z",
                  application_deadline: "2026-08-25T00:00:00Z",
                  capacity: 25,
                  timezone: "UTC",
                  is_demo: false,
                },
              ],
              tracks: [],
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        if (url.endsWith("/internships/me/applications/application-1")) {
          return new Response(JSON.stringify(application), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response(null, { status: 404 });
      });
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <InternshipStudentPortal view="application" />
      </QueryClientProvider>,
    );

    expect(
      await screen.findByRole("heading", {
        name: "Start an internship application.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Loading application..."),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("option", { name: "Closed Internship" }),
    ).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Program"), {
      target: { value: "program-1" },
    });
    await screen.findByRole("option", { name: "September cohort" });
    fireEvent.change(screen.getByLabelText("Cohort"), {
      target: { value: "cohort-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create application" }));

    await screen.findByRole("heading", {
      name: "Your application is governed by explicit review states.",
    });
    await waitFor(() => {
      const post = fetchMock.mock.calls.find(
        ([input, init]) =>
          String(input).endsWith("/internships/me/applications") &&
          init?.method === "POST",
      );
      expect(post).toBeDefined();
      expect(JSON.parse(String(post?.[1]?.body))).toEqual({
        program_id: "program-1",
        cohort_id: "cohort-1",
        consent_version: "internship-1",
      });
    });
  });
});
