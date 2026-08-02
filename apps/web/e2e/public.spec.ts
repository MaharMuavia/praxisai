import { expect, test } from "@playwright/test";

test("landing page communicates the supervised operating model", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /From learning to paid delivery/i }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "Students build proof. Employers choose. Teams verify delivery.",
    ),
  ).toBeVisible();
  await expect(page.getByText("Demo data").first()).toBeVisible();
});

for (const path of [
  "/how-it-works/clients",
  "/how-it-works/students",
  "/project-types",
  "/pricing",
  "/trust",
  "/universities",
  "/verify",
  "/terms",
  "/privacy",
  "/accessibility",
  "/login",
  "/signup",
  "/auth/callback",
  "/invite/demo-invitation",
  "/onboarding/student",
  "/onboarding/lead",
  "/onboarding/client",
  "/portfolio/demo-student",
]) {
  test(`public route ${path} renders`, async ({ page }) => {
    await page.goto(path);
    await expect(page.locator("h1")).toBeVisible();
  });
}

for (const path of [
  "/client",
  "/client/projects",
  "/client/projects/new",
  "/client/invoices",
  "/client/organization",
  "/student",
  "/student/offers",
  "/student/projects",
  "/student/earnings",
  "/student/credentials",
  "/lead",
  "/lead/offers",
  "/lead/earnings",
  "/ops",
  "/ops/approvals",
  "/ops/risks",
  "/ops/projects",
  "/ops/students",
  "/ops/agent-runs",
  "/admin",
  "/admin/access",
  "/admin/integrations",
  "/admin/jobs",
  "/university",
  "/university/students",
  "/university/exports",
  "/university/settings",
]) {
  test(`workspace route ${path} renders its authorized shell`, async ({
    page,
  }) => {
    await page.goto(path);
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.getByText("Demo data").first()).toBeVisible();
  });
}
