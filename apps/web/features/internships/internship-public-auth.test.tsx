import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { StudentSignup } from "./internship-public";

const PROGRAM_ID = "11111111-1111-4111-8111-111111111111";
const COHORT_ID = "22222222-2222-4222-8222-222222222222";
const signUp = vi.fn();

vi.mock("next/navigation", () => ({
  useSearchParams: () =>
    new URLSearchParams({ program: PROGRAM_ID, cohort: COHORT_ID }),
}));

vi.mock("@/lib/supabase", () => ({
  getSupabaseClient: () => ({ auth: { signUp } }),
}));

describe("StudentSignup Supabase flow", () => {
  beforeEach(() => {
    signUp.mockReset();
    signUp.mockResolvedValue({
      data: { user: { id: "supabase-user" } },
      error: null,
    });
  });

  afterEach(cleanup);

  it("sends an explicit callback URL that preserves program context", async () => {
    render(<StudentSignup />);
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "student@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "long-enough-password" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Send verification email" }),
    );

    await waitFor(() => expect(signUp).toHaveBeenCalledOnce());
    const request = signUp.mock.calls[0]?.[0] as {
      email: string;
      password: string;
      options: { emailRedirectTo: string };
    };
    expect(request.email).toBe("student@example.com");
    expect(request.password).toBe("long-enough-password");
    const redirect = new URL(request.options.emailRedirectTo);
    expect(redirect.pathname).toBe("/auth/callback");
    expect(redirect.searchParams.get("next")).toBe(
      `/auth/student-signup?program=${PROGRAM_ID}&cohort=${COHORT_ID}`,
    );
    expect(await screen.findByRole("status")).toHaveTextContent(
      "confirmation link will return here",
    );
  });
});
