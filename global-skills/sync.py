#!/usr/bin/env python3
"""전역 플러그인/스킬 동기화 — manifest.json vs 로컬 상태 diff 후 신규 항목만 확인받아 설치.
sync.sh 가 호출한다. 인자: <manifest.json> <state.json> [--review|--update]

  (없음)     아직 설치 여부를 정하지 않은 항목만 물어보고 설치한다.
  --review   과거에 "건너뜀"으로 결정한 항목도 다시 물어본다.
  --update   설치를 새로 하지 않고, 이미 설치된 것을 최신으로 갱신한다.
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
mode = sys.argv[3] if len(sys.argv) > 3 else ""
review = mode == "--review"
update = mode == "--update"

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


def ask(state_key, desc):
    if state_key in state and not review:
        return None
    print(f"\n[{state_key}]\n  {desc}")
    ans = input("  설치할까? (y/N) ").strip().lower()
    return ans == "y"


def run(cmd):
    subprocess.run(cmd, shell=True, check=True)


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


def tree_hash(root):
    """폴더 안 모든 파일의 상대경로와 내용을 합쳐 해시한다. 내용이 같으면 같은 값이 나온다."""
    h = hashlib.sha256()
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def confirm(prompt):
    return input(f"  {prompt} (y/N) ").strip().lower() == "y"


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
                install(f"update:skill:{s['id']}", lambda s=s: run(s["installCmd"]))
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
    want = ask(key, m["desc"])
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
    want = ask(key, p["desc"])
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
    want = ask(key, s["desc"])
    if want is None:
        continue
    if not want:
        state[key] = "skipped"
        save()
        continue

    def do(s=s):
        if s.get("installCmd"):
            run(s["installCmd"])
            return
        src = skills_base / s["path"]
        if not src.is_dir():
            raise FileNotFoundError(f"리포에 소스 폴더 없음: {src}")
        shutil.copytree(src, home / ".claude/skills" / s["id"])

    install(key, do)

save()
if failures:
    print(f"\n⚠️  실패 {len(failures)}건: {', '.join(failures)} — 재실행하면 다시 물어본다")
print(f"\n완료. 상태 기록: {state_path}")
print("건너뛴 항목을 다시 검토하려면: ./sync.sh --review")
