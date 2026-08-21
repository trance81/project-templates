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
| 진행중인데 아직 안 끝난 작업(다음 세션에 이어야 함) | `.baton/` (`baton-init` 스킬로 도입, STRUCTURE.md 8장) |

## 2. 이관

- `template/`의 pjt-docs 뼈대를 프로젝트에 복사
- 분류대로 내용 이동. 이관하며 각 문서에 프론트매터 부여 — 검증 안 된 내용은 `status: draft`, `source: 추정`으로 정직하게
- 원본 파일은 이관 완료 확인 전까지 삭제하지 않는다

## 3. 진입점 축소

- CLAUDE.md를 얇은 진입점으로 재작성 (STRUCTURE.md 7장 형식)
- `.cursor/rules/pjt-docs.mdc` 추가
- `.claude/` 안의 지식성 파일은 이관 확인 후 삭제

## 4. 마무리

- `pjt-docs/README.md` 인덱스 작성 (전 문서 등재). 상단 `표준 갱신일`은 정본 `STRUCTURE.md`의 값을 그대로 적는다 — 이후 [update.md](update.md)가 이 값으로 뒤처짐을 판단한다
- `pjt-docs/CHANGELOG.md`에 "pjt-docs 구조 도입, X개 문서 이관" 기록
- `.gitignore`에 `pjt-docs/local/` 추가
- 커밋: `docs: pjt-docs 지식관리 구조 도입`
