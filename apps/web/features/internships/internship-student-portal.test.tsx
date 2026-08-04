import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
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
});
