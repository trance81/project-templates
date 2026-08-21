# 전역 세팅 가이드

새 PC나 새 AI 도구에 이 리포를 "구성 기초"로 등록하는 절차. 이걸 마치면 어떤 프로젝트에서 작업하든 AI가 pjt-docs 구조를 자동 인지하고 유지한다.

## 제일 쉬운 방법 — AI에게 시키기

새 PC의 Claude CLI(또는 다른 AI 도구)에서 이렇게 요청하면 끝:

> https://github.com/trance81/project-templates.git 클론해서 SETUP.md대로 전역 세팅해줘

AI가 할 일 (이 문서가 절차 정본):
1. 리포를 durable한 위치(예: `~/Workspace/project-templates` 등)에 클론 — 임시 폴더 금지
2. `setup.ps1`(Windows) / `setup.sh`(macOS/Linux) 실행 → 전역 등록
3. `global-skills/sync.ps1` / `sync.sh` 실행 안내 → 사용자가 항목별 y/N 선택 (AI가 임의로 전부 설치하지 말 것)
4. Cursor 쓰는 PC면: Settings → Rules → User Rules에 아래 "수동 > Cursor" 절의 블록 붙여넣으라고 안내 (앱 설정 화면이라 AI가 대신 못 함)

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
- ~/.claude/pjt-templates-skills-state.json 이 없으면(스킬 동기화를 한 번도 안 돌린 PC) global-skills/sync 실행을 먼저 안내할 것
```

### Cursor

Cursor는 파일 기반 전역 규칙이 없다. Settings → Rules → User Rules에 위 블록을 붙여넣는다.
프로젝트 단위로는 템플릿의 `.cursor/rules/pjt-docs.mdc`가 자동 적용된다.

### 기타 AI 도구 (Codex, Copilot 등 — 향후)

- 전역 지시 파일을 지원하면(예: `~/.codex/AGENTS.md`) 같은 블록을 추가
- 프로젝트 단위는 pjt-docs/ 자체가 일반 md 폴더라 어떤 AI든 읽을 수 있음 — 진입점 파일(CLAUDE.md 상당)만 그 도구 규약에 맞게 한 장 추가

## 전역 플러그인/스킬 동기화

`global-skills/manifest.json`에 이 리포로 관리하는 마켓플레이스·플러그인·스킬 목록이 있다. 새 PC에서, 혹은 리포가 갱신된 뒤 실행하면 **아직 설치 여부를 정하지 않은 항목만** 하나씩 물어보고, 선택한 것만 설치한다.

`skills` 항목은 두 가지 방식으로 설치된다. `installCmd`가 있으면 그 명령을 실행하고(`npx skills add` 등), `path`가 있으면 이 리포에 보관된 소스를 `~/.claude/skills/<id>`로 복사한다. 어느 쪽이든 설치 위치는 같다.

```powershell
# Windows
cd project-templates\global-skills
.\sync.ps1
```

```bash
# macOS / Linux
cd project-templates/global-skills
./sync.sh
```

- 이미 설치돼 있거나 이전에 "설치/건너뜀"으로 결정한 항목은 다시 안 물어본다 (결정은 `~/.claude/pjt-templates-skills-state.json`에 기록).
- 리포에 새 항목이 추가된 뒤 재실행하면 **그 신규 항목만** 물어본다 — 기존 결정은 그대로 유지.
- 건너뛴 항목을 다시 검토하려면: `.\sync.ps1 -Review` / `./sync.sh --review`
- 이미 설치된 것을 최신으로 갱신하려면: `.\sync.ps1 -Update` / `./sync.sh --update`. 새로 설치하지는 않고, 리포에 소스가 있는 스킬은 내용을 대조해 다를 때만 묻고 교체한다. 플러그인 갱신은 Claude Code 재시작 후 반영된다.
- 새 플러그인을 설치했으면 `global-skills/manifest.json`에 항목을 추가해 다른 PC에도 전파되게 할 것.

## 확인

아무 프로젝트에서나 AI에게 "이 프로젝트 지식구조 어떻게 관리해?"라고 물었을 때 pjt-docs/ 구조를 답하면 성공.
`cd global-skills && ./sync.sh` (또는 `.\sync.ps1`) 실행 시 새로 추가된 항목만 물어보면 성공.
