# <프로젝트명>

<한 줄 소개>

## 지식베이스
프로젝트 지식은 전부 [pjt-docs/README.md](pjt-docs/README.md)에서 시작한다.
작업 전 반드시 읽을 것: pjt-docs/overview.md, 관련 domain/ 문서.

## 규칙
- **IMPORTANT**: 아키텍처·방식 결정 전 `pjt-docs/decisions/`를 먼저 확인할 것. 기존 결정을 뒤집으려면 해당 문서의 `revisit` 조건 충족 여부부터 확인하고, 새 결정은 구현 전에 결정 문서 초안부터 작성할 것.
- **IMPORTANT**: 지식 변경 시 같은 커밋에서 pjt-docs/README.md 인덱스와 CHANGELOG.md 갱신. 코드/동작 변경 시 관련 pjt-docs 문서도 같은 커밋에서 갱신 — 틀린 지식은 없는 지식보다 나쁘다.
- AI 도구 폴더(.claude, .cursor 등)에는 절대 지식을 넣지 않는다 (도구 설정 전용). 폐기 문서는 삭제하지 않는다 — `status: deprecated` + 대체 링크 배너.
- **IMPORTANT**: 세션 시작 시 `.baton/` 최상위의 `running`·`waiting` 배턴만 읽고 그 맥락에서 이어간다. `done/`과 지난 배턴은 지금 요청과 관련 있을 때만 찾아본다 — 전부 읽으면 컨텍스트만 낭비한다. 운영 규칙은 `.baton/README.md`.
- **IMPORTANT**: 프로젝트에 남는 작업(코드·설정 변경, 이 프로젝트의 문서 작업)은 한 턴에 끝나 커밋까지 마쳤더라도 배턴 한 장을 만들거나 갱신하고, 끝나면 `status: passed`로 닫는다. 판단 기준은 걸린 턴 수가 아니라 프로젝트에 남는 변경인지 여부다. 조사·질의응답이나 프로젝트와 무관한 산출물에는 만들지 않는다.
