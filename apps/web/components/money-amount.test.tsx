import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MoneyAmount } from "./money-amount";

describe("MoneyAmount", () => {
  it("renders integer minor units as the configured currency", () => {
    render(<MoneyAmount amountMinor={125050} currency="USD" />);
    expect(screen.getByText("$1,250.50")).toBeInTheDocument();
  });
});
