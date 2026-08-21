# 프로젝트 지식관리 구조 표준

프로젝트 안의 지식을 AI(Claude, Cursor)와 사람이 구분 없이 읽고 쓰는 구조. 이 문서가 정본이다.

**표준 갱신일: 2026-08-25**

각 프로젝트의 `pjt-docs/README.md` 상단에도 같은 값을 적어 둔다. 두 값이 다르면 그 프로젝트는
표준보다 뒤처져 있다는 뜻이므로 [update.md](update.md) 절차로 갱신한다. 이 날짜는 프로젝트가
따라와야 하는 변경이 생겼을 때만 올린다. 오타 수정이나 문장 다듬기로는 올리지 않는다.

## 1. 전체 구조

```
<프로젝트루트>/
  .claude/                      # Claude 도구 설정·플러그인·훅 — 그대로 사용. 지식은 넣지 않는다
  CLAUDE.md                     # 얇은 진입점 (10~20행). 지식 본문 금지
  AGENTS.md                     # 같은 내용 — Cursor(최신)·Codex 등 공용 규약
  .cursor/rules/pjt-docs.mdc    # Cursor 진입점 (구버전 Cursor 대비)
  scripts/check-docs.py         # pjt-docs 정합성 검사 (6장 참조)
  pjt-docs/                     # ★ 지식 정본 — AI·사람 공용
    README.md                   # 통합 인덱스: 지식 지도 + 읽는 순서
    CHANGELOG.md                # 지식 수정 이력 (git 커밋과 별개)
    HELP.md                     # 사람용 치트시트: 폴더 구조 그림 + AI 요청 문구 + 검사법
    overview.md                 # 프로젝트 개요: 목적·배경·기술스택·실행법
    decisions/                  # 결정 기록
      0001-<제목>.md
    domain/                     # 도메인 지식: 업무 규칙·용어·프로세스
    reference/                  # 외부 자료
      원본/                     # 받은 그대로 보존 (수정 금지)
      markdown/                 # 검색 가능한 변환본
    skills/                     # 공유 가능한 노하우 (프로젝트 중립적으로 작성)
    troubleshooting/            # 문제-해결 기록
      YYYY-MM-DD-<제목>.md
    local/                      # git 미추적: 접속정보·개인메모 (.gitignore 등록)
```

빈 폴더는 만들지 않는다 — 해당 유형의 지식이 처음 생길 때 폴더를 만든다. 필수는 `README.md`, `CHANGELOG.md`, `HELP.md`, `overview.md` 넷이다.

`HELP.md`는 **사람 전용** 확인 문서다 — 폴더 구조 그림, AI에게 자주 쓰는 요청 문구, 문서 규칙 읽는 법, 검사 실행법을 심플하게 담는다. 프론트매터·인덱스 등재 의무가 없고(README/CHANGELOG와 같은 취급), 도입 시 템플릿 그대로 복사하면 된다. 프로젝트 전용 스킬·플러그인을 쓰게 되면 그 사용법도 여기에 한 줄씩 추가한다.

## 2. 폴더별 역할

| 폴더 | 담는 것 | 담지 않는 것 |
|---|---|---|
| `decisions/` | 왜 이렇게 하기로 했나, 왜 안 하기로 했나, 언제 다시 논의하나 | 구현 방법 상세 (그건 domain/이나 코드 주석) |
| `domain/` | 업무 규칙, 용어 정의, 프로세스, DB/시스템 도메인 지식 | 일시적 메모 (그건 local/) |
| `reference/원본/` | 설계문서·PPT·명세 등 받은 원본 그대로 | — 수정 금지 |
| `reference/markdown/` | 원본의 검색 가능한 md 변환본 | 원본에 없는 해석 (해석은 domain/에) |
| `skills/` | 다른 프로젝트에 복사해 갈 수 있는 재사용 노하우 | 이 프로젝트에서만 유효한 내용 |
| `troubleshooting/` | 겪은 문제와 해법, 재발 방지법 | 미해결 추측 (해결 후 기록) |
| `local/` | DB 접속정보, 개인 메모 — git 미추적 | 팀과 공유할 지식 |

## 3. README.md — 통합 인덱스 (필수)

AI든 사람이든 이 파일 하나로 전체를 파악한다. 형식:

```markdown
# <프로젝트명> 지식베이스

## 이 프로젝트는
한 단락 요약. 상세는 [overview.md](overview.md).

## 지식 지도
| 문서 | 설명 | 상태 | 갱신일 |
|---|---|---|---|
| [overview.md](overview.md) | 프로젝트 개요 | active | 2026-08-13 |
| [decisions/0001-예시.md](decisions/0001-예시.md) | 예시 결정 | active | 2026-08-13 |

## 읽는 순서
- 처음 온 사람/AI: overview → domain → decisions
- 작업 재개: CHANGELOG 최근 항목부터
```

규칙:
- 모든 문서는 지식 지도 표에 한 줄씩 올린다. 표에 없는 문서는 없는 문서다.
- 상태·갱신일은 각 문서의 프론트매터와 일치시킨다.

## 4. CHANGELOG.md — 지식 수정 이력 (필수)

git 커밋은 "파일이 바뀌었다"만 남긴다. "지식이 왜 어떻게 바뀌었나"는 여기 남긴다. 최신이 위.

```markdown
# 지식 변경 이력

## 2026-08-13
- decisions/0002 추가: 동기화 방식 확정 (사유: 출장 중 지식 유실)
- domain/용어사전.md: "마감" 정의 수정 — 실DB 확인 결과 기존 설명이 틀렸음
```

내용 없는 항목("문서 수정")은 금지 — 무엇이 왜 바뀌었는지 한 줄로.

## 5. 문서 공통 규칙

모든 `pjt-docs/` 문서 상단에 프론트매터 3필드:

```yaml
---
status: draft | active | deprecated
updated: 2026-08-13
source: 실DB 확인 / 담당자 구두 / 설계문서 v1.2 / 추정
---
```

- `status`: draft(초안, 검증 안 됨) / active(정본) / deprecated(폐기)
- `source`: 이 지식이 어디서 왔나. **검증 방법과 날짜가 있으면 명시** (예: "2026-08-13 실DB 조회로 확인"). 추정이면 솔직하게 `추정`.
- 폐기 시 삭제하지 않는다 — `status: deprecated`로 바꾸고 본문 맨 위에 배너: `> ⚠️ 폐기됨 (2026-08-13). 대체: [새문서](링크)`

`decisions/` 문서는 필드 추가:

```yaml
revisit: 검색 실패율 5% 초과 시 / 제품 버전 업그레이드 시 / 없음(영구)
```

재론 조건을 가능한 한 숫자로. 이게 있어야 같은 논의가 반복되지 않고, AI가 근거 없이 결정을 뒤집지 않는다.

## 6. 운영 규칙

1. **지식 변경 = 같은 커밋에서 README 인덱스 + CHANGELOG 갱신.** 나중에 하면 반드시 어긋난다.
2. **코드/동작이 바뀌면 관련 pjt-docs 문서도 같은 커밋에서 갱신.** 틀린 지식은 없는 지식보다 나쁘다 — AI가 자신 있게 틀린 답을 한다.
3. **결정 우선.** 아키텍처·방식 결정 전 `decisions/`를 먼저 확인한다. 기존 결정을 뒤집으려면 그 문서의 `revisit` 조건 충족 여부부터 확인하고, 새 결정은 구현 전에 결정 문서 초안부터 쓴다. (AI가 "왜"를 모르면 그 이유를 리팩토링으로 지워버린다.)
4. **원본은 보존, 작업은 변환본으로.** `reference/원본/`은 손대지 않는다.
5. **AI 도구 폴더에 지식 금지.** `.claude/`는 설정·플러그인·훅 전용. 기존에 있던 지식성 파일은 pjt-docs/로 이관.

### 정합성 검사 (scripts/check-docs.py)

프로젝트 루트에서 `python scripts/check-docs.py` 실행. 검사 항목:
- 프론트매터 누락, `status`/`updated` 필드 누락, 날짜 형식 오류
- README 인덱스 표 ↔ 실제 파일 불일치 (미등재 문서, 없는 파일 링크)
- 문서 안 깨진 상대 링크
- `status: active`인데 `updated`가 180일 지난 문서 → 신선도 경고 (`--stale-days`로 조정)

커밋 전이나 작업 시작 시 돌리는 것을 권장. `pjt-docs/local/`과 `reference/원본/`은 검사 제외.

## 7. AI 진입점

### CLAUDE.md (프로젝트 루트)

```markdown
# <프로젝트명>

한 줄 소개.

## 지식베이스
프로젝트 지식은 전부 [pjt-docs/README.md](pjt-docs/README.md)에서 시작한다.
작업 전 반드시 읽을 것: overview.md, 관련 domain/ 문서.

## 규칙
- **IMPORTANT**: 아키텍처·방식 결정 전 `pjt-docs/decisions/`를 먼저 확인할 것. 기존 결정을 뒤집으려면 revisit 조건 충족 여부부터, 새 결정은 구현 전에 결정 문서 초안부터.
- **IMPORTANT**: 지식 변경 시 같은 커밋에서 pjt-docs/README.md 인덱스와 CHANGELOG.md 갱신. 코드/동작 변경 시 관련 pjt-docs 문서도 같은 커밋에서 갱신.
- .claude/에는 지식을 넣지 않는다. 폐기 문서는 삭제 대신 deprecated + 대체 링크.
```

강조 마커(**IMPORTANT**)는 장식이 아니다 — AI의 규칙 준수율을 실제로 높인다. 단, 남발하면 효과가 죽으니 핵심 2~3개에만 쓴다. 진입점은 200행 이하(우리 표준은 20행 이하)로 유지 — 길수록 준수율이 떨어진다.

### AGENTS.md (프로젝트 루트)

CLAUDE.md와 같은 내용. Cursor(최신), Codex 등 AGENTS.md 규약을 따르는 도구가 자동으로 읽는다.

### .cursor/rules/pjt-docs.mdc

CLAUDE.md와 같은 내용. 상단에 `alwaysApply: true` 프론트매터. (AGENTS.md를 못 읽는 구버전 Cursor 대비)

## 8. 진행 중 작업 상태 (.baton/)

`pjt-docs/`는 사람이 정제해서 남긴 확정된 지식을 담는다. 반면에 아직 진행 중이라 확정되지 않은
작업 상태, 즉 "무슨 작업을 하다가 세션이 끊겼는가"를 담는 자리는 따로 없었다. `.baton/`이 그
공백을 메운다.

```
<프로젝트루트>/
  .baton/
    README.md       # 운영 규칙                                          git
    <slug>.md       # 작업 단위 진행상태 (status: running/waiting/passed)  git
    done/           # 아카이브 (선택)                                     git
    local/          # 로컬 전용 메모 (선택)                               git 제외
    .session/       # 턴 종료 훅이 쓰는 런타임 기록                        git 제외
```

- `pjt-docs/`와는 레이어가 다르다. `.baton/*.md`는 모델이 매 세션 갱신하는 진행 상태이고,
  `pjt-docs/`는 사람이 검증해서 남기는 확정 지식이다. 둘을 하나로 합치지 않는다.
- 배턴이 `status: passed`로 끝나도 지우지 않는다. 그중에서 재사용할 가치가 있는 내용(결정 근거,
  노하우, 문제 해결 기록)은 `pjt-docs/decisions/`나 `pjt-docs/troubleshooting/`으로 **추가로**
  옮겨 적되, 옮겼다고 해서 배턴 원본을 지우지는 않는다. 승격은 복사이지 대체가 아니다.
- `check-docs.py`의 정합성 검사 대상은 `pjt-docs/`뿐이고 `.baton/`은 검사하지 않는다.
- 세션을 시작할 때는 `.baton/` 최상위의 `running`과 `waiting` 배턴만 읽는다. `done/`과 지난
  배턴은 지금 요청과 관련이 있을 때만 찾아본다. 전부 읽으면 컨텍스트만 낭비한다.
- 도입은 `baton-init` 스킬로 한다. 이 리포의 `global-skills/skills/baton-init/`가 정본이며,
  `global-skills/sync`를 실행하면 `~/.claude/skills/baton-init/`에 설치된다. 이후 프로젝트에서
  "이 프로젝트에 baton 추가해줘"라고 요청하면 스킬이 `.baton/README.md` 생성, 진입점 포인터 줄
  추가, 턴 종료 훅 등록까지 처리한다. 상세한 규약과 필드, 제약은 그 폴더의 `SKILL.md`와
  `templates/baton-readme.md`(설치되는 `.baton/README.md` 원문)가 정본이다.
