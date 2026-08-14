import { defineConfig, devices } from "@playwright/test";

const playwrightPort = process.env.PLAYWRIGHT_PORT ?? "3000";
if (!/^\d+$/.test(playwrightPort)) {
  throw new Error("PLAYWRIGHT_PORT must be an integer between 1 and 65535");
}

const port = Number(playwrightPort);
if (!Number.isSafeInteger(port) || port < 1 || port > 65535) {
  throw new Error("PLAYWRIGHT_PORT must be an integer between 1 and 65535");
}

const baseURL = `http://localhost:${port}`;

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL, trace: "retain-on-failure" },
  webServer: {
    command: "node scripts/playwright-server.mjs",
    url: baseURL,
    env: { PORT: String(port) },
    reuseExistingServer: false,
    gracefulShutdown: { signal: "SIGINT", timeout: 5000 },
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        ...(process.env.PLAYWRIGHT_USE_SYSTEM_CHROME === "true"
          ? { channel: "chrome" }
          : {}),
      },
    },
  ],
});
