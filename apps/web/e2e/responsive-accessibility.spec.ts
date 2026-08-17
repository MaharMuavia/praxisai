import { expect, test } from "@playwright/test";

const viewports = [
  { name: "phone", width: 320, height: 720 },
  { name: "mobile", width: 375, height: 812 },
  { name: "tablet", width: 768, height: 900 },
  { name: "laptop", width: 1024, height: 900 },
  { name: "desktop", width: 1440, height: 1000 },
];

for (const viewport of viewports) {
  test(`marketing layout remains usable at ${viewport.name}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await page.goto("/for-students");

    await expect(page.locator("main")).toHaveCount(1);
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator("header.marketing-header")).toBeVisible();
    if (viewport.width < 1024) {
      await expect(
        page.getByRole("button", { name: "Open navigation menu" }),
      ).toBeVisible();
    } else {
      await expect(
        page.getByRole("navigation", { name: "Primary navigation" }),
      ).toBeVisible();
    }
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    expect(await page.locator("img:not([alt])").count()).toBe(0);
  });
}

test("workspace shell remains usable at mobile and desktop widths", async ({
  page,
}) => {
  for (const viewport of [
    { width: 375, height: 812 },
    { width: 1440, height: 1000 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto("/client");
    await expect(page.locator("main")).toHaveCount(1);
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.getByText("Demo data")).toHaveCount(0);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  }
});

test("key marketing surfaces have stable visual snapshots", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page).toHaveScreenshot("marketing-home.png", {
    animations: "disabled",
    caret: "hide",
    fullPage: true,
    maxDiffPixelRatio: 0.35,
    timeout: 15_000,
  });

  await page.goto("/trust");
  await expect(page).toHaveScreenshot("marketing-trust.png", {
    animations: "disabled",
    caret: "hide",
    fullPage: true,
    maxDiffPixels: 800,
    timeout: 15_000,
  });
});
