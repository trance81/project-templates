#!/usr/bin/env bash
# project-templates 전역 세팅 (macOS/Linux)
# ~/.claude/CLAUDE.md 에 표준 참조 블록을 추가한다. 이미 있으면 건너뛴다.
set -euo pipefail

REPO_PATH="$(cd "$(dirname "$0")" && pwd)"
GLOBAL_MD="$HOME/.claude/CLAUDE.md"
MARKER="## 프로젝트 지식관리 표준 (project-templates)"

mkdir -p "$HOME/.claude"
if [ -f "$GLOBAL_MD" ] && grep -qF "$MARKER" "$GLOBAL_MD"; then
  echo "이미 등록됨: $GLOBAL_MD"
else
  cat >> "$GLOBAL_MD" <<EOF

$MARKER
- 정본: https://github.com/trance81/project-templates.git (로컬: $REPO_PATH)
- 새 프로젝트 시작, 기존 프로젝트 분석/개발 시 STRUCTURE.md의 pjt-docs/ 구조로 지식을 구성·유지할 것
- 프로젝트에 pjt-docs/가 없으면 도입을 제안할 것
- ~/.claude/pjt-templates-skills-state.json 이 없으면(스킬 동기화를 한 번도 안 돌린 PC) global-skills/sync 실행을 먼저 안내할 것
EOF
  echo "등록 완료: $GLOBAL_MD"
fi
echo ""
echo "Cursor는 수동 등록 필요 — SETUP.md의 Cursor 절 참조 (Settings > Rules > User Rules)"
