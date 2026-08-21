---
name: bento-templates
description: bento 슬라이드·덱 템플릿 선택. bento 덱·슬라이드·프레젠테이션 생성 요청 시 반드시 먼저 로드해 어떤 템플릿으로 만들지 묻는다. "bento로 만들어", "슬라이드로 작성", "덱 만들어", "설계서 슬라이드" 같은 요청이 트리거다.
user-invocable: true
---

# Bento 템플릿 선택 (전역)

이 스킬은 **모든 프로젝트에서 공통으로 쓰는 bento 템플릿 레지스트리**다.
프로젝트에 전용 템플릿이 있으면 그것까지 합쳐서 선택지를 만든다.

## 규칙 1 — 작성 전 반드시 묻는다

bento 슬라이드/덱 생성 요청을 받으면 **다른 작업을 하기 전에** `AskUserQuestion` 으로 템플릿 선택을 받는다.
사용자가 이미 템플릿을 지정했다면(예: "Terra로", "신규로", "부록형으로") 묻지 않고 진행한다.

## 규칙 2 — 선택지는 전역 + 프로젝트를 합쳐서 만든다

1. **전역 레지스트리**: 이 폴더의 `TEMPLATES.md` 를 읽는다. (공식 디자인 템플릿 + 신규 작성)
2. **프로젝트 레지스트리**: 현재 작업 디렉토리에서 `.claude/skills/*/TEMPLATES.md` 를 찾는다.
   있으면 읽어서 **그 항목을 선택지 앞쪽에 놓는다.** (프로젝트 전용이 더 구체적이므로 우선)
   없으면 전역 항목만으로 구성한다.
3. 옵션 라벨에는 템플릿 이름을, 설명에는 **한글 설명**을 넣는다.

`AskUserQuestion` 은 한 질문에 최대 4개 선택지만 허용하므로, 항목이 4개를 넘으면
먼저 **분류**를 묻고 필요하면 한 번 더 묻는다.

1차 질문 예 — "어떤 템플릿으로 작성할까요?"

| 상황 | 선택지 구성 |
|---|---|
| 프로젝트 템플릿 있음 | 프로젝트 템플릿 1~2종 + `공식 디자인 템플릿`(2차 질문) + `신규 작성` |
| 프로젝트 템플릿 없음 | 공식 4종 중 상위 3종 + `신규 작성`, 또는 `공식 디자인 템플릿`(2차) + `신규 작성` |

2차 질문(공식 템플릿 선택 시) — 레지스트리의 4종을 한글 설명과 함께 제시한다.

## 규칙 3 — 템플릿 선택 시 절차

템플릿 파일(`templates/*.bento.html`)에 박혀 있는 앱 런타임은 받아둔 시점 것이라 **오래될 수 있다**.
디자인(JSON)만 템플릿에서 가져오고, 앱 런타임은 매번 bento.page에서 최신으로 새로 받는다 —
bento-slides 플러그인이 신규 덱을 만들 때 쓰는 것과 같은 방식.

1. 최신 앱 셸을 대상 경로로 받는다.
   ```bash
   curl -fsSL https://bento.page/releases/slides/Bento_Slides.bento.html -o "<대상>.bento.html"
   ```
   (Windows, curl 없으면: `iwr https://bento.page/releases/slides/Bento_Slides.bento.html -OutFile <대상>.bento.html`)
2. 템플릿의 `#bento-doc` JSON만 읽어 방금 받은 파일에 이식한다 — 런타임은 그대로 둔다.
   ```python
   import bento_io
   doc = bento_io.load("~/.claude/skills/bento-templates/templates/Terra.bento.html")
   bento_io.save("<대상>.bento.html", doc)
   ```
3. `docId`·`collab` 은 이식한 JSON에 없다(열 때 새로 생성됨). 억지로 넣지 않는다.
4. 네트워크 안 되거나 curl/iwr 실패 시에만 폴백: 템플릿 파일을 그대로 `cp` — 런타임이 예전 버전일 수 있음을 사용자에게 알린다.

스키마·모션·차트 문법은 `bento-slides` 플러그인 스킬(https://bento.page/agents.md)을 따른다.
이 스킬은 **템플릿 선택과 안전한 읽기/쓰기**만 담당한다.

## 규칙 4 — 기존 덱 수정 시

이미 만들어진 덱을 고칠 때는 **처음부터 다시 빌드하지 말 것.**
사용자가 편집기에서 직접 수정한 내용(표지 문구·로고 위치·행 추가 등)이 날아간다.
JSON을 읽어 **해당 슬라이드/요소만 수정하고 다시 써넣는다.** `docId`·`collab`·`assets` 는 그대로 둔다.

## 규칙 5 — 템플릿 추가

- **전역(모든 프로젝트에서 쓸 것)**: `~/.claude/skills/bento-templates/templates/` 에 파일을 넣고
  이 폴더의 `TEMPLATES.md` 표에 행을 추가한다.
- **특정 프로젝트 전용**: 그 프로젝트의 `.claude/skills/<스킬명>/templates/` 에 넣고
  그쪽 `TEMPLATES.md` 에 행을 추가한다.

어느 쪽이든 코드 수정은 필요 없다. 레지스트리만 고치면 다음부터 선택지에 나온다.

## 파일 구성

```
~/.claude/skills/bento-templates/
├─ SKILL.md         이 파일 — 절차
├─ TEMPLATES.md     전역 템플릿 레지스트리 (작성 전 읽을 것)
├─ bento_io.py      #bento-doc 블록 안전 읽기/쓰기 (이스케이프 처리)
└─ templates/
   ├─ Terra.bento.html          공식 — 프리미엄 제품   (1280×720)
   ├─ Orbital.bento.html        공식 — 다크 몰입형
   ├─ Pixel_Picnic.bento.html   공식 — 캐주얼
   └─ Signal.bento.html         공식 — 에디토리얼
```
