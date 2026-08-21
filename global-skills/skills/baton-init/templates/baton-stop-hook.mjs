#!/usr/bin/env node
// Post-turn hook for Baton — any agent whose end-of-turn lifecycle hook sends
// a JSON payload on stdin: Claude Code's `Stop`/`StopFailure`, Codex's
// `Stop`/`SessionEnd`, Gemini CLI's `AfterAgent`/`SessionEnd`.
//
// Writes a small JSON breadcrumb recording where the session was last seen.
// It never calls the model, so it costs zero tokens, and it can't write
// prose — the durable state lives in `.baton/<task>.md`, which the model
// maintains. This file only helps recover context when a baton looks
// doubtful or a session ended abnormally.
//
// Best-effort by design: a user interrupt (Ctrl+C/ESC), a forced kill, or a
// power cut means this never runs at all. That's fine — the markdown file
// is the source of truth either way.
//
// No-op unless `.baton/` already exists somewhere above the hook's cwd; it
// doesn't create one.
//
// stdin fields used: session_id, transcript_path, cwd, hook_event_name,
// whichever field carries the last response (`last_assistant_message` on
// Claude Code and Codex, `prompt_response` on Gemini CLI), and `error` on a
// failure event.

import { existsSync, mkdirSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { StringDecoder } from "node:string_decoder";

const MAX_ANCESTOR_DEPTH = 20;
const MAX_MESSAGE_BYTES = 4096;

// Session ids become filenames, so anything outside this set is refused
// rather than sanitized — a payload that doesn't look like an id is a sign
// something is wrong, not something to guess at. Keeping the id verbatim
// (rather than hashing it) is what lets a person match a baton's `session`
// field to a file in `.session/` by eye.
const SAFE_SESSION_ID = /^[A-Za-z0-9._-]{1,128}$/;

function findBatonRoot(startCwd) {
  let dir = startCwd;
  for (let i = 0; i < MAX_ANCESTOR_DEPTH; i++) {
    if (existsSync(join(dir, ".baton"))) return dir;
    const parent = dirname(dir);
    if (parent === dir) return null;
    dir = parent;
  }
  return null;
}

// Cuts to a byte budget without splitting a multi-byte character in half —
// a naive slice turns the last Korean syllable or emoji into U+FFFD.
function truncate(text) {
  if (typeof text !== "string") return null;
  const buf = Buffer.from(text, "utf8");
  if (buf.length <= MAX_MESSAGE_BYTES) return text;
  const decoder = new StringDecoder("utf8");
  const head = decoder.write(buf.subarray(0, MAX_MESSAGE_BYTES));
  return `${head}…`;
}

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", () => resolve(data));
    // Never hang the session on a hook that isn't going to get input.
    setTimeout(() => resolve(data), 2000).unref();
  });
}

// Write to a temp file and rename, so a process that dies mid-write leaves
// the previous breadcrumb intact instead of a half-written one.
function writeAtomic(path, contents) {
  const tmp = `${path}.tmp`;
  writeFileSync(tmp, contents, { encoding: "utf8", mode: 0o600 });
  renameSync(tmp, path);
}

async function main() {
  const raw = await readStdin();
  let payload;
  try {
    payload = JSON.parse(raw);
  } catch {
    return; // Malformed input — quietly do nothing rather than error the session.
  }

  const cwd = typeof payload.cwd === "string" ? payload.cwd : process.cwd();
  const sessionId = payload.session_id;
  if (typeof sessionId !== "string" || !SAFE_SESSION_ID.test(sessionId)) return;

  const root = findBatonRoot(cwd);
  if (!root) return; // No .baton/ anywhere above — nothing tracks this session.

  const sidecarDir = join(root, ".baton", ".session");
  mkdirSync(sidecarDir, { recursive: true, mode: 0o700 });

  const breadcrumb = {
    // Named for what it is: when the hook last observed this session, not a
    // claim about how fresh the baton is.
    observedAt: new Date().toISOString(),
    event: typeof payload.hook_event_name === "string" ? payload.hook_event_name : null,
    transcriptPath:
      typeof payload.transcript_path === "string" ? payload.transcript_path : null,
    // A failure event usually has no completed response to record; it
    // carries the error instead.
    lastMessage: truncate(payload.last_assistant_message ?? payload.prompt_response),
  };

  // Tools differ on whether `error` is a bare type string with the detail in
  // `error_details`, or a single object carrying both. Accept either rather
  // than dropping the one detail a failed turn has to offer. A bare string is
  // the *type* — the values a StopFailure matcher selects on (`rate_limit`,
  // `overloaded`, …) are exactly these identifiers, not prose.
  const rawError = payload.error;
  if (typeof rawError === "string") {
    breadcrumb.error = { type: rawError, message: truncate(payload.error_details) };
  } else if (rawError && typeof rawError === "object") {
    breadcrumb.error = {
      type: typeof rawError.type === "string" ? rawError.type : null,
      message: truncate(rawError.message ?? payload.error_details),
    };
  }

  writeAtomic(join(sidecarDir, `${sessionId}.json`), JSON.stringify(breadcrumb));
}

main().catch(() => {
  // Hooks must never block or crash the session over a bookkeeping failure.
});
