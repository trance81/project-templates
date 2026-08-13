# 프로젝트 지식관리 구조 표준

프로젝트 안의 지식을 AI(Claude, Cursor)와 사람이 구분 없이 읽고 쓰는 구조. 이 문서가 정본이다.

## 1. 전체 구조

```
<프로젝트루트>/
  .claude/                      # Claude 도구 설정·플러그인·훅 — 그대로 사용. 지식은 넣지 않는다
  CLAUDE.md                     # 얇은 진입점 (10~20행). 지식 본문 금지
  AGENTS.md                     # 같은 내용 — Cursor(최신)·Codex 등 공용 규약
  .cursor/rules/pjt-docs.mdc    # Cursor 진입점 (구버전 Cursor 대비)
  pjt-docs/                     # ★ 지식 정본 — AI·사람 공용
    README.md                   # 통합 인덱스: 지식 지도 + 읽는 순서
    CHANGELOG.md                # 지식 수정 이력 (git 커밋과 별개)
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

빈 폴더는 만들지 않는다 — 해당 유형의 지식이 처음 생길 때 폴더를 만든다. 필수는 `README.md`, `CHANGELOG.md`, `overview.md` 셋뿐이다.

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
3. **원본은 보존, 작업은 변환본으로.** `reference/원본/`은 손대지 않는다.
4. **AI 도구 폴더에 지식 금지.** `.claude/`는 설정·플러그인·훅 전용. 기존에 있던 지식성 파일은 pjt-docs/로 이관.

## 7. AI 진입점

### CLAUDE.md (프로젝트 루트)

```markdown
# <프로젝트명>

한 줄 소개.

## 지식베이스
프로젝트 지식은 전부 [pjt-docs/README.md](pjt-docs/README.md)에서 시작한다.
작업 전 반드시 읽을 것: overview.md, 관련 domain/ 문서.

## 규칙
- 지식 변경 시 같은 커밋에서 pjt-docs/README.md 인덱스와 CHANGELOG.md 갱신
- 코드/동작 변경 시 관련 pjt-docs 문서 같은 커밋에서 갱신
```

### AGENTS.md (프로젝트 루트)

CLAUDE.md와 같은 내용. Cursor(최신), Codex 등 AGENTS.md 규약을 따르는 도구가 자동으로 읽는다.

### .cursor/rules/pjt-docs.mdc

CLAUDE.md와 같은 내용. 상단에 `alwaysApply: true` 프론트매터. (AGENTS.md를 못 읽는 구버전 Cursor 대비)
