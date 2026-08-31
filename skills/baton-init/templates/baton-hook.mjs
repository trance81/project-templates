#!/usr/bin/env node
// Baton 훅 — 두 지점에서만 동작한다.
//
//   1. SessionStart  세션을 시작할 때 owner 와 진행 중인 배턴을 보여준다. 아무것도 막지 않는다.
//   2. Stop          .baton/ 밖 변경이 남아 있는데 배턴이 없으면 턴 종료를 거부한다.
//
// "열린 배턴" 은 .baton/<owner>/ 최상위에 있는 status: running 또는 waiting 인 .md 파일이다.
// owner 는 .baton/local/owner 의 첫 줄에서 읽는다. 이 파일이 없으면 Stop 이 막고, SessionStart 는
// .baton/ 아래의 폴더 목록을 후보로 보여주며 사용자에게 묻게 한다. 폴더가 하나뿐이더라도 그것이
// 이 사용자의 것이라고 가정하지 않는다.
//
// Stop 은 exit 2 와 stderr 로 거부한다. Claude Code 는 exit 2 일 때의 stderr 를 모델에게 돌려준다.
// 거부가 무한히 반복되지 않도록 한 세션에서 MAX_STOP_BLOCKS 번까지만 막고, 그 뒤에는 경고만
// 남기고 통과시킨다. SessionStart 는 stdout 으로 안내를 내보내며 종료 코드는 언제나 0 이다.
//
// 판정 기준은 git 작업 트리의 변경이되, **이번 세션이 만든 변경**만 센다. SessionStart 가 그
// 시점의 변경 목록을 기준선으로 적어 두고 Stop 이 그것과 비교한다. 그래서 잡담, 지식 질의,
// 프로젝트 밖에 만드는 산출물에는 배턴을 요구하지 않고, 이전 세션이 남긴 미커밋 변경 때문에
// 파일을 건드리지 않은 턴이 거부되지도 않는다. git 저장소가 아닌 프로젝트에서는 변경을 감지할
// 수 없으므로 Stop 이 통과하고 SessionStart 의 안내만 남는다.
//
// 훅은 모델을 호출하지 않는다. 거부될 때만 모델이 한 턴을 더 쓴다.
//
// 표준 입력: Claude Code 훅 JSON (hook_event_name, cwd, session_id 등).

import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, resolve, sep } from "node:path";
import { spawnSync } from "node:child_process";

const MAX_ANCESTOR_DEPTH = 20;
const MAX_STOP_BLOCKS = 3;
const GIT_TIMEOUT_MS = 5000;
const SAFE_SESSION_ID = /^[A-Za-z0-9._-]{1,128}$/;
const RESERVED_DIRS = new Set(["local", ".session"]);

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

// .baton/ 아래에 있는 사용자 폴더 후보. local/ 과 .session/ 은 제외한다.
function ownerCandidates(root) {
  try {
    return readdirSync(join(root, ".baton"), { withFileTypes: true })
      .filter((e) => e.isDirectory() && !RESERVED_DIRS.has(e.name))
      .map((e) => e.name);
  } catch {
    return [];
  }
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

// 열린 배턴 목록을 [{ rel, status }] 형태로 돌려준다.
function openBatons(root, owner) {
  const dir = join(root, ".baton", owner);
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith(".md") && f !== "README.md")
    .map((f) => ({
      rel: join(".baton", owner, f).split(sep).join("/"),
      status: statusOf(join(dir, f)),
    }))
    .filter((b) => b.status === "running" || b.status === "waiting");
}

function git(args, cwd) {
  const r = spawnSync("git", args, { cwd, encoding: "utf8", timeout: GIT_TIMEOUT_MS });
  if (r.error || r.status !== 0) return null;
  return r.stdout;
}

// git 작업 트리의 변경을 .baton/ 안쪽과 바깥쪽으로 나눈다. 저장소가 아니면 null 을 돌려준다.
function changedFiles(cwd) {
  const top = git(["rev-parse", "--show-toplevel"], cwd);
  if (!top) return null; // git 저장소가 아니어서 변경을 감지할 수 없다
  const out = git(["status", "--porcelain", "--untracked-files=all"], cwd);
  if (out === null) return null;
  const all = out
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => line.slice(3).trim().replace(/^"(.*)"$/, "$1"))
    .map((p) => (p.includes(" -> ") ? p.split(" -> ")[1] : p));
  const inBaton = (p) => p === ".baton" || p.startsWith(".baton/");
  return { repo: top.trim(), outside: all.filter((p) => !inBaton(p)), baton: all.filter(inBaton) };
}

// 파일의 수정 시각(ms). 읽을 수 없으면 null.
function mtimeOf(repo, rel) {
  try {
    return statSync(join(repo, rel)).mtimeMs;
  } catch {
    return null;
  }
}

// ---------- 세션 기준선 ----------
//
// Stop 이 봐야 하는 것은 "지금 트리가 더러운가"가 아니라 "이 세션이 배턴 없이 무언가를 바꿨나"다.
// 그래서 SessionStart 가 그 시점의 변경 목록을 경로별 수정 시각과 함께 적어 두고, Stop 은 그
// 기준선과 달라진 것만 센다. 이렇게 하지 않으면 이전 세션이 남긴 미커밋 변경 때문에 파일을
// 전혀 건드리지 않은 질의응답 턴까지 거부당한다.
//
// 기준선 파일이 없으면(훅을 세션 도중에 걸었거나 다른 도구로 시작한 경우) 예전처럼 트리 전체를
// 본다. 놓치는 것보다 한 번 더 묻는 쪽이 낫기 때문이다.

function baselinePath(root, sessionId) {
  return join(root, ".baton", ".session", `${sessionId}.baseline`);
}

function readBaseline(root, sessionId) {
  try {
    return JSON.parse(readFileSync(baselinePath(root, sessionId), "utf8"));
  } catch {
    return null;
  }
}

function writeBaseline(root, sessionId, repo, outside) {
  const f = baselinePath(root, sessionId);
  // 압축(compact) 등으로 SessionStart 가 세션 도중 다시 돌 수 있다. 그때 기준선을 새로 쓰면
  // 그 전까지 이 세션이 만든 변경이 기준선에 흡수되어 없던 일이 된다. 그래서 한 번만 쓴다.
  if (existsSync(f)) return;
  const entry = {};
  for (const rel of outside) entry[rel] = mtimeOf(repo, rel);
  mkdirSync(dirname(f), { recursive: true, mode: 0o700 });
  const tmp = `${f}.tmp`;
  writeFileSync(tmp, JSON.stringify(entry), { encoding: "utf8", mode: 0o600 });
  renameSync(tmp, f);
}

// 기준선 이후에 새로 생기거나 다시 바뀐 경로만 걸러낸다.
function changesSinceBaseline(baseline, repo, outside) {
  if (!baseline) return outside; // 기준선이 없으면 트리 전체를 본다
  return outside.filter((rel) => {
    if (!(rel in baseline)) return true; // 세션 시작 뒤에 새로 생긴 변경
    const before = baseline[rel];
    const now = mtimeOf(repo, rel);
    if (before === null || now === null) return false; // 시각을 모르면 이미 있던 변경으로 본다
    return now > before;                               // 세션 시작 뒤에 또 바뀌었다
  });
}

function formatList(paths) {
  const head = paths.slice(0, 8).join(", ");
  return paths.length > 8 ? `${head} 외 ${paths.length - 8}건` : head;
}

function ownerMissingMessage(root) {
  const found = ownerCandidates(root);
  const lines = ["[baton] 이 PC 에서 쓸 배턴 사용자 이름이 정해져 있지 않습니다: .baton/local/owner 파일이 없습니다."];
  if (found.length > 0) {
    lines.push(`.baton/ 에 이미 있는 폴더: ${found.join(", ")}`);
    lines.push("이 가운데 사용자 본인의 것이 있는지 물어보고, 없으면 새 이름을 받으십시오.");
  } else {
    lines.push("사용자에게 이름을 물어보십시오.");
  }
  lines.push("받은 이름을 .baton/local/owner 에 한 줄로 적고 .baton/<이름>/ 폴더를 만드십시오.");
  lines.push("폴더가 하나뿐이더라도 그것이 이 사용자의 것이라고 가정하지 마십시오.");
  lines.push("이름이 비슷한 폴더가 여럿 있더라도 임의로 합치지 마십시오. 같은 사람이 PC 마다 다른 이름을 썼는지는 사용자만 판단할 수 있습니다.");
  lines.push(`(.baton 위치: ${root})`);
  return lines.join("\n");
}

function noOpenBatonMessage(root, owner, what) {
  return [
    `[baton] ${what}`,
    `.baton/${owner}/ 에 running 이나 waiting 상태인 배턴이 없습니다.`,
    "이 작업이 손대는 단위(.baton/README.md 에 선언된 단위)의 배턴을 먼저 찾아서 여십시오.",
    "이미 있으면 그 파일을 running 으로 되돌린 뒤 수정 이력을 읽고 이어서 쓰고, 없으면 단위 식별자로 새로 만드십시오.",
    "커밋 메시지를 남겼다고 해서 배턴을 대신하지는 않습니다.",
    `(.baton 위치: ${root})`,
  ].join("\n");
}

// Stop 을 몇 번 막았는지 센다. 세션마다 파일 하나를 쓰며 무한 반복을 막는 데에만 쓴다.
function bumpBlockCount(root, sessionId) {
  const dir = join(root, ".baton", ".session");
  mkdirSync(dir, { recursive: true, mode: 0o700 });
  const f = join(dir, `${sessionId}.guard`);
  let n = 0;
  try {
    n = parseInt(readFileSync(f, "utf8"), 10) || 0;
  } catch {}
  n += 1;
  const tmp = `${f}.tmp`;
  writeFileSync(tmp, String(n), { encoding: "utf8", mode: 0o600 });
  renameSync(tmp, f);
  return n;
}

// ---------- 각 지점 ----------

// 세션 시작 안내. 아무것도 막지 않으며, stdout 에 쓴 내용이 모델의 컨텍스트로 들어간다.
function sessionStart(root, cwd, sessionId) {
  const ch = changedFiles(cwd);
  // 이 세션이 무엇을 바꿨는지 Stop 이 판별할 수 있도록 지금의 변경 목록을 기준선으로 남긴다.
  if (ch) writeBaseline(root, sessionId, ch.repo, ch.outside);

  const owner = readOwner(root);
  if (!owner) {
    process.stdout.write(ownerMissingMessage(root) + "\n");
    return;
  }

  const open = openBatons(root, owner);
  const lines = [`[baton] owner: ${owner}`];

  if (open.length > 0) {
    lines.push(`진행 중인 배턴이 ${open.length}건 있습니다. 새 작업을 시작하기 전에 먼저 읽고 정리하십시오.`);
    for (const b of open) lines.push(`  - ${b.rel} (${b.status})`);
  } else {
    lines.push("진행 중인 배턴이 없습니다.");
    if (ch && ch.outside.length > 0) {
      lines.push(`다만 커밋되지 않은 변경이 남아 있습니다: ${formatList(ch.outside)}`);
      lines.push("이전 세션이 배턴 없이 끝났을 수 있습니다. 무엇을 하던 중이었는지 확인하고 해당 단위의 배턴부터 정리하십시오.");
      lines.push("이 변경들은 이번 세션이 만든 것이 아니므로 턴 종료를 막지는 않습니다.");
    }
  }
  lines.push("다른 사람의 폴더는 사용자가 지시할 때에만 엽니다.");
  process.stdout.write(lines.join("\n") + "\n");
}

function guardStop(root, sessionId, cwd) {
  const ch = changedFiles(cwd);
  if (!ch || ch.outside.length === 0) return 0; // 변경이 없거나 git 저장소가 아니다
  // 이번 세션이 새로 만들거나 다시 건드린 변경만 센다. 이전 세션이 남긴 미커밋 변경 때문에
  // 파일을 건드리지 않은 턴이 거부되면 안 된다.
  const mine = changesSinceBaseline(readBaseline(root, sessionId), ch.repo, ch.outside);
  if (mine.length === 0) return 0;
  const owner = readOwner(root);
  if (owner) {
    // 열린 배턴이 있거나, 이 변경과 함께 내 배턴 파일이 바뀌어 있으면(수정 이력을 남기고 닫은
    // 경우에 해당한다) 기록된 것으로 본다.
    if (openBatons(root, owner).length > 0) return 0;
    const myBatons = ch.baton.filter((p) => p.startsWith(`.baton/${owner}/`) && p.endsWith(".md"));
    if (myBatons.length > 0) return 0;
  }

  const n = bumpBlockCount(root, sessionId);
  const msg = owner
    ? noOpenBatonMessage(root, owner, `이번 세션이 바꾼 파일이 있는데 배턴이 없습니다: ${formatList(mine)}`)
    : `${ownerMissingMessage(root)}\n이번 세션이 바꾼 파일: ${formatList(mine)}`;
  if (n > MAX_STOP_BLOCKS) {
    // 여기서 더 막으면 무한 반복에 빠질 수 있으므로 경고만 남기고 통과시킨다.
    process.stderr.write(`[baton] ${MAX_STOP_BLOCKS}회 거부한 뒤이므로 통과시킵니다. 배턴을 여십시오.\n`);
    return 0;
  }
  process.stderr.write(`${msg}\n(이 세션에서 ${n}/${MAX_STOP_BLOCKS}번째 거부입니다)`);
  return 2;
}

// ---------- 진입 ----------

function readStdin() {
  return new Promise((done) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (data += c));
    process.stdin.on("end", () => done(data));
    setTimeout(() => done(data), 2000).unref();
  });
}

async function main() {
  let payload;
  try {
    payload = JSON.parse(await readStdin());
  } catch {
    return; // 입력이 이상하면 조용히 통과시킨다. 훅이 세션을 깨뜨리면 안 된다.
  }
  const cwd = typeof payload.cwd === "string" ? payload.cwd : process.cwd();
  const root = findBatonRoot(cwd);
  if (!root) return; // .baton 이 없으므로 관할 밖이다

  const sessionId = payload.session_id;
  const okId = typeof sessionId === "string" && SAFE_SESSION_ID.test(sessionId);
  const sid = okId ? sessionId : "unknown";

  if (payload.hook_event_name === "SessionStart") {
    sessionStart(root, cwd, sid);
    return;
  }
  if (payload.hook_event_name === "Stop") {
    process.exitCode = guardStop(root, sid, cwd);
  }
}

main().catch(() => {
  // 훅 자체에서 난 오류로 세션을 막지는 않는다. 거부는 위에서 명시적으로만 한다.
});
