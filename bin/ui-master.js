#!/usr/bin/env node

/**
 * UI-Master CLI Runner
 * Bridges Node.js / Bun environments to the native Rust Rig engine or Python fallback.
 */

import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { existsSync } from 'node:fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const candidates = [
  join(__dirname, '../crates/ui-master-engine/target/release/ui-master-engine'),
  join(__dirname, '../crates/ui-master-engine/target/debug/ui-master-engine'),
  join(__dirname, '../skills/ui-master/scripts/uim'),
  join(process.env.HOME || '', '.bun/bin/uim'),
  join(process.env.HOME || '', '.bun/bin/ui-master-engine')
];

let targetBin = null;
for (const cand of candidates) {
  if (existsSync(cand)) {
    targetBin = cand;
    break;
  }
}

let args = process.argv.slice(2);
let command = targetBin || 'uim';

if (!targetBin) {
  // If no binary exists, delegate to the shell runner
  command = join(__dirname, '../skills/ui-master/scripts/uim');
}

const proc = spawn(command, args, {
  stdio: 'inherit',
  env: process.env
});

proc.on('error', (err) => {
  console.error(`Error executing UI-Master: ${err.message}`);
  process.exit(1);
});

proc.on('close', (code) => {
  process.exit(code ?? 0);
});
