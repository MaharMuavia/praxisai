import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EmployerTalentWorkspace } from "./employer-talent-workspace";

const proposal = {
  id: "33333333-3333-3333-3333-333333333333",
  opportunity_id: "11111111-1111-1111-1111-111111111111",
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
};

const opportunity = {
  id: proposal.opportunity_id,
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
  proposal_count: 1,
  my_proposal: null,
  created_at: "2026-07-31T00:00:00Z",
  proposals: [proposal],
};

afterEach(cleanup);

describe("EmployerTalentWorkspace", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("compares student evidence and records an employer acceptance reason", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/talent/employers/me/opportunities")) {
        return Promise.resolve(Response.json([opportunity]));
      }
      if (url.endsWith("/projects")) {
        return Promise.resolve(Response.json({ items: [] }));
      }
      if (
        url.includes(`/talent/proposals/${proposal.id}/decision`) &&
        init?.method === "POST"
      ) {
        return Promise.resolve(
          Response.json({
            ...proposal,
            state: "ACCEPTED",
            decision_reason:
              "The evidence and milestone plan best match the published requirements.",
            decided_at: "2026-07-31T01:00:00Z",
          }),
        );
      }
      return Promise.resolve(
        Response.json({ detail: "Unexpected request" }, { status: 500 }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<EmployerTalentWorkspace page="proposals" />);

    expect(await screen.findByText("Amina Yusuf")).toBeInTheDocument();
    expect(screen.getByText("Accessible directory")).toBeInTheDocument();
    expect(screen.getByText(/Validated workflow/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Decision reason"), {
      target: {
        value:
          "The evidence and milestone plan best match the published requirements.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Accept proposal" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining(`/talent/proposals/${proposal.id}/decision`),
        expect.objectContaining({ method: "POST" }),
      ),
    );
    const decisionCall = fetchMock.mock.calls.find(
      ([url, init]) =>
        String(url).includes(`/talent/proposals/${proposal.id}/decision`) &&
        init?.method === "POST",
    );
    expect(JSON.parse(String(decisionCall?.[1]?.body))).toMatchObject({
      decision: "ACCEPTED",
      reason:
        "The evidence and milestone plan best match the published requirements.",
    });
    expect(
      await screen.findByText(/Proposal selected. The student was notified/i),
    ).toBeInTheDocument();
  });
});
