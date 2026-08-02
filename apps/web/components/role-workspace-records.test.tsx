import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RoleWorkspaceRecords } from "./role-workspace-records";

describe("RoleWorkspaceRecords", () => {
  it("renders approved external invoice evidence without implying payment processing", () => {
    render(
      <RoleWorkspaceRecords
        data={{
          kind: "invoices",
          items: [
            {
              id: "11111111-1111-1111-1111-111111111111",
              project_id: "22222222-2222-2222-2222-222222222222",
              project_title: "Accessibility audit",
              number: "INV-DEMO-001",
              amount_minor: 125050,
              currency: "USD",
              status: "FUNDED_EXTERNALLY",
              environment: "demo",
              created_at: "2026-07-30T00:00:00Z",
            },
          ],
        }}
      />,
    );

    expect(screen.getByText("INV-DEMO-001")).toBeInTheDocument();
    expect(screen.getByText("$1,250.50")).toBeInTheDocument();
    expect(screen.getByText("FUNDED EXTERNALLY")).toBeInTheDocument();
    expect(screen.queryByText(/Stripe/i)).not.toBeInTheDocument();
  });

  it("shows an intentional empty state", () => {
    render(<RoleWorkspaceRecords data={{ kind: "credentials", items: [] }} />);

    expect(
      screen.getByText("No authorized records require attention."),
    ).toBeInTheDocument();
  });

  it("shows complete offer terms and exposes penalty-free decisions", () => {
    const decide = vi.fn();
    render(
      <RoleWorkspaceRecords
        data={{
          kind: "offers",
          items: [
            {
              id: "33333333-3333-3333-3333-333333333333",
              project_id: "44444444-4444-4444-4444-444444444444",
              recipient_user_id: "55555555-5555-5555-5555-555555555555",
              role: "student developer",
              state: "OFFERED",
              terms_snapshot: {
                gross_compensation_minor: 120000,
                currency: "USD",
              },
              expires_at: "2026-08-02T00:00:00Z",
              decided_at: null,
            },
          ],
        }}
        onOfferDecision={decide}
      />,
    );

    expect(screen.getByText("$1,200.00")).toBeInTheDocument();
    expect(
      screen.getByText(/declining has no reputation penalty/i),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Accept" }));
    expect(decide).toHaveBeenCalledWith(
      "33333333-3333-3333-3333-333333333333",
      "accept",
    );
  });
});
