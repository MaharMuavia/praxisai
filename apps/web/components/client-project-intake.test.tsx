import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ClientProjectIntake } from "./client-project-intake";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

afterEach(cleanup);

describe("ClientProjectIntake", () => {
  beforeEach(() => {
    push.mockReset();
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it("validates and submits the complete immutable intake payload", async () => {
    const fetchMock = vi.fn<typeof fetch>();
    fetchMock.mockResolvedValue(
      Response.json(
        {
          id: "11111111-1111-1111-1111-111111111111",
          client_organization_id: "22222222-2222-2222-2222-222222222222",
          title: "Accessible support portal",
          description: "A complete support portal for university students.",
          category: "crud_tool",
          state: "DRAFT",
          version: 1,
          required_deposit_minor: 0,
          funded_minor: 0,
          currency: "USD",
          complexity: "LOW",
          is_demo: true,
          created_at: "2026-07-31T00:00:00Z",
        },
        { status: 201 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<ClientProjectIntake />);
    fireEvent.change(screen.getByLabelText("Project title"), {
      target: { value: "Accessible support portal" },
    });
    fireEvent.change(screen.getByLabelText("Project type"), {
      target: { value: "crud_tool" },
    });
    fireEvent.change(screen.getByLabelText("Desired business outcome"), {
      target: { value: "Reduce support request turnaround time" },
    });
    fireEvent.change(screen.getByLabelText("Target users"), {
      target: { value: "University students and support coordinators" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));

    fireEvent.change(screen.getByLabelText("Current problem and context"), {
      target: {
        value:
          "Support requests currently arrive through unstructured email messages.",
      },
    });
    fireEvent.change(screen.getByLabelText(/Expected deliverables/i), {
      target: { value: "Authenticated request workflow\nReporting dashboard" },
    });
    fireEvent.change(screen.getByLabelText(/Constraints or dependencies/i), {
      target: { value: "WCAG AA\nNo sensitive health data" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));

    fireEvent.change(screen.getByLabelText(/Budget guidance/i), {
      target: { value: "2500" },
    });
    fireEvent.change(screen.getByLabelText(/Existing brief links/i), {
      target: { value: "https://example.test/brief.pdf" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Create project draft/i }),
    );

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [, init] = fetchMock.mock.calls[0];
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    expect(body).toMatchObject({
      category: "crud_tool",
      budget_guidance_minor: 250000,
      data_sensitivity: "internal",
      deliverables: ["Authenticated request workflow", "Reporting dashboard"],
      constraints: ["WCAG AA", "No sensitive health data"],
      attachment_references: ["https://example.test/brief.pdf"],
    });
    await waitFor(() =>
      expect(push).toHaveBeenCalledWith(
        "/client/projects/11111111-1111-1111-1111-111111111111",
      ),
    );
  });

  it("does not accept non-HTTPS attachment references", async () => {
    render(<ClientProjectIntake />);
    fireEvent.change(screen.getByLabelText("Project title"), {
      target: { value: "Accessible support portal" },
    });
    fireEvent.change(screen.getByLabelText("Project type"), {
      target: { value: "dashboard" },
    });
    fireEvent.change(screen.getByLabelText("Desired business outcome"), {
      target: { value: "Reduce support request turnaround time" },
    });
    fireEvent.change(screen.getByLabelText("Target users"), {
      target: { value: "University students" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));
    fireEvent.change(screen.getByLabelText("Current problem and context"), {
      target: {
        value:
          "Support requests currently arrive through unstructured email messages.",
      },
    });
    fireEvent.change(screen.getByLabelText(/Expected deliverables/i), {
      target: { value: "Reporting dashboard" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));
    fireEvent.change(screen.getByLabelText(/Existing brief links/i), {
      target: { value: "http://example.test/brief.pdf" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Create project draft/i }),
    );

    expect(
      await screen.findByText(/Invalid attachment URL/i),
    ).toBeInTheDocument();
  });
});
