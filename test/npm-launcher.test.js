import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import test from "node:test";

import { run, uvxArgs } from "../bin/google-fonts-mcp.js";

test("launcher pins the matching PyPI release and forwards arguments", () => {
  assert.deepEqual(uvxArgs(["--help"]), [
    "--from",
    "google-fonts-mcp==1.4.0",
    "google-fonts-mcp",
    "--help",
  ]);
});

function withProcessState(callback) {
  const exitCode = process.exitCode;
  const consoleError = console.error;
  try {
    process.exitCode = undefined;
    return callback();
  } finally {
    process.exitCode = exitCode;
    console.error = consoleError;
  }
}

test("launcher reports a missing uv executable", () => {
  withProcessState(() => {
    const child = new EventEmitter();
    let message = "";
    console.error = (value) => {
      message = value;
    };

    run([], () => child);
    const error = new Error("spawn uvx ENOENT");
    error.code = "ENOENT";
    child.emit("error", error);

    assert.equal(process.exitCode, 127);
    assert.match(message, /requires uv/);
  });
});

test("launcher preserves child exit codes", () => {
  withProcessState(() => {
    const child = new EventEmitter();
    run([], () => child);
    child.emit("exit", 42, null);
    assert.equal(process.exitCode, 42);
  });
});

test("launcher fails when the child exits on a signal", () => {
  withProcessState(() => {
    const child = new EventEmitter();
    run([], () => child);
    child.emit("exit", null, "SIGTERM");
    assert.equal(process.exitCode, 1);
  });
});
