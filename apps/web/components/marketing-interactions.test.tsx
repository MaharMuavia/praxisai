import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MarketingNav } from "./marketing-nav";
import { MarketingProductPreview } from "./marketing-product-preview";

afterEach(() => {
  document.body.style.overflow = "";
});

describe("premium marketing interactions", () => {
  it("opens a structured desktop menu and restores focus on Escape", async () => {
    render(<MarketingNav />);
    const product = screen.getByRole("button", { name: "Product" });
    fireEvent.click(product);
    expect(screen.getByRole("menu")).toBeInTheDocument();
    expect(
      screen.getByRole("menuitem", { name: /How it works/i }),
    ).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
    await waitFor(() => expect(product).toHaveFocus());
  });

  it("switches sanitized product previews without presenting metrics as evidence", () => {
    render(<MarketingProductPreview />);
    fireEvent.click(screen.getByRole("tab", { name: "Readiness" }));
    expect(
      screen.getByRole("heading", { name: "Student readiness evidence" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Product demonstration")).toBeInTheDocument();
    expect(screen.queryByText("126")).not.toBeInTheDocument();
  });
});
