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

## 사용법

### 새 프로젝트

1. `template/` 내용을 프로젝트 루트에 복사
2. `pjt-docs/overview.md`부터 채우고 `pjt-docs/README.md` 인덱스 갱신
3. `pjt-docs/CHANGELOG.md`에 "최초 구성" 기록

### 기존 프로젝트

[adopt.md](adopt.md) 절차를 따른다. 핵심: 기존 CLAUDE.md / `.claude/` 안의 지식을 유형별로 `pjt-docs/` 하위로 이관하고, CLAUDE.md는 얇은 진입점으로 축소.

### AI 전역 연결

`~/.claude/CLAUDE.md`(전역 메모리)에 아래 한 줄을 추가하면 모든 프로젝트에서 자동 적용된다:

```
프로젝트 지식관리 표준: https://github.com/trance81/project-templates.git 의 STRUCTURE.md.
새 프로젝트 시작·기존 프로젝트 분석/개발 시 이 구조로 pjt-docs/ 를 구성·유지할 것.
```
