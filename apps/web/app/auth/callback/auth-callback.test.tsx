import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthCallback } from "./auth-callback";

const replace = vi.fn();
const router = { replace };
const exchangeCodeForSession = vi.fn();
let currentParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => router,
  useSearchParams: () => currentParams,
}));

vi.mock("@/lib/supabase", () => ({
  getSupabaseClient: () => ({ auth: { exchangeCodeForSession } }),
}));

describe("AuthCallback", () => {
  beforeEach(() => {
    replace.mockReset();
    exchangeCodeForSession.mockReset();
    currentParams = new URLSearchParams();
  });

  afterEach(cleanup);

  it("exchanges the one-time PKCE code and returns to student signup", async () => {
    currentParams = new URLSearchParams({
      code: "one-time-auth-code",
      next: "/auth/student-signup?program=11111111-1111-4111-8111-111111111111",
    });
    exchangeCodeForSession.mockResolvedValue({ data: {}, error: null });

    render(<AuthCallback />);

    await waitFor(() =>
      expect(exchangeCodeForSession).toHaveBeenCalledWith("one-time-auth-code"),
    );
    expect(replace).toHaveBeenCalledWith(
      "/auth/student-signup?program=11111111-1111-4111-8111-111111111111",
    );
  });

  it("does not exchange a missing code", async () => {
    currentParams = new URLSearchParams({ next: "https://attacker.example" });

    render(<AuthCallback />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "missing or invalid",
    );
    expect(exchangeCodeForSession).not.toHaveBeenCalled();
    expect(replace).not.toHaveBeenCalled();
  });
});
