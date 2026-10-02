#!/usr/bin/env node

/**
 * KARMA ☯ | Universal Agent Skill & CLI runner
 * Bridges Node.js / Bun environments to the offline-first Python runtime.
 */

import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { existsSync } from 'node:fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Locate portable karma.py or root src
const candidates = [
  join(__dirname, '../skills/find-karma/scripts/karma.py'),
  join(__dirname, '../src/karma/runtime.py'),
  join(__dirname, 'karma.py')
];

let targetScript = null;
for (const cand of candidates) {
  if (existsSync(cand)) {
    targetScript = cand;
    break;
  }
}

if (!targetScript) {
  console.error('Error: Could not locate karma.py script.');
  process.exit(1);
}

const args = [targetScript, ...process.argv.slice(2)];
const pythonExec = process.env.PYTHON_BIN || 'python3';

const proc = spawn(pythonExec, args, {
  stdio: 'inherit',
  env: process.env
});

proc.on('error', (err) => {
  if (err.code === 'ENOENT') {
    console.error(`Error: '${pythonExec}' was not found on PATH. KARMA requires Python 3.10+ stdlib.`);
  } else {
    console.error(`Error executing KARMA: ${err.message}`);
  }
  process.exit(1);
});

proc.on('close', (code) => {
  process.exit(code ?? 0);
});
