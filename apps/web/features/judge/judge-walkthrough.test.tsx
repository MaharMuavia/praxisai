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
