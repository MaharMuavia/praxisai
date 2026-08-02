import { describe, expect, it } from "vitest";
import {
  demoWorkspaceSnapshot,
  isRecoverableDemoError,
  withDemoFallback,
} from "./demo-data";

describe("demo data boundary", () => {
  it("uses fixtures for network failures", async () => {
    const result = await withDemoFallback(
      Promise.reject(new TypeError("Failed to fetch")),
      demoWorkspaceSnapshot.projects,
    );

    expect(result.isDemo).toBe(true);
    expect(result.data).toBe(demoWorkspaceSnapshot.projects);
  });

  it("keeps live data authoritative", async () => {
    const liveProjects = demoWorkspaceSnapshot.projects.slice(0, 1);
    const result = await withDemoFallback(
      Promise.resolve(liveProjects),
      demoWorkspaceSnapshot.projects,
    );

    expect(result.isDemo).toBe(false);
    expect(result.data).toBe(liveProjects);
  });

  it("does not classify authorization errors as demo fallbacks", () => {
    expect(isRecoverableDemoError(new Error("Request failed (403)"))).toBe(
      false,
    );
    expect(isRecoverableDemoError(new Error("Request failed (503)"))).toBe(
      true,
    );
  });
});
