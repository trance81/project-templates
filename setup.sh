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
- 프로젝트 pjt-docs/README.md 상단의 \`표준 갱신일\`이 STRUCTURE.md의 값보다 오래됐거나 아예 없으면 update.md 절차로 갱신을 제안할 것
EOF
  echo "등록 완료: $GLOBAL_MD"
fi
# baton-init 스킬을 ~/.claude/skills/ 로 복사한다. 내용이 같으면 건너뛴다.
SKILL_SRC="$REPO_PATH/skills/baton-init"
SKILL_DST="$HOME/.claude/skills/baton-init"
if [ -d "$SKILL_SRC" ]; then
  if [ -d "$SKILL_DST" ] && diff -r -q "$SKILL_SRC" "$SKILL_DST" >/dev/null 2>&1; then
    echo "스킬 최신: $SKILL_DST"
  else
    mkdir -p "$HOME/.claude/skills"
    rm -rf "$SKILL_DST"
    cp -R "$SKILL_SRC" "$SKILL_DST"
    echo "스킬 설치: $SKILL_DST"
  fi
fi
