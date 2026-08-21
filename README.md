# project-templates

프로젝트 지식관리 구조 표준 리포. AI(Claude, Cursor)와 사람이 공용으로 쓰는 프로젝트 지식베이스(`pjt-docs/`)의 정본 정의와 템플릿을 담는다.

## 목적

- 프로젝트별 지식(도메인 지식, 결정 기록, 참고 자료, 노하우)을 특정 AI 도구 폴더(`.claude/` 등)에 가두지 않고, 일반 폴더로 관리한다.
- 회사/집/외부 어디서든 git clone/pull 만으로 프로젝트 지식을 동일하게 확보한다.
- AI와 사람 모두 `pjt-docs/README.md` 하나로 프로젝트 지식 전체를 파악한다.

## 구성

| 파일/폴더 | 설명 |
|---|---|
| [STRUCTURE.md](STRUCTURE.md) | 지식관리 구조 표준 정의서 (정본) |
| [template/](template/) | 새 프로젝트에 복사해 쓰는 뼈대 (각 폴더에 예시 포함) |
| [adopt.md](adopt.md) | 기존 프로젝트(.claude 등에 지식 산재)에 구조를 도입하는 절차 |
| [update.md](update.md) | 이미 도입한 프로젝트를 최신 표준으로 갱신하는 절차 |
| [global-skills/](global-skills/) | PC 전역 플러그인·스킬 설치 목록 + 동기화 스크립트 (SETUP.md 참조) |
| [global-skills/skills/baton-init/](global-skills/skills/baton-init/) | 세션 간 진행 중 작업 상태(`.baton/`)를 도입하는 스킬 (STRUCTURE.md 8장 참조) |

## 사용법

### 새 프로젝트

1. `template/` 내용을 프로젝트 루트에 복사
2. `pjt-docs/overview.md`부터 채우고 `pjt-docs/README.md` 인덱스 갱신
3. `pjt-docs/CHANGELOG.md`에 "최초 구성" 기록

### 기존 프로젝트

[adopt.md](adopt.md) 절차를 따른다. 핵심: 기존 CLAUDE.md / `.claude/` 안의 지식을 유형별로 `pjt-docs/` 하위로 이관하고, CLAUDE.md는 얇은 진입점으로 축소.

### 이미 도입한 프로젝트 갱신

표준이 바뀌면 [update.md](update.md) 절차를 따른다. AI에게 "pjt-docs 최신 표준으로 갱신해줘"라고
요청하면 된다. 프로젝트의 `pjt-docs/README.md`에 적힌 표준 갱신일이 [STRUCTURE.md](STRUCTURE.md)의
값보다 오래됐다면 갱신할 때가 된 것이다.

PC에 설치된 스킬 갱신은 별개다. `global-skills/sync.ps1 -Update`(또는 `sync.sh --update`)를 쓴다.

### 진행 중 작업 상태 (선택)

여러 세션에 걸치는 작업이 있으면 `baton-init` 스킬로 `.baton/`을 추가로 도입한다 (STRUCTURE.md 8장). `global-skills/sync`로 설치되며, `pjt-docs/`(확정 지식)와는 레이어가 다르다.

### AI 전역 연결

`~/.claude/CLAUDE.md`(전역 메모리)에 아래 한 줄을 추가하면 모든 프로젝트에서 자동 적용된다:

```
프로젝트 지식관리 표준: https://github.com/trance81/project-templates.git 의 STRUCTURE.md.
새 프로젝트 시작·기존 프로젝트 분석/개발 시 이 구조로 pjt-docs/ 를 구성·유지할 것.
```
