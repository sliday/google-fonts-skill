#!/usr/bin/env node

import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const packageJson = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));

export function uvxArgs(args = []) {
  return ["--from", `google-fonts-mcp==${packageJson.version}`, "google-fonts-mcp", ...args];
}

export function run(args = process.argv.slice(2), spawnProcess = spawn) {
  const child = spawnProcess("uvx", uvxArgs(args), { stdio: "inherit", shell: false });
  child.on("error", (error) => {
    if (error.code === "ENOENT") {
      console.error("google-fonts-mcp requires uv. Install it from https://docs.astral.sh/uv/getting-started/installation/");
      process.exitCode = 127;
      return;
    }
    console.error(error.message);
    process.exitCode = 1;
  });
  child.on("exit", (code, signal) => {
    process.exitCode = signal ? 1 : (code ?? 1);
  });
  return child;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  run();
}
