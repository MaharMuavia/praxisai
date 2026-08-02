import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { StudentCareerWorkspace } from "./student-career-workspace";

const opportunity = {
  id: "11111111-1111-1111-1111-111111111111",
  project_id: "22222222-2222-2222-2222-222222222222",
  employer_name: "Northstar Community Labs",
  headline: "Build an accessible community resource finder",
  brief:
    "Community members need a responsive way to find verified local services by category and location.",
  required_skills: ["TypeScript", "Accessibility"],
  nice_to_have_skills: ["User research"],
  deliverables: ["Responsive resource finder", "Verification report"],
  proposal_requirements: ["Delivery approach", "Relevant work evidence"],
  estimated_hours_low: 24,
  estimated_hours_high: 36,
  budget_minor: 120000,
  currency: "USD",
  deadline: "2026-10-30T00:00:00Z",
  supervision_level: "guided",
  status: "OPEN",
  proposal_count: 2,
  my_proposal: null,
  created_at: "2026-07-31T00:00:00Z",
};

function responseFor(url: string, init?: RequestInit) {
  if (url.endsWith("/learning/paths")) return Response.json([]);
  if (url.endsWith("/talent/opportunities"))
    return Response.json([opportunity]);
  if (url.endsWith("/talent/students/me/proposals")) return Response.json([]);
  if (url.includes("/proposals") && init?.method === "POST") {
    return Response.json(
      {
        id: "33333333-3333-3333-3333-333333333333",
        opportunity_id: opportunity.id,
        student_user_id: "44444444-4444-4444-4444-444444444444",
        student_display_name: "Amina Yusuf",
        cover_note:
          "I have delivered comparable accessible workflows with verified evidence.",
        approach:
          "I will clarify requirements, build the workflow, test keyboard behavior, and prepare review evidence for every milestone.",
        delivery_plan: [
          {
            milestone: "Validated workflow",
            outcome: "A reviewed implementation with acceptance-test evidence.",
          },
        ],
        relevant_evidence: [
          {
            title: "Accessible directory",
            url: "https://example.test/work",
            relevance: "Demonstrates comparable accessible interface delivery.",
          },
        ],
        proposed_amount_minor: 95000,
        currency: "USD",
        estimated_days: 10,
        availability_hours_per_week: 12,
        state: "SUBMITTED",
        decision_reason: null,
        decided_at: null,
        created_at: "2026-07-31T00:00:00Z",
      },
      { status: 201 },
    );
  }
  return Response.json({ detail: "Unexpected request" }, { status: 500 });
}

afterEach(cleanup);

describe("StudentCareerWorkspace", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows a complete employer brief and submits immutable proposal terms", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) =>
      Promise.resolve(responseFor(String(input), init)),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<StudentCareerWorkspace page="opportunities" />);

    expect(
      await screen.findByRole("heading", {
        name: "Build an accessible community resource finder",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Responsive resource finder")).toBeInTheDocument();
    expect(screen.getByText("Relevant work evidence")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Build proposal/i }));

    fireEvent.change(screen.getByLabelText("Why you are a strong fit"), {
      target: {
        value:
          "I have delivered comparable accessible workflows and can show relevant evidence.",
      },
    });
    fireEvent.change(
      screen.getByLabelText("Your technical and delivery approach"),
      {
        target: {
          value:
            "I will clarify the criteria, build the smallest complete workflow, test keyboard behavior, and prepare review evidence for every milestone.",
        },
      },
    );
    fireEvent.change(screen.getByLabelText(/Milestone plan/i), {
      target: {
        value:
          "Validated workflow | A reviewed implementation with acceptance-test evidence",
      },
    });
    fireEvent.change(screen.getByLabelText(/Fixed proposal/i), {
      target: { value: "950" },
    });
    fireEvent.change(screen.getByLabelText("Estimated calendar days"), {
      target: { value: "10" },
    });
    fireEvent.change(screen.getByLabelText("Available hours/week"), {
      target: { value: "12" },
    });
    fireEvent.change(screen.getByLabelText("Work sample title"), {
      target: { value: "Accessible directory" },
    });
    fireEvent.change(screen.getByLabelText("HTTPS evidence URL"), {
      target: { value: "https://example.test/work" },
    });
    fireEvent.change(screen.getByLabelText("Why this evidence is relevant"), {
      target: {
        value: "Demonstrates comparable accessible interface delivery.",
      },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Submit immutable proposal" }),
    );

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining(
          `/talent/opportunities/${opportunity.id}/proposals`,
        ),
        expect.objectContaining({ method: "POST" }),
      ),
    );
    const submitCall = fetchMock.mock.calls.find(
      ([url, init]) =>
        String(url).includes(
          `/talent/opportunities/${opportunity.id}/proposals`,
        ) && init?.method === "POST",
    );
    const payload = JSON.parse(String(submitCall?.[1]?.body)) as Record<
      string,
      unknown
    >;
    expect(payload).toMatchObject({
      proposed_amount_minor: 95000,
      estimated_days: 10,
      availability_hours_per_week: 12,
      currency: "USD",
    });
    expect(
      await screen.findByText(/Proposal submitted with immutable terms/i),
    ).toBeInTheDocument();
  });
});
