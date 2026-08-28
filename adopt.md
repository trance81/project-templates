# 기존 프로젝트 도입 절차

`.claude/`와 CLAUDE.md에 지식이 산재한 기존 프로젝트에 pjt-docs 구조를 도입하는 절차. AI에게 "이 프로젝트에 pjt-docs 구조 도입해줘"라고 요청하면 이 절차를 따른다.

이미 도입한 프로젝트를 최신 표준에 맞추는 것은 [update.md](update.md)를 본다.

## 1. 현황 파악

- CLAUDE.md, `.claude/` 하위(rules/, local/, memory/, 프로젝트정보/ 등), docs/, 흩어진 md 파일을 전부 나열
- 각 파일의 내용을 지식 유형으로 분류:

| 기존 내용 | 이관 위치 |
|---|---|
| 프로젝트 개요·빌드법·실행법 | `pjt-docs/overview.md` |
| 개발 표준·패턴 문서 (.claude/rules/ 등) | `pjt-docs/domain/` |
| 업무 규칙·용어·도메인 지식 | `pjt-docs/domain/` |
| 결정 사항·경위 ("~하기로 했다") | `pjt-docs/decisions/` (재론 조건 보강) |
| 설계문서·외부 원본 | `pjt-docs/reference/원본/` + 변환본 |
| 문제 해결 기록 | `pjt-docs/troubleshooting/` |
| 재사용 가능 노하우 | `pjt-docs/skills/` |
| DB 접속정보 등 비밀 (.claude/local/ 등) | `pjt-docs/local/` (.gitignore 확인) |
| 도구 설정 (settings.json, hooks, 플러그인) | `.claude/`에 그대로 둠 |
| 진행중인데 아직 안 끝난 작업(다음 세션에 이어야 함) | `.baton/<이름>/` (`baton-init` 스킬로 도입, STRUCTURE.md 8장) |
| 조사만 하고 하지 않기로 한 것 ("~는 안 하기로") | `pjt-docs/decisions/` (재론 조건 보강) |

## 2. 이관

- `template/`의 pjt-docs 뼈대를 프로젝트에 복사
- 분류대로 내용 이동. 이관하며 각 문서에 문서 메타데이터 부여 — 검증 안 된 내용은 `status: draft`, `source: 추정`으로 정직하게
- 원본 파일은 이관 완료 확인 전까지 삭제하지 않는다

## 3. 진입점 축소

- CLAUDE.md를 얇은 진입점으로 재작성 (STRUCTURE.md 7장 형식)
- 같은 내용으로 `AGENTS.md` 추가
- `.claude/` 안의 지식성 파일은 이관 확인 후 삭제

## 4. .baton/ 구성

`.baton/`은 표준의 기본 구성이라 pjt-docs와 함께 만든다 (STRUCTURE.md 8장). 손으로 파일을
만들지 말고 `baton-init` 스킬을 실행한다. 스킬이 이 PC의 사용자 이름과 이 프로젝트의 배턴
단위(화면, 섹션, 인터페이스 등 반복 수정되는 것)를 묻고, `.baton/README.md` 생성, 사용자
폴더 생성, 진입점 규칙 줄 추가, 훅 셋(편집·턴 종료·커밋을 막는 PreToolUse·Stop·pre-commit) 등록,
`.gitignore` 정리를 한 번에 처리한다.

1단계에서 "진행 중인데 아직 안 끝난 작업"으로 분류한 내용이 있으면, 스킬 실행 후 각각을
`.baton/<이름>/<단위>.md`로 옮긴다. 파일명은 작업 이름이 아니라 그 작업이 손대는 단위의
식별자로 짓는다. 이미 끝난 작업이면 `status: passed`로 적고, 무엇을 왜 바꿨는지를 수정 이력
항목으로 남긴다.

`.baton/`은 git에 들어가야 한다. pjt-docs를 독립 저장소로 두는 구성이면 `.baton/`도 그
저장소 안에 둔다.

## 5. 마무리

- `pjt-docs/README.md` 인덱스 작성 (전 문서 등재). 상단 `표준 갱신일`은 기준 문서 `STRUCTURE.md`의 값을 그대로 적는다 — 이후 [update.md](update.md)가 이 값으로 뒤처짐을 판단한다
- `pjt-docs/CHANGELOG.md`에 "pjt-docs 구조 도입, X개 문서 이관" 기록
- `.gitignore`에 `pjt-docs/local/` 추가 (`.baton/` 쪽은 4단계에서 스킬이 처리한다)
- 커밋: `docs: pjt-docs 지식관리 구조 도입`

git 저장소가 아닌 프로젝트라면 `git init`을 권하고, 사용자가 원치 않으면 `CHANGELOG.md`를 더
성실히 쓰고 `pjt-docs/local/`을 백업·공유 대상에서 빼야 한다고 알린다
(STRUCTURE.md 6장 "git 을 쓰지 않는 프로젝트").
