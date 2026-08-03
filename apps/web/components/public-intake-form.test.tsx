import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PublicIntakeForm } from "./public-intake-form";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("PublicIntakeForm", () => {
  it("sends a company intake to the public API and confirms only after persistence", async () => {
    let requestUrl: RequestInfo | URL | undefined;
    let requestInit: RequestInit | undefined;
    const request = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        requestUrl = input;
        requestInit = init;
        return Response.json(
          { correlation_id: "corr-company-1" },
          { status: 201 },
        );
      },
    );
    vi.stubGlobal("fetch", request);

    render(<PublicIntakeForm />);
    fireEvent.change(screen.getByLabelText("Full name"), {
      target: { value: "Amina Noor" },
    });
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "amina@example.test" },
    });
    fireEvent.change(screen.getByLabelText("Country"), {
      target: { value: "Pakistan" },
    });
    fireEvent.change(screen.getByLabelText("Company name"), {
      target: { value: "Northstar Studio" },
    });
    fireEvent.change(
      screen.getByLabelText(
        "What business problem should the project address?",
      ),
      {
        target: {
          value:
            "We need supervised help making our civic resource directory accessible.",
        },
      },
    );
    fireEvent.change(screen.getByLabelText("Desired result"), {
      target: { value: "A clear, tested workflow for the operations team." },
    });
    fireEvent.change(screen.getByLabelText("Project category"), {
      target: { value: "workflow automation" },
    });
    fireEvent.change(screen.getByLabelText("Target timeline"), {
      target: { value: "This quarter" },
    });
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(
      screen.getByRole("button", { name: "Submit for human review" }),
    );

    await waitFor(() => expect(request).toHaveBeenCalledOnce());
    expect(requestUrl).toBe("/api/v1/public/company");
    expect(requestInit?.method).toBe("POST");
    expect(
      new Headers(requestInit?.headers).get("Idempotency-Key"),
    ).toBeTruthy();
    expect(screen.getByRole("status")).toHaveTextContent("corr-company-1");
    expect(
      screen.queryByRole("button", { name: "Submit for human review" }),
    ).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Submit another request" }),
    );
    expect(
      screen.getByRole("button", { name: "Submit for human review" }),
    ).toBeInTheDocument();
  });

  it("keeps the form in an error state when the API rejects the submission", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        Response.json(
          {
            error: {
              message: "Submission rate limit reached",
              correlation_id: "corr-limit-1",
            },
          },
          { status: 429 },
        ),
      ),
    );

    render(<PublicIntakeForm />);
    fireEvent.change(screen.getByLabelText("Full name"), {
      target: { value: "Amina Noor" },
    });
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "amina@example.test" },
    });
    fireEvent.change(screen.getByLabelText("Country"), {
      target: { value: "Pakistan" },
    });
    fireEvent.change(screen.getByLabelText("Company name"), {
      target: { value: "Northstar Studio" },
    });
    fireEvent.change(
      screen.getByLabelText(
        "What business problem should the project address?",
      ),
      {
        target: {
          value:
            "We need supervised help making our civic resource directory accessible.",
        },
      },
    );
    fireEvent.change(screen.getByLabelText("Desired result"), {
      target: { value: "A clear, tested workflow for the operations team." },
    });
    fireEvent.change(screen.getByLabelText("Project category"), {
      target: { value: "workflow automation" },
    });
    fireEvent.change(screen.getByLabelText("Target timeline"), {
      target: { value: "This quarter" },
    });
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(
      screen.getByRole("button", { name: "Submit for human review" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Too many submissions from this address",
    );
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
