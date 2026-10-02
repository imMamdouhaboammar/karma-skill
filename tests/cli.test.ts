import { describe, expect, it } from "bun:test";
import { spawnSync } from "node:child_process";
import { join } from "node:path";

const projectRoot = join(import.meta.dir, "..");

describe("KARMA CLI runner via Bun", () => {
  it("runs karma doctor successfully", () => {
    const res = spawnSync("bun", ["bin/cli.js", "doctor"], {
      cwd: projectRoot,
      encoding: "utf-8",
    });
    expect(res.status).toBe(0);
    expect(res.stdout).toContain("records: 36");
    expect(res.stdout).toContain("packaged_skill: True");
  });

  it("finds recommendations in dry-run mode without network", () => {
    const res = spawnSync(
      "bun",
      [
        "bin/cli.js",
        "find",
        "--project",
        "examples/react-app",
        "--goal",
        "frontend UI polish",
        "--agent",
        "codex",
        "--json",
      ],
      {
        cwd: projectRoot,
        encoding: "utf-8",
      }
    );
    expect(res.status).toBe(0);
    const parsed = JSON.parse(res.stdout);
    expect(parsed.recommendations).toBeArray();
    expect(parsed.recommendations.length).toBeGreaterThan(0);
    expect(parsed.agent).toBe("codex");
  });

  it("supports windsurf agent in CLI", () => {
    const res = spawnSync(
      "bun",
      [
        "bin/cli.js",
        "find",
        "--project",
        "examples/python-api",
        "--goal",
        "security audit",
        "--agent",
        "windsurf",
        "--json",
      ],
      {
        cwd: projectRoot,
        encoding: "utf-8",
      }
    );
    expect(res.status).toBe(0);
    const parsed = JSON.parse(res.stdout);
    expect(parsed.agent).toBe("windsurf");
  });
});
