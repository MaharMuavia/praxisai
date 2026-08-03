import type { components } from "@praxisai/api-client";
import { describe, expect, it } from "vitest";
import { resolveWorkspacePrimaryAction } from "./resolve";

type Session = components["schemas"]["SessionView"];

const session = (
  role: Session["active_membership"]["role"],
  capabilities: string[],
): Session => ({
  user_id: "11111111-1111-4111-8111-111111111111",
  display_name: "Test User",
  email: "test@example.test",
  active_membership: {
    organization_id: "22222222-2222-4222-8222-222222222222",
    organization_name: "Test Organization",
    role,
  },
  capabilities,
  onboarding_state: "COMPLETE",
  notification_count: 0,
  environment_label: "test",
  required_consent_versions: {},
});

describe("resolveWorkspacePrimaryAction", () => {
  it("resolves a client project action from the current route and capability", () => {
    const action = resolveWorkspacePrimaryAction({
      path: "/client/projects/33333333-3333-4333-8333-333333333333",
      root: "client",
      session: session("client_admin", ["projects:create"]),
      projects: [
        {
          id: "33333333-3333-4333-8333-333333333333",
          client_organization_id: "44444444-4444-4444-8444-444444444444",
          title: "Test project",
          description: "A project",
          category: "website",
          state: "DRAFT",
          version: 1,
          required_deposit_minor: 0,
          funded_minor: 0,
          currency: "USD",
          complexity: "LOW",
          is_demo: false,
          created_at: "2026-08-01T00:00:00Z",
        },
      ],
    });

    expect(action).toMatchObject({
      id: "continue-project-intake",
      href: "/client/projects/33333333-3333-4333-8333-333333333333",
      intent: "navigate",
    });
  });

  it("does not expose a privileged action without its capability", () => {
    const action = resolveWorkspacePrimaryAction({
      path: "/ops/approvals",
      root: "ops",
      session: session("coordinator", []),
      projects: [],
    });

    expect(action).toBeNull();
  });
});
