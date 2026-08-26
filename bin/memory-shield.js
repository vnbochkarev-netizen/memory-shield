#!/usr/bin/env node
"use strict";
/**
 * memory-shield — npm CLI wrapper.
 * Runs the Python skill scripts (stdlib only, Python 3.10+ required).
 *
 * Usage:
 *   memory-shield snapshot --memory <path> [--out <dir>] [--label <name>]
 *   memory-shield scan --memory <path> [--report <file>]
 *   memory-shield audit --before <snapshot> --after <snapshot>
 */
const { spawnSync } = require("child_process");
const path = require("path");

const script = path.join(__dirname, "..", "scripts", "memory_shield.py");
const r = spawnSync("python3", [script, ...process.argv.slice(2)], {
  stdio: "inherit",
});
process.exit(r.status === null ? 1 : r.status);
