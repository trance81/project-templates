# 전역 세팅 가이드

이걸 마치면 어느 프로젝트에서 작업하든 AI가 `pjt-docs/`, `.baton/` 구조를 인지하고 유지합니다.

## 제일 쉬운 방법: AI에게 시키기

Claude Code에서 이 한 줄이면 됩니다.

> https://github.com/trance81/project-templates.git 클론해서 SETUP.md대로 전역 세팅해줘

AI가 따를 절차입니다. 이 문서를 기준으로 삼습니다.

1. 저장소를 오래 둘 위치(예: `~/Workspace/project-templates`)에 클론합니다. 전역 지시가 이 경로를
   가리키게 되므로 지워질 임시 폴더는 안 됩니다.
2. `setup.ps1`(Windows) 또는 `setup.sh`(macOS/Linux)를 실행해 전역 지시 블록을 등록합니다.

여기까지가 표준 세팅의 전부입니다.

## 직접 하기

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

스크립트가 하는 일은 셋입니다.

1. 전역 메모리 `~/.claude/CLAUDE.md`에 표준 참조 블록을 추가합니다. 이미 있으면 건너뜁니다.
2. 클론 위치를 그 블록에 기록해, AI가 `STRUCTURE.md`를 로컬에서 바로 읽게 합니다.
3. `skills/baton-init`을 `~/.claude/skills/baton-init`으로 복사합니다. 내용이 같으면 건너뜁니다.

## 수동 등록

`~/.claude/CLAUDE.md`에 아래 블록을 추가합니다.

```markdown
## 프로젝트 지식관리 표준 (project-templates)
- 기준 문서: https://github.com/trance81/project-templates.git (로컬: <클론경로>)
- 새 프로젝트 시작, 기존 프로젝트 분석/개발 시 STRUCTURE.md의 pjt-docs/ 구조로 지식을 구성·유지할 것
- 프로젝트에 pjt-docs/가 없으면 도입을 제안할 것
- 프로젝트 pjt-docs/README.md 상단의 `표준 갱신일`이 STRUCTURE.md의 값보다 오래됐거나 아예 없으면 update.md 절차로 갱신을 제안할 것
```

스크립트를 쓰지 않고 손으로 등록했다면 `skills/baton-init` 폴더를 `~/.claude/skills/baton-init`으로
복사합니다. `.baton/` 도입을 이 스킬이 처리합니다.

### 기타 AI 도구 (Codex, Cursor 등)

- 전역 지시 파일을 지원하면(예: `~/.codex/AGENTS.md`) 같은 블록을 추가합니다.
- 프로젝트 단위는 `pjt-docs/` 자체가 일반 Markdown 폴더라 어떤 AI든 읽을 수 있습니다. 진입점
  파일(`CLAUDE.md` 상당)만 그 도구 규약에 맞게 한 장 추가하면 됩니다.

## 확인

아무 프로젝트에서나 AI에게 "이 프로젝트 지식구조 어떻게 관리해?"라고 물었을 때 `pjt-docs/`
구조를 답하면 성공입니다. `~/.claude/skills/baton-init/SKILL.md`가 있으면 스킬 설치도 된 것입니다.
