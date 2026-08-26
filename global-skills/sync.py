#!/usr/bin/env python3
"""전역 플러그인/스킬 동기화 — manifest.json vs 로컬 상태 diff 후 신규 항목만 확인받아 설치.
sync.sh 가 호출한다. 인자: <manifest.json> <state.json> [옵션...]

  (없음)       아직 설치 여부를 정하지 않은 항목만 물어보고 설치한다.
  --review     과거에 "건너뜀"으로 결정한 항목도 다시 물어본다.
  --update     설치를 새로 하지 않고, 이미 설치된 것을 최신으로 갱신한다.
  --yes        묻지 않고 전부 y 로 답한다. 터미널이 아닌 곳에서 돌릴 때 쓴다.
  --list       아무것도 설치하지 않고, 물어볼 항목만 출력한다.
  --only a,b   지정한 id 만 묻지 않고 설치한다. --list 로 목록을 뽑아
               사용자에게 고르게 한 뒤 그 답을 그대로 넘기는 용도다.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 — desc 의 한글·em dash 출력 대비

manifest_path, state_path = sys.argv[1], sys.argv[2]
flags = sys.argv[3:]
review = "--review" in flags
update = "--update" in flags
assume_yes = "--yes" in flags
list_only = "--list" in flags

only = None
for f in flags:
    if f.startswith("--only"):
        raw = f.split("=", 1)[1] if "=" in f else flags[flags.index(f) + 1]
        only = {x.strip() for x in raw.split(",") if x.strip()}
if only is not None:
    assume_yes = True   # 고를 항목을 이미 받았으니 다시 묻지 않는다

NOT_INTERACTIVE = (
    "입력이 터미널이 아니어서 y/N 을 물어볼 수 없다. 아무것도 바꾸지 않고 끝낸다.\n"
    "실제 터미널에서 실행하거나, 전부 설치할 생각이면 --yes 를 붙여라."
)

# 이 스크립트는 항목마다 y/N 을 물어본다. 입력이 터미널이 아니면 답을 받을 수 없는데, 그대로 두면
# EOF 를 "아니오"로 읽어 묻지도 않은 항목을 skipped 로 기록해 버린다. 그런 결정이 상태 파일에
# 남으면 다음 실행 때 다시 묻지 않으므로 미리 막는다.
if not sys.stdin.isatty() and not (assume_yes or list_only):
    print(NOT_INTERACTIVE)
    sys.exit(2)


def prompt(text):
    """y/N 을 받는다. Windows 에서는 리다이렉트를 isatty 로 못 걸러내는 경우가 있어
    (예: NUL 을 stdin 으로 주면 문자 장치라 isatty 가 True 다) EOF 도 함께 막는다."""
    try:
        return input(text).strip().lower() == "y"
    except EOFError:
        print(f"\n{NOT_INTERACTIVE}")
        sys.exit(2)

home = Path.home()
manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
state = json.loads(Path(state_path).read_text(encoding="utf-8")) if Path(state_path).exists() else {}


def save():
    Path(state_path).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def already_installed(kind, key):
    if kind == "marketplace":
        f = home / ".claude/plugins/known_marketplaces.json"
        if f.exists():
            return key in json.loads(f.read_text(encoding="utf-8"))
    elif kind == "plugin":
        f = home / ".claude/plugins/installed_plugins.json"
        if f.exists():
            return key in json.loads(f.read_text(encoding="utf-8")).get("plugins", {})
    elif kind == "skill":
        return (home / ".claude/skills" / key).exists()
    return False


def pending(kind, item_id, state_key):
    """아직 설치도 안 됐고 결정도 안 난 항목인가. 물어볼 대상인지 판단한다."""
    if already_installed(kind, item_id):
        return False
    return state_key not in state or review


def ask(state_key, desc, item_id=None):
    if state_key in state and not review:
        return None
    if only is not None and item_id not in only:
        return None   # 고르지 않은 항목은 결정도 남기지 않는다
    print(f"\n[{state_key}]\n  {desc}")
    if assume_yes:
        print("  설치할까? (y/N) y")
        return True
    return prompt("  설치할까? (y/N) ")


def run(cmd):
    # 홈에서 실행한다. `npx skills add` 류는 전역 플래그가 빠지면 현재 폴더에 설치하는데,
    # 리포 안에서 sync 를 돌리는 게 보통이라 그대로 두면 리포를 오염시킨다.
    subprocess.run(cmd, shell=True, check=True, cwd=home)


def verify_skill(skill_id):
    """설치 명령이 성공했다고 해서 전역에 들어갔다는 보장이 없다. 실제로 확인한다."""
    if not (home / ".claude/skills" / skill_id).exists():
        raise RuntimeError(
            f"명령은 끝났지만 ~/.claude/skills/{skill_id} 가 없다. "
            "설치 명령에 전역 플래그(-g)가 빠졌을 수 있다"
        )


failures = []


def install(key, action):
    """action 을 실행하고 결과를 state 에 남긴다. 실패해도 sync 전체를 멈추지 않는다."""
    try:
        action()
        state[key] = "installed"
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        failures.append(key)
        state.pop(key, None)   # 결정을 남기지 않아 재실행 시 다시 묻는다
    save()


# path 는 manifest.json 이 있는 global-skills/ 기준 상대경로다.
skills_base = Path(manifest_path).resolve().parent


# 실행 중 저절로 생기는 것들. 대조에서 빼지 않으면 갱신할 게 없는데도 매번 "다르다"고 나온다.
IGNORED_DIRS = {"__pycache__", ".git", "node_modules", ".venv"}
IGNORED_NAMES = {".DS_Store", "Thumbs.db"}


def tree_hash(root):
    """폴더 안 모든 파일의 상대경로와 내용을 합쳐 해시한다. 내용이 같으면 같은 값이 나온다."""
    root = Path(root)
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if set(rel.parts) & IGNORED_DIRS or rel.name in IGNORED_NAMES or rel.suffix == ".pyc":
            continue
        h.update(rel.as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def confirm(text):
    if assume_yes:
        print(f"  {text} (y/N) y  [--yes]")
        return True
    return prompt(f"  {text} (y/N) ")


if list_only:
    # 아무것도 바꾸지 않고, 물어볼 항목만 보여준다. AI 가 이 목록을 사용자에게 제시하고
    # 답을 받아 --only 로 되돌려주는 흐름을 염두에 둔 출력이다.
    groups = [
        ("마켓플레이스", "marketplace", manifest.get("marketplaces", [])),
        ("플러그인", "plugin", manifest.get("plugins", [])),
        ("스킬", "skill", manifest.get("skills", [])),
    ]
    total = 0
    for label, kind, items in groups:
        rows = [i for i in items if pending(kind, i["id"], f"{kind}:{i['id']}")]
        if not rows:
            continue
        print(f"\n[{label}]")
        for i in rows:
            print(f"  {i['id']}\n      {i['desc']}")
        total += len(rows)
    if total == 0:
        print("설치할 새 항목이 없다. 전부 설치됐거나 이미 결정된 상태다.")
    else:
        print(f"\n총 {total}건. 설치하려면 --only 에 id 를 쉼표로 이어 넘긴다.")
        print("예: --only baton-init,hallmark")
    sys.exit(0)


if update:
    print("설치는 하지 않고, 이미 설치된 것만 갱신한다.\n")

    print("2) 마켓플레이스 갱신")
    if any(already_installed("marketplace", m["id"]) for m in manifest.get("marketplaces", [])):
        install("update:marketplaces", lambda: run("claude plugin marketplace update"))
    else:
        print("  설치된 마켓플레이스 없음")

    print("\n3) 플러그인 갱신")
    targets = [p for p in manifest.get("plugins", []) if already_installed("plugin", p["id"])]
    if not targets:
        print("  설치된 플러그인 없음")
    for p in targets:
        print(f"  {p['id']}")
        install(f"update:plugin:{p['id']}", lambda p=p: run(f"claude plugin update {p['id']}"))

    print("\n4) 스킬 갱신")
    for s in manifest.get("skills", []):
        dest = home / ".claude/skills" / s["id"]
        if not dest.exists():
            continue   # 설치 안 된 것은 갱신 대상이 아니다. 설치하려면 플래그 없이 실행한다.

        if s.get("installCmd"):
            # 정본이 외부에 있어 내용을 대조할 수 없다. 재실행 여부를 사용자에게 맡긴다.
            print(f"\n[{s['id']}] 외부 스킬이라 최신 여부를 대조할 수 없다")
            print(f"  설치 명령: {s['installCmd']}")
            if confirm("설치 명령을 다시 실행할까?"):
                def rerun(s=s):
                    run(s["installCmd"])
                    verify_skill(s["id"])

                install(f"update:skill:{s['id']}", rerun)
            continue

        src = skills_base / s["path"]
        if not src.is_dir():
            print(f"\n[{s['id']}] ❌ 리포에 소스 폴더 없음: {src}")
            failures.append(f"update:skill:{s['id']}")
            continue
        if tree_hash(src) == tree_hash(dest):
            print(f"  {s['id']}: 최신")
            continue

        # 내용이 다를 때만 묻는다. 로컬에서 손댄 내용을 말없이 덮어쓰지 않기 위해서다.
        print(f"\n[{s['id']}] 리포 내용과 다르다")
        print(f"  {dest} 를 리포 내용으로 교체한다. 로컬에서 고친 부분이 있으면 사라진다.")
        if not confirm("교체할까?"):
            print("  건너뜀")
            continue

        def replace(src=src, dest=dest):
            shutil.rmtree(dest)
            shutil.copytree(src, dest)

        install(f"update:skill:{s['id']}", replace)

    save()
    if failures:
        print(f"\n⚠️  실패 {len(failures)}건: {', '.join(failures)}")
    print("\n갱신 완료. 플러그인 갱신은 Claude Code 재시작 후 반영된다.")
    sys.exit(1 if failures else 0)


print("2) 마켓플레이스 확인")
for m in manifest.get("marketplaces", []):
    key = f"marketplace:{m['id']}"
    if already_installed("marketplace", m["id"]):
        state[key] = "installed(기존)"
        continue
    want = ask(key, m["desc"], m["id"])
    if want is None:
        continue
    if want:
        src = m["repo"] if m["type"] == "github" else m["url"]
        install(key, lambda src=src: run(f"claude plugin marketplace add {src}"))
    else:
        state[key] = "skipped"
        save()

print("\n3) 플러그인 확인")
for p in manifest.get("plugins", []):
    key = f"plugin:{p['id']}"
    if already_installed("plugin", p["id"]):
        state[key] = "installed(기존)"
        continue
    want = ask(key, p["desc"], p["id"])
    if want is None:
        continue
    if want:
        install(key, lambda p=p: run(f"claude plugin install {p['id']}"))
    else:
        state[key] = "skipped"
        save()

print("\n4) 스킬 확인 (installCmd 로 설치하거나, 이 리포에서 복사)")
for s in manifest.get("skills", []):
    key = f"skill:{s['id']}"
    if already_installed("skill", s["id"]):
        state[key] = "installed(기존)"
        continue
    want = ask(key, s["desc"], s["id"])
    if want is None:
        continue
    if not want:
        state[key] = "skipped"
        save()
        continue

    def do(s=s):
        if s.get("installCmd"):
            run(s["installCmd"])
        else:
            src = skills_base / s["path"]
            if not src.is_dir():
                raise FileNotFoundError(f"리포에 소스 폴더 없음: {src}")
            shutil.copytree(src, home / ".claude/skills" / s["id"])
        verify_skill(s["id"])

    install(key, do)

save()
if failures:
    print(f"\n⚠️  실패 {len(failures)}건: {', '.join(failures)} — 재실행하면 다시 물어본다")
print(f"\n완료. 상태 기록: {state_path}")
print("건너뛴 항목을 다시 검토하려면: ./sync.sh --review")
