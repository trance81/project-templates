# HELP — 이 프로젝트의 AI·지식관리 사용법

사람이 확인차 보는 문서. AI 규칙은 CLAUDE.md/AGENTS.md, 구조 표준은 project-templates 저장소의 STRUCTURE.md 를 기준으로 삼는다.

## 폴더 구조 한눈에

```
프로젝트/
├─ CLAUDE.md, AGENTS.md          AI 진입점 (Claude Code / 그 외 도구)
├─ .claude/                      Claude 도구 설정 (지식 없음)
├─ scripts/check-docs.py         문서 정합성 검사
├─ .baton/                       진행 중 작업 + 화면·기능별 수정 이력
│  ├─ README.md                  운영 규칙 (이 프로젝트의 배턴 단위가 여기 적혀 있음)
│  └─ <내이름>/<단위>.md          내 배턴. 같은 화면을 다시 고치면 같은 파일에 이력이 쌓임
└─ pjt-docs/                     ★ 지식은 전부 여기
   ├─ README.md                  지식 지도 (문서 목록·상태) — 여기부터 볼 것
   ├─ CHANGELOG.md               릴리스·마일스톤 요약 (쓰는 프로젝트만)
   ├─ HELP.md                    이 문서
   ├─ overview.md                프로젝트 개요·실행법
   ├─ decisions/                 왜 이렇게 했나 (결정 기록)
   ├─ domain/                    업무 규칙·용어·도메인 지식
   ├─ reference/                 외부 자료 (원본/ + markdown/ 변환본)
   ├─ skills/                    다른 프로젝트로 가져갈 노하우
   ├─ troubleshooting/           겪은 문제와 해법
   └─ local/                     git 미추적 (접속정보·개인메모)
```

## AI한테 자주 쓰는 요청

| 하고 싶은 것 | 이렇게 말하면 됨 |
|---|---|
| 프로젝트 파악 | "pjt-docs 읽고 이 프로젝트 요약해줘" |
| 지식 추가 | "이 내용 pjt-docs에 기록해줘" (알아서 분류하고 인덱스까지 등재) |
| 결정 기록 | "이거 이렇게 하기로 한 거 결정 문서로 남겨줘" |
| 문제 해결 기록 | "방금 해결한 거 troubleshooting에 남겨줘" |
| 문서 상태 점검 | "check-docs 돌리고 문제 정리해줘" |
| 구조 처음 도입 | "pjt-docs 구조 도입해줘" |
| 이 화면 지난번에 뭐 고쳤나 | "PSBSOP00400 배턴 수정 이력 보여줘" (단위 식별자로) |
| 다른 사람 작업 참고 | "hong 폴더의 같은 화면 배턴도 같이 봐줘" (지시해야만 읽음) |
| 조사만 하고 안 하기로 함 | "이거 안 하기로 한 이유 decisions에 남겨줘" |

## 문서 규칙 (읽을 때 알아둘 것)

- 각 문서 상단 `status`: **draft**(검증 안 됨) / **active**(유효) / **deprecated**(폐기 — 대체 링크 있음)
- `source`: 이 지식이 어디서 왔나 (실DB 확인 / 추정 등) — 신뢰도 판단 기준
- 결정 문서의 `revisit`: 이 조건이 되면 다시 논의 가능하다는 뜻

## 정합성 검사

```
python scripts/check-docs.py
```
인덱스 누락·깨진 링크·오래된 문서(180일)를 잡아준다. 커밋 전 실행 권장.

## PC 전역 AI 세팅 (프로젝트와 별개)

- 세팅 절차: https://github.com/trance81/project-templates.git 의 SETUP.md
- 새 PC: 위 저장소를 클론한 뒤 `setup.ps1`(Windows) 또는 `setup.sh`(macOS/Linux) 실행
- 스크립트가 전역 지시 등록과 `baton-init` 스킬 설치를 함께 처리한다
