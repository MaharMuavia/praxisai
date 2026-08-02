import { expect, test } from "@playwright/test";

test("landing page communicates the supervised operating model", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: /Turn potential into paid professional experience/i,
    }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "Students build proof. Employers choose. Teams verify delivery.",
    ),
  ).toBeVisible();
  await expect(page.getByText("Conceptual workflow").first()).toBeVisible();
  await expect(page.getByText("126")).toHaveCount(0);
});

test("marketing navigation works at mobile width and does not overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  const menuButton = page.getByRole("button", {
    name: "Open navigation menu",
  });
  await menuButton.focus();
  await menuButton.press("Enter");
  await expect(
    page.getByRole("navigation", { name: "Mobile navigation" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Apply as a student" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Open navigation menu" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Open navigation menu" }),
  ).toBeFocused();
});

test("desktop dropdown navigation is keyboard accessible", async ({ page }) => {
  await page.goto("/");
  const product = page.getByRole("button", { name: "Product" });
  await product.focus();
  await product.press("Enter");
  await expect(page.getByRole("menu")).toBeVisible();
  await expect(
    page.getByRole("menuitem", { name: "How it works" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("menu")).toHaveCount(0);
  await expect(product).toBeFocused();
});

test("workflow and product preview remain understandable without autoplay", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Next workflow stage" }).click();
  await expect(page.getByText("AI-assisted scope").last()).toBeVisible();
  await expect(
    page.getByText(/Manual review mode|Sequencing paused/),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Readiness" }).click();
  await expect(
    page.getByRole("heading", { name: "Student readiness evidence" }),
  ).toBeVisible();
});

test("320px layout has no horizontal overflow and reduced motion is respected", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 320, height: 720 });
  await page.goto("/");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  const motionState = await page
    .locator(".marketing-hero-copy h1")
    .evaluate((node) => getComputedStyle(node).animationDuration);
  expect(parseFloat(motionState)).toBeLessThanOrEqual(0.001);
});

for (const path of [
  "/how-it-works/clients",
  "/how-it-works/students",
  "/how-it-works",
  "/for-students",
  "/for-companies",
  "/for-expert-leads",
  "/for-universities",
  "/solutions",
  "/solutions/ai-automation",
  "/solutions/data-dashboards",
  "/solutions/internal-tools",
  "/solutions/customer-portals",
  "/project-types",
  "/pricing",
  "/trust",
  "/universities",
  "/verify",
  "/terms",
  "/privacy",
  "/accessibility",
  "/trust/ai-governance",
  "/trust/student-protection",
  "/trust/data-and-privacy",
  "/impact",
  "/about",
  "/contact",
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
