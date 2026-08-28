#!/usr/bin/env node
// Baton 강제 훅 — 배턴 없이 프로젝트가 바뀌는 것을 세 지점에서 막는다.
//
//   1. PreToolUse (Edit/Write/MultiEdit, 쓰기 형태의 Bash)  열린 배턴이 없으면 파일 편집을 거부
//   2. Stop                                 git 변경이 남아 있는데 열린 배턴도, 함께 바뀐 내 배턴도 없으면 턴 종료를 거부
//   3. pre-commit (node baton-hook.mjs --pre-commit)
//                                           .baton/ 밖 파일을 커밋하는데 배턴이 함께 없으면 커밋 거부
//
// "열린 배턴" = .baton/<owner>/ 최상위의 status: running | waiting 인 .md 파일.
// owner 는 .baton/local/owner 한 줄. 없으면 세 지점 모두 막는다 — 누구 폴더인지 모르면
// 배턴을 찾을 수 없기 때문이다. 이름을 묻고 파일을 만들면 풀린다.
//
// 1·2 는 exit 2 + stderr 로 거부한다. Claude Code 는 exit 2 의 stderr 를 모델에게 돌려준다.
// Stop 은 무한 반복을 막기 위해 세션당 MAX_STOP_BLOCKS 번까지만 막고, 그 뒤엔 경고만 남기고
// 통과시킨다. 3 은 exit 1 로 git 이 커밋을 거부한다.
//
// Stop/StopFailure 에서는 예전처럼 .baton/.session/<session>.json 브레드크럼도 남긴다.
// 훅은 모델을 호출하지 않는다. 거부될 때만 모델이 한 턴 더 쓴다.
//
// 표준 입력: Claude Code 훅 JSON (hook_event_name, tool_name, tool_input, cwd, session_id,
// transcript_path, last_assistant_message, stop_hook_active, error ...).

import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { spawnSync } from "node:child_process";
import { StringDecoder } from "node:string_decoder";

const MAX_ANCESTOR_DEPTH = 20;
const MAX_MESSAGE_BYTES = 4096;
const MAX_STOP_BLOCKS = 3;
const GIT_TIMEOUT_MS = 5000;
const SAFE_SESSION_ID = /^[A-Za-z0-9._-]{1,128}$/;
const EDIT_TOOLS = new Set(["Edit", "Write", "MultiEdit", "NotebookEdit"]);
// Bash 명령에서 파일을 바꾸는 흔한 형태. 완전한 판별은 불가능하고, /dev/null 리다이렉트는 제외한다.
// 셸로 우회한 나머지는 Stop 과 pre-commit 이 잡는다.
const BASH_WRITE_PATTERNS = [
  /(^|[^<>])>>?\s*(?!\/dev\/null)[^\s|&;]/,   // > file, >> file (/dev/null 제외)
  /\bsed\s+(-[a-zA-Z]*i|--in-place)/,          // sed -i
  /\btee\s+(?!\/dev\/null)/,                   // tee file
  /\b(mv|cp|rm|rmdir|truncate|install)\s/,     // 이동·복사·삭제
  /\b(git\s+(checkout|restore|reset|stash|apply|am|cherry-pick|merge|rebase|revert))\b/, // 작업 트리를 바꾸는 git
];
function looksLikeWrite(cmd) {
  return BASH_WRITE_PATTERNS.some((re) => re.test(cmd));
}

// ---------- 공통 ----------

function findBatonRoot(startDir) {
  let dir = resolve(startDir);
  for (let i = 0; i < MAX_ANCESTOR_DEPTH; i++) {
    if (existsSync(join(dir, ".baton"))) return dir;
    const parent = dirname(dir);
    if (parent === dir) return null;
    dir = parent;
  }
  return null;
}

function readOwner(root) {
  const f = join(root, ".baton", "local", "owner");
  if (!existsSync(f)) return null;
  const name = readFileSync(f, "utf8").split(/\r?\n/)[0].trim();
  return name || null;
}

function statusOf(file) {
  let head;
  try {
    head = readFileSync(file, "utf8").slice(0, 2048);
  } catch {
    return null;
  }
  const m = /^---\s*\r?\n([\s\S]*?)\r?\n---/.exec(head);
  if (!m) return null;
  const s = /^status:\s*([A-Za-z-]+)/m.exec(m[1]);
  return s ? s[1].toLowerCase() : null;
}

function openBatons(root, owner) {
  const dir = join(root, ".baton", owner);
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith(".md") && f !== "README.md")
    .filter((f) => ["running", "waiting"].includes(statusOf(join(dir, f))))
    .map((f) => join(".baton", owner, f).split(sep).join("/"));
}

function isInsideBaton(root, filePath) {
  const rel = relative(root, resolve(filePath));
  if (rel.startsWith("..") || isAbsolute(rel)) return null; // 프로젝트 밖
  return rel === ".baton" || rel.startsWith(".baton" + sep) || rel.startsWith(".baton/");
}

function git(args, cwd) {
  const r = spawnSync("git", args, { cwd, encoding: "utf8", timeout: GIT_TIMEOUT_MS });
  if (r.error || r.status !== 0) return null;
  return r.stdout;
}

// git 작업 트리의 변경을 .baton/ 안팎으로 나눈다. 저장소가 아니면 null.
function changedFiles(cwd) {
  const top = git(["rev-parse", "--show-toplevel"], cwd);
  if (!top) return null; // git 저장소 아님 — 변경 감지 불가
  const out = git(["status", "--porcelain", "--untracked-files=all"], cwd);
  if (out === null) return null;
  const all = out
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => line.slice(3).trim().replace(/^"(.*)"$/, "$1"))
    .map((p) => (p.includes(" -> ") ? p.split(" -> ")[1] : p));
  const inBaton = (p) => p === ".baton" || p.startsWith(".baton/");
  return { outside: all.filter((p) => !inBaton(p)), baton: all.filter(inBaton) };
}

function ownerMissingMessage(root) {
  return [
    "[baton] 이 PC 의 배턴 사용자 이름이 없습니다: .baton/local/owner 파일이 없습니다.",
    "사용자에게 이름을 물어 그 파일에 한 줄로 적고 .baton/<이름>/ 폴더를 만드십시오.",
    "폴더가 하나뿐이어도 그것이 이 사용자의 것이라고 가정하지 마십시오.",
    `(.baton 위치: ${root})`,
  ].join("\n");
}

function noOpenBatonMessage(root, owner, what) {
  return [
    `[baton] ${what}`,
    `.baton/${owner}/ 에 running 또는 waiting 상태의 배턴이 없습니다.`,
    "먼저 이 작업이 손대는 단위(.baton/README.md 에 선언된 단위)의 배턴을 찾아 여십시오.",
    "있으면 그 파일을 running 으로 되돌려 수정 이력을 읽고 이어 쓰고, 없으면 단위 식별자로 새로 만드십시오.",
    "CHANGELOG 나 커밋 메시지는 배턴을 대신하지 않습니다.",
    `(.baton 위치: ${root})`,
  ].join("\n");
}

// ---------- 브레드크럼 (Stop / StopFailure) ----------

function truncate(text) {
  if (typeof text !== "string") return null;
  const buf = Buffer.from(text, "utf8");
  if (buf.length <= MAX_MESSAGE_BYTES) return text;
  const decoder = new StringDecoder("utf8");
  return `${decoder.write(buf.subarray(0, MAX_MESSAGE_BYTES))}…`;
}

function writeAtomic(path, contents) {
  const tmp = `${path}.tmp`;
  writeFileSync(tmp, contents, { encoding: "utf8", mode: 0o600 });
  renameSync(tmp, path);
}

function writeBreadcrumb(root, payload, sessionId) {
  const dir = join(root, ".baton", ".session");
  mkdirSync(dir, { recursive: true, mode: 0o700 });
  const crumb = {
    observedAt: new Date().toISOString(),
    event: typeof payload.hook_event_name === "string" ? payload.hook_event_name : null,
    transcriptPath: typeof payload.transcript_path === "string" ? payload.transcript_path : null,
    lastMessage: truncate(payload.last_assistant_message ?? payload.prompt_response),
  };
  const rawError = payload.error;
  if (typeof rawError === "string") {
    crumb.error = { type: rawError, message: truncate(payload.error_details) };
  } else if (rawError && typeof rawError === "object") {
    crumb.error = {
      type: typeof rawError.type === "string" ? rawError.type : null,
      message: truncate(rawError.message ?? payload.error_details),
    };
  }
  writeAtomic(join(dir, `${sessionId}.json`), JSON.stringify(crumb));
}

// Stop 차단 횟수. 세션별 파일 하나. 무한 반복 방지용.
function bumpBlockCount(root, sessionId) {
  const dir = join(root, ".baton", ".session");
  mkdirSync(dir, { recursive: true, mode: 0o700 });
  const f = join(dir, `${sessionId}.guard`);
  let n = 0;
  try {
    n = parseInt(readFileSync(f, "utf8"), 10) || 0;
  } catch {}
  n += 1;
  writeAtomic(f, String(n));
  return n;
}

// ---------- 각 지점 ----------

function guardPreToolUse(payload, root) {
  if (payload.tool_name === "Bash") {
    const cmd = payload.tool_input?.command;
    if (typeof cmd !== "string" || !looksLikeWrite(cmd)) return 0;
    const owner = readOwner(root);
    if (!owner) {
      process.stderr.write(ownerMissingMessage(root));
      return 2;
    }
    if (openBatons(root, owner).length > 0) return 0;
    process.stderr.write(
      noOpenBatonMessage(root, owner, "열린 배턴 없이 파일을 바꾸는 셸 명령을 실행할 수 없습니다: " + cmd.slice(0, 120)),
    );
    return 2;
  }
  if (!EDIT_TOOLS.has(payload.tool_name)) return 0;
  const target = payload.tool_input?.file_path ?? payload.tool_input?.notebook_path;
  if (typeof target !== "string") return 0;
  const inside = isInsideBaton(root, target);
  if (inside === null || inside === true) return 0; // 프로젝트 밖이거나 .baton/ 안 — 통과
  const owner = readOwner(root);
  if (!owner) {
    process.stderr.write(ownerMissingMessage(root));
    return 2;
  }
  if (openBatons(root, owner).length > 0) return 0;
  const rel = relative(root, resolve(target)).split(sep).join("/");
  process.stderr.write(noOpenBatonMessage(root, owner, `열린 배턴 없이 파일을 바꿀 수 없습니다: ${rel}`));
  return 2;
}

function guardStop(payload, root, sessionId, cwd) {
  const ch = changedFiles(cwd);
  if (!ch || ch.outside.length === 0) return 0; // 변경 없음 또는 감지 불가
  const changed = ch.outside;
  const owner = readOwner(root);
  if (owner) {
    // 열린 배턴이 있거나, 내 배턴 파일이 이 변경과 함께 바뀌어 있으면(이력을 남기고 닫은
    // 경우) 기록된 것으로 본다. pre-commit 과 같은 기준이다.
    if (openBatons(root, owner).length > 0) return 0;
    const mine = ch.baton.filter((p) => p.startsWith(`.baton/${owner}/`) && p.endsWith(".md"));
    if (mine.length > 0) return 0;
  }

  const n = bumpBlockCount(root, sessionId);
  const list = changed.slice(0, 8).join(", ") + (changed.length > 8 ? ` 외 ${changed.length - 8}건` : "");
  const msg = owner
    ? noOpenBatonMessage(root, owner, `변경된 파일이 있는데 배턴이 없습니다: ${list}`)
    : ownerMissingMessage(root) + `\n변경된 파일: ${list}`;
  if (n > MAX_STOP_BLOCKS) {
    // 더 막으면 무한 반복 위험. 경고만 남기고 통과시킨다. 커밋 시점에 pre-commit 이 한 번 더 막는다.
    process.stderr.write(`[baton] ${MAX_STOP_BLOCKS}회 거부 후 통과시킵니다. 커밋 전까지 배턴을 여십시오.\n`);
    return 0;
  }
  process.stderr.write(msg + `\n(이 세션에서 ${n}/${MAX_STOP_BLOCKS}번째 거부)`);
  return 2;
}

function preCommit(cwd) {
  const top = git(["rev-parse", "--show-toplevel"], cwd);
  if (!top) return 0;
  const repo = top.trim();
  const root = findBatonRoot(repo);
  if (!root) return 0; // 이 저장소 위로 .baton 이 없으면 관할 밖
  const out = git(["diff", "--cached", "--name-only", "--diff-filter=ACMRD"], repo) ?? "";
  const staged = out.split(/\r?\n/).filter(Boolean);
  if (staged.length === 0) return 0;

  const batonInThisRepo = resolve(root) === resolve(repo);
  const outside = staged.filter((p) => !(p === ".baton" || p.startsWith(".baton/")));
  if (outside.length === 0) return 0; // 배턴만 커밋 — 통과

  const owner = readOwner(root);
  if (!owner) {
    process.stderr.write(ownerMissingMessage(root) + "\n");
    return 1;
  }
  if (batonInThisRepo) {
    // 같은 저장소: 이 커밋에 내 배턴이 함께 스테이징되어야 한다.
    const mine = staged.filter((p) => p.startsWith(`.baton/${owner}/`) && p.endsWith(".md"));
    if (mine.length > 0) return 0;
    process.stderr.write(
      [
        `[baton] 커밋 거부: .baton/${owner}/ 의 배턴이 이 커밋에 없습니다.`,
        `바뀐 파일: ${outside.slice(0, 8).join(", ")}${outside.length > 8 ? " …" : ""}`,
        "해당 단위의 배턴에 수정 이력 항목을 남기고 함께 스테이징하십시오.",
        "문서 변경(pjt-docs/)도 배턴이 필요합니다. CHANGELOG 는 배턴을 대신하지 않습니다.",
        "우회는 git commit --no-verify 뿐이며, 그것은 의도적 결정이어야 합니다.",
      ].join("\n") + "\n",
    );
    return 1;
  }
  // 다른 저장소(그룹 루트 구성): 같은 커밋에 넣을 수 없으니 열린 배턴이 있는지만 본다.
  if (openBatons(root, owner).length > 0) return 0;
  process.stderr.write(noOpenBatonMessage(root, owner, "커밋 거부: 열린 배턴이 없습니다.") + "\n");
  return 1;
}

// ---------- 진입 ----------

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => resolve(data), 2000).unref();
  });
}

async function main() {
  if (process.argv.includes("--pre-commit")) {
    process.exitCode = preCommit(process.cwd());
    return;
  }

  let payload;
  try {
    payload = JSON.parse(await readStdin());
  } catch {
    return; // 입력이 이상하면 조용히 통과. 훅이 세션을 깨면 안 된다.
  }
  const cwd = typeof payload.cwd === "string" ? payload.cwd : process.cwd();
  const root = findBatonRoot(cwd);
  if (!root) return; // .baton 없음 — 관할 밖
  const event = payload.hook_event_name;

  if (event === "PreToolUse") {
    process.exitCode = guardPreToolUse(payload, root);
    return;
  }

  const sessionId = payload.session_id;
  const okId = typeof sessionId === "string" && SAFE_SESSION_ID.test(sessionId);
  if (event === "Stop" || event === "StopFailure") {
    if (okId) writeBreadcrumb(root, payload, sessionId);
    if (event === "Stop") {
      process.exitCode = guardStop(payload, root, okId ? sessionId : "unknown", cwd);
    }
  }
}

main().catch(() => {
  // 훅 자체의 오류로 세션을 막지 않는다. 거부는 위에서 명시적으로만 한다.
});
