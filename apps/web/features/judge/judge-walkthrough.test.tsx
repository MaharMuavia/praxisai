import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { cleanup } from "@testing-library/react";
import { JudgeWalkthrough } from "./judge-walkthrough";

afterEach(cleanup);

describe("judge walkthrough", () => {
  it("keeps the deterministic scenario and human boundary visible", () => {
    render(<JudgeWalkthrough />);
    expect(
      screen.getByText(
        "Fixture AI and simulated workflow; no live provider calls.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Submit a bounded project brief" }),
    ).toBeInTheDocument();
    fireEvent.keyDown(
      screen.getByRole("application", {
        name: "Interactive PraxisAI judge walkthrough",
      }),
      { key: "ArrowRight" },
    );
    expect(
      screen.getByRole("heading", { name: "Draft scope assumptions" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/AI proposes; it cannot accept scope/),
    ).toBeInTheDocument();
  });

  it("supports direct step selection and restart", () => {
    render(<JudgeWalkthrough />);
    fireEvent.click(
      within(
        screen.getByRole("complementary", { name: "Walkthrough steps" }),
      ).getByRole("button", { name: /14.*Control portfolio/ }),
    );
    expect(
      screen.getByRole("heading", {
        name: "Control portfolio and credential proof",
      }),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /Restart walkthrough/ }),
    );
    expect(
      screen.getByRole("heading", { name: "Submit a bounded project brief" }),
    ).toBeInTheDocument();
  });
});

describe("judge sandbox", () => {
  it("renders an illustrative scoping proposal and labels it as not live", async () => {
    const { JudgeSandbox } = await import("./judge-sandbox");
    render(<JudgeSandbox />);

    expect(
      screen.getByRole("heading", {
        name: "Walk the agent contract & deterministic boundaries in 60 seconds.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/pre-scripted deterministic illustrations/),
    ).toBeInTheDocument();

    const runButton = screen.getByRole("button", {
      name: /Show illustrative.*proposal/,
    });
    fireEvent.click(runButton);

    expect(
      await screen.findByText(/"status": "PROPOSAL_GENERATED"/),
    ).toBeInTheDocument();
  });

  it("handles prompt injection preset safely", async () => {
    const { JudgeSandbox } = await import("./judge-sandbox");
    render(<JudgeSandbox />);

    fireEvent.click(
      screen.getByRole("button", {
        name: /Prompt Injection Attack/,
      }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: /Show illustrative.*proposal/ }),
    );

    expect(
      await screen.findByText(/"status": "PROMPT_INJECTION_CONTAINED"/),
    ).toBeInTheDocument();
  });

  it("calculates deterministic escrow pricing across slider inputs", async () => {
    const { JudgeSandbox } = await import("./judge-sandbox");
    render(<JudgeSandbox />);

    fireEvent.click(
      screen.getByRole("button", { name: /3\. Deterministic Escrow/ }),
    );

    expect(screen.getByText("Student Talent Squad (75%)")).toBeInTheDocument();
    expect(screen.getByText("Total Escrow Quote")).toBeInTheDocument();
  });
});

describe("judge scorecard", () => {
  it("maps to the three judging criteria and shows honest gaps", async () => {
    const { JudgeScorecard } = await import("./judge-scorecard");
    render(<JudgeScorecard />);

    expect(
      screen.getByRole("heading", {
        name: "How PraxisAI maps to the three judging criteria.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "AI-Native Operations" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Business Viability" }),
    ).toBeInTheDocument();
    // The scorecard must state gaps, not just strengths.
    expect(screen.getAllByText(/Gap:/).length).toBeGreaterThan(0);
  });
});
