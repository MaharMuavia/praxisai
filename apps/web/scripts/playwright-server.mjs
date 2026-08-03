import { spawn, spawnSync } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const nextBin = require.resolve("next/dist/bin/next");
const child = spawn(process.execPath, [nextBin, "dev"], {
  stdio: "inherit",
  detached: process.platform !== "win32",
  windowsHide: true,
});

let stopping = false;
function stop() {
  if (stopping) return;
  stopping = true;
  if (child.pid == null) return;
  if (process.platform === "win32") {
    spawnSync("taskkill", ["/pid", String(child.pid), "/t", "/f"], {
      stdio: "ignore",
    });
  } else {
    try {
      process.kill(-child.pid, "SIGTERM");
    } catch {
      child.kill("SIGTERM");
    }
  }
}

process.once("SIGINT", stop);
process.once("SIGTERM", stop);
child.once("exit", (code, signal) => {
  if (!stopping) process.exitCode = code ?? (signal ? 1 : 0);
  process.exit();
});
