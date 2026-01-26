#!/usr/bin/env node
/**
 * fail-only-fast-min.js
 *
 * Minimal Newman runner that prints only failed assertions as NDJSON.
 * Usage:
 *   node fail-only-fast-min.js <collection.json> [--out fail.ndjson]
 *
 * Output (NDJSON, one JSON per line):
 *   {"folder":"ROOT","item":"POST /api","assertion":"status code","message":"Expected 200 but got 500"}
 *
 * Exit codes:
 *   0 -> all assertions passed
 *   1 -> assertion failures occurred
 *   2 -> runtime error (invalid input / Newman error)
 */

const fs = require('fs');
const path = require('path');

// ---- Robustly load newman so we control the exit code when it's missing
let newman;
try {
  const { createRequire } = require('module');
  const requireHere = createRequire(__dirname + '/'); // prefer local next to this script
  newman = requireHere('newman');
} catch (e) {
  try {
    newman = require('newman'); // fallback to CWD resolution
  } catch (e2) {
    console.error('Newman module not found. Install it locally or expose it via NODE_PATH to the global npm root.');
    process.exit(2);
  }
}

// ---- Helpers
const closeWriterAndExit = (writer, code) => {
  if (writer !== process.stdout) {
    try {
      writer.end(() => process.exit(code));
    } catch {
      process.exit(code);
    }
  } else {
    process.exit(code);
  }
};

// Ensure we always exit with 2 on unexpected runtime errors
process.on('uncaughtException', (err) => {
  console.error('Runtime error (uncaughtException):', err && err.stack || err);
  closeWriterAndExit(process.stdout, 2);
});
process.on('unhandledRejection', (reason) => {
  console.error('Runtime error (unhandledRejection):', reason);
  closeWriterAndExit(process.stdout, 2);
});

// -------------------- Parse args --------------------
const args = process.argv.slice(2);
if (!args[0]) {
  console.error('Usage: node fail-only-fast-min.js <collection.json> [--out fail.ndjson]');
  process.exit(2);
}

const collection = path.resolve(args[0]);
if (!fs.existsSync(collection)) {
  console.error('Collection not found:', collection);
  process.exit(2);
}

const outIdx = args.indexOf('--out');
const outFile = (outIdx !== -1 && args[outIdx + 1]) ? path.resolve(args[outIdx + 1]) : null;

let writer = process.stdout;
if (outFile) {
  // ensure output directory exists
  const dir = path.dirname(outFile);
  try {
    fs.mkdirSync(dir, { recursive: true });
  } catch (e) {
    console.error('Failed to create output directory:', dir, e && e.message || e);
    process.exit(2);
  }
  try {
    writer = fs.createWriteStream(outFile, { encoding: 'utf8', flags: 'w' });
    writer.on('error', (e) => {
      console.error('Failed to write NDJSON:', e && e.message || e);
      closeWriterAndExit(writer, 2);
    });
  } catch (e) {
    console.error('Failed to open output file:', outFile, e && e.message || e);
    process.exit(2);
  }
}

// -------------------- Run Newman --------------------
let total = 0, failed = 0;

newman.run({
  collection,
  reporters: [],
  color: false,
  bail: false,
  timeout: 0,
  timeoutRequest: 1,    // skip real requests (mock mode)
  timeoutScript: 2000,
  ignoreRedirects: true,
  insecure: true
}, (err) => {
  if (err) {
    console.error('Newman error:', err.message || err);
    return closeWriterAndExit(writer, 2);
  }
  return closeWriterAndExit(writer, failed > 0 ? 1 : 0);
})
.on('assertion', (err, o) => {
  total++;
  if (!err) return;
  failed++;

  const obj = {
    folder: o?.item?.parent?.name || 'ROOT',
    item: o?.item?.name || '<unnamed>',
    assertion: o?.assertion || '<unnamed>',
    message: String(err?.message ?? err)
  };
  // If write fails, 'error' handler on writer will turn it into exit code 2
  writer.write(JSON.stringify(obj) + '\n');
})
.on('console', () => {})
.on('request', () => {});
