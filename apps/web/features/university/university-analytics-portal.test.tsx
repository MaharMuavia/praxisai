import { cleanup, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, it } from "vitest";
import { UniversityAnalyticsPortal } from "./university-analytics-portal";

afterEach(cleanup);

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("UniversityAnalyticsPortal", () => {
  it("renders accredited university metrics and Perkins V compliance indicators", async () => {
    renderWithClient(<UniversityAnalyticsPortal />);

    expect(
      await screen.findByRole("heading", {
        name: "University Outcomes & Perkins V Compliance",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Consented Cohort")).toBeInTheDocument();
    expect(screen.getByText("Verified Work Hours")).toBeInTheDocument();
    expect(screen.getByText("Student Escrow Earnings")).toBeInTheDocument();
    expect(screen.getByText("Verified Credentials")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Competency & Hours Distribution" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Generate Perkins V / IPEDS Audit Exports",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Instant CSV Download" }),
    ).toBeInTheDocument();
  });
});
