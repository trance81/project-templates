#!/usr/bin/env bash
# 전역 플러그인/스킬 동기화 (macOS/Linux)
# manifest.json 과 로컬 상태를 비교해, 아직 결정 안 한 항목만 하나씩 물어보고 설치한다.
# 리포가 갱신된 뒤 재실행하면 새로 추가된 항목만 새로 물어본다(기존 결정은 재사용).
# 옵션: --review  과거 "건너뜀" 항목도 다시 물어본다
#       --update  설치는 하지 않고, 이미 설치된 것을 리포 최신 내용으로 갱신한다
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$REPO_ROOT/global-skills/manifest.json"
STATE_PATH="$HOME/.claude/pjt-templates-skills-state.json"
MODE="${1:-}"

PY="$(command -v python3 || command -v python || true)"
[ -n "$PY" ] || { echo "python3 가 필요합니다."; exit 1; }

# 정본은 이 git 리포다. 대조·갱신 전에 먼저 최신으로 맞춘다.
echo "1) 리포 최신화 ($REPO_ROOT)"
( cd "$REPO_ROOT" && git pull --ff-only ) || echo "  경고: git pull 실패 — 로컬 내용으로 계속 진행"

mkdir -p "$(dirname "$STATE_PATH")"
[ -f "$STATE_PATH" ] || echo '{}' > "$STATE_PATH"

"$PY" "$REPO_ROOT/global-skills/sync.py" "$MANIFEST" "$STATE_PATH" "$MODE"
