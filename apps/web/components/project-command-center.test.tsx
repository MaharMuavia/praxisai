import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProjectCommandCenter } from "./project-command-center";

describe("ProjectCommandCenter", () => {
  it("renders task and immutable deliverable evidence", () => {
    render(
      <ProjectCommandCenter
        onWorkspaceChange={vi.fn()}
        role="coordinator"
        workspace={{
          project: {
            id: "11111111-1111-1111-1111-111111111111",
            client_organization_id: "22222222-2222-2222-2222-222222222222",
            title: "Accessible directory",
            description: "Approved fictional delivery evidence.",
            category: "website",
            state: "COMPLETED",
            version: 18,
            required_deposit_minor: 180000,
            funded_minor: 180000,
            currency: "USD",
            complexity: "LOW",
            is_demo: true,
            created_at: "2026-01-01T00:00:00Z",
          },
          latest_scope: {
            id: "66666666-6666-6666-6666-666666666666",
            version: 1,
            status: "CLIENT_ACCEPTED",
            snapshot: {
              normalized_title: "Accessible directory",
              summary: "A constrained and approved delivery scope.",
              effort_low_hours: 12,
              effort_high_hours: 18,
              complexity: "LOW",
              deliverables: ["Searchable directory"],
            },
            acceptance_criteria: ["Keyboard navigation is verified"],
            immutable_at: "2026-01-02T00:00:00Z",
            created_at: "2026-01-01T00:00:00Z",
          },
          latest_quote: {
            id: "77777777-7777-7777-7777-777777777777",
            scope_version_id: "66666666-6666-6666-6666-666666666666",
            version: 1,
            currency: "USD",
            low_minor: 120000,
            base_minor: 180000,
            high_minor: 240000,
            revision_rounds: 2,
            formula_version: "pilot-2026-01",
            status: "CLIENT_ACCEPTED",
            line_items: [
              {
                kind: "student_compensation",
                description: "student compensation",
                amount_minor: 160000,
              },
            ],
            created_at: "2026-01-02T00:00:00Z",
          },
          latest_staffing: {
            id: "88888888-8888-8888-8888-888888888888",
            status: "COMPLETED",
            weights_version: "pilot-2026-01",
            candidates: [
              {
                student_profile_id: "99999999-9999-9999-9999-999999999999",
                student_user_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                display_name: "Fictional Student",
                score_basis_points: 8200,
                confidence: "medium",
                components: { skill_fit: 90 },
                explanation: "Ranked from job-relevant evidence only.",
              },
            ],
            created_at: "2026-01-03T00:00:00Z",
          },
          eligible_leads: [
            {
              user_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
              display_name: "Fictional Lead",
              domains: ["accessibility"],
              available_hours: 8,
            },
          ],
          assignment_offers: [],
          latest_plan: null,
          milestones: [],
          tasks: [
            {
              id: "33333333-3333-3333-3333-333333333333",
              project_id: "11111111-1111-1111-1111-111111111111",
              milestone_id: null,
              assignee_id: "44444444-4444-4444-4444-444444444444",
              title: "Validate accessibility",
              definition_of_done:
                "Automated and keyboard evidence is attached.",
              state: "DONE",
              dependency_ids: [],
              estimate_hours: 3,
            },
          ],
          deliverables: [
            {
              id: "55555555-5555-5555-5555-555555555555",
              title: "Release candidate",
              status: "ACCEPTED",
              version: 1,
              artifact_kind: "repository",
              artifact_content_hash: "a".repeat(64),
              scan_status: "CLEAN",
              qa_status: "COMPLETED",
              qa_recommendation: "PASS",
              lead_recommendation: "RELEASE",
              client_decision: "ACCEPTED",
              created_at: "2026-01-15T00:00:00Z",
            },
          ],
          risks: [],
          timeline: [],
        }}
      />,
    );

    expect(screen.getByText("Validate accessibility")).toBeInTheDocument();
    expect(screen.getByText(/PASS \/ RELEASE \/ ACCEPTED/)).toBeInTheDocument();
    expect(screen.getByText(/hash a{12}/)).toBeInTheDocument();
    expect(
      screen.getByText("Keyboard navigation is verified"),
    ).toBeInTheDocument();
    expect(screen.getByText("student compensation")).toBeInTheDocument();
    expect(screen.getByText("Fictional Student")).toBeInTheDocument();
    expect(screen.getByText("82.00%")).toBeInTheDocument();
  });
});
