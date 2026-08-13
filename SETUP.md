# 전역 세팅 가이드

새 PC나 새 AI 도구에 이 리포를 "구성 기초"로 등록하는 절차. 이걸 마치면 어떤 프로젝트에서 작업하든 AI가 pjt-docs 구조를 자동 인지하고 유지한다.

## 자동 (권장)

리포 클론 후 스크립트 실행:

```powershell
# Windows
git clone https://github.com/trance81/project-templates.git
cd project-templates
.\setup.ps1
```

```bash
# macOS / Linux
git clone https://github.com/trance81/project-templates.git
cd project-templates
./setup.sh
```

스크립트가 하는 일:
1. `~/.claude/CLAUDE.md`(전역 메모리)에 표준 참조 블록 추가 (이미 있으면 건너뜀)
2. 클론 위치를 블록에 기록 (AI가 STRUCTURE.md를 로컬에서 바로 읽게)

## 수동

### Claude Code

`~/.claude/CLAUDE.md`에 아래 블록 추가:

```markdown
## 프로젝트 지식관리 표준 (project-templates)
- 정본: https://github.com/trance81/project-templates.git (로컬: <클론경로>)
- 새 프로젝트 시작, 기존 프로젝트 분석/개발 시 STRUCTURE.md의 pjt-docs/ 구조로 지식을 구성·유지할 것
- 프로젝트에 pjt-docs/가 없으면 도입을 제안할 것
```

### Cursor

Cursor는 파일 기반 전역 규칙이 없다. Settings → Rules → User Rules에 위 블록을 붙여넣는다.
프로젝트 단위로는 템플릿의 `.cursor/rules/pjt-docs.mdc`가 자동 적용된다.

### 기타 AI 도구 (Codex, Copilot 등 — 향후)

- 전역 지시 파일을 지원하면(예: `~/.codex/AGENTS.md`) 같은 블록을 추가
- 프로젝트 단위는 pjt-docs/ 자체가 일반 md 폴더라 어떤 AI든 읽을 수 있음 — 진입점 파일(CLAUDE.md 상당)만 그 도구 규약에 맞게 한 장 추가

## 확인

아무 프로젝트에서나 AI에게 "이 프로젝트 지식구조 어떻게 관리해?"라고 물었을 때 pjt-docs/ 구조를 답하면 성공.
