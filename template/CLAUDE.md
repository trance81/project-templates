# <프로젝트명>

<한 줄 소개>

## 지식베이스
프로젝트 지식은 전부 [pjt-docs/README.md](pjt-docs/README.md)에서 시작한다.
작업 전 반드시 읽을 것: pjt-docs/overview.md, 관련 domain/ 문서.

## 규칙
- **IMPORTANT**: 아키텍처·방식 결정 전 `pjt-docs/decisions/`를 먼저 확인할 것. 기존 결정을 뒤집으려면 해당 문서의 `revisit` 조건 충족 여부부터 확인하고, 새 결정은 구현 전에 결정 문서 초안부터 작성할 것.
- **IMPORTANT**: 지식 변경 시 같은 커밋에서 pjt-docs/README.md 인덱스와 CHANGELOG.md 갱신. 코드/동작 변경 시 관련 pjt-docs 문서도 같은 커밋에서 갱신 — 틀린 지식은 없는 지식보다 나쁘다.
- `.claude/`에는 절대 지식을 넣지 않는다 (도구 설정 전용). 폐기 문서는 삭제하지 않는다 — `status: deprecated` + 대체 링크 배너.
- **IMPORTANT**: 세션 시작 시 `.baton/local/owner`에 적힌 내 폴더(`.baton/<이름>/`)의 `running`·`waiting` 배턴만 읽고 그 맥락에서 이어간다. `owner`가 없으면 사용자에게 묻는다. 다른 사람의 폴더는 사용자가 지시할 때만 연다. 운영 규칙은 `.baton/README.md`.
- **IMPORTANT**: 프로젝트에 남는 작업을 시작하기 전에 내 폴더에서 그 단위(`.baton/README.md`에 선언된 단위)의 배턴을 먼저 찾는다. 있으면 수정 이력을 읽고 같은 파일을 이어 쓴다. 없으면 단위 식별자로 새로 만든다. 날짜나 작업 동사를 파일명에 넣지 않는다.
- **IMPORTANT**: 프로젝트에 남는 작업(코드·설정 변경, 이 프로젝트의 문서 작업)은 한 턴에 끝나 커밋까지 마쳤더라도 배턴을 갱신하고 수정 이력에 `날짜 · 기능 · 요지` 항목을 남긴 뒤 `status: passed`로 닫는다. 파일 변경이 없어도 "하지 않기로 했다", "확인된 사실", "우리가 고칠 수 없다"로 끝난 조사는 남긴다. 결정은 `pjt-docs/decisions/`에, 사실은 배턴 이력에, 못 고치는 문제는 `pjt-docs/troubleshooting/`에 draft로. CHANGELOG 나 커밋 메시지를 썼다고 배턴을 대신하지 않는다. 훅이 열린 배턴 없는 편집·턴 종료·커밋을 막는다.
