#!/usr/bin/env node

/**
 * UI-Master CLI Runner
 * Bridges Node.js / Bun environments to the native Rust Rig engine or Python fallback.
 */

import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { existsSync } from 'node:fs';
import { constants as osConstants } from 'node:os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const candidates = [
  join(__dirname, '../crates/ui-master-engine/target/release/ui-master-engine'),
  join(__dirname, '../crates/ui-master-engine/target/debug/ui-master-engine'),
  join(__dirname, '../skills/ui-master/scripts/uim'),
  join(process.env.HOME || '', '.bun/bin/uim'),
  join(process.env.HOME || '', '.bun/bin/ui-master-engine')
];

const args = process.argv.slice(2);
// Every audit, including strict native audits, must pass the launcher's
// coverage capability check. Direct Node-to-binary dispatch could use a stale
// target/debug executable that still reports a false-clean result.
const auditCommand = args[0] === 'audit';
let targetBin = auditCommand ? join(__dirname, '../skills/ui-master/scripts/uim') : null;
if (!auditCommand) {
  for (const cand of candidates) {
    if (existsSync(cand)) {
      targetBin = cand;
      break;
    }
  }
}
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

proc.on('close', (code, signal) => {
  const signalNumber = signal ? osConstants.signals[signal] : undefined;
  process.exit(code ?? (signalNumber ? 128 + signalNumber : 1));
});
