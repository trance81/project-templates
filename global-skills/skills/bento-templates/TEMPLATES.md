# 전역 템플릿 레지스트리

모든 프로젝트에서 선택할 수 있는 bento 템플릿 목록이다.
**추가하려면 아래 표에 행을 추가하고 `templates/` 에 파일을 넣으면 된다.** 코드 수정은 필요 없다.

> 현재 프로젝트에 전용 템플릿이 있으면(`.claude/skills/*/TEMPLATES.md`) 그 항목을 **앞쪽에** 놓고
> 아래 항목을 뒤에 붙여 선택지를 만든다.

## 공식 디자인 템플릿 (bento.page 제공 · 1280×720)

| 코드 | 이름 | 파일 | 한글 설명 |
|---|---|---|---|
| `terra` | Terra — 프리미엄 제품 | `Terra.bento.html` | **차분한 고급 톤.** 베이지 배경(#F7F5F0)에 테라코타 포인트, 사진 7장이 켄번스로 천천히 움직임. 제품 소개·브랜드 발표에 적합. 5장 |
| `orbital` | Orbital — 다크 몰입형 | `Orbital.bento.html` | **어두운 배경의 임팩트형.** 딥네이비(#05060E)에 시안 네온, 모션 27개로 화면이 계속 살아있음. **클릭하면 상세가 열리는 드릴다운(state) 2개**와 영상 포함. 기술·데이터 발표에 적합. 8장 (3.8MB) |
| `pixel` | Pixel Picnic — 캐주얼 | `Pixel_Picnic.bento.html` | **밝고 발랄한 톤.** 노랑 배경(#FFD43A)에 핑크 포인트, 숫자가 올라가는 카운트업과 효과음 포함. 사내 행사·팀 이벤트 안내에 적합. 6장 |
| `signal` | Signal — 에디토리얼 | `Signal.bento.html` | **타이포 중심의 편집 디자인.** 오프화이트(#EFEDE4)에 강렬한 레드, 큰 글씨와 흐르는 마퀴로 메시지를 강조. 컨퍼런스·선언문·아젠다에 적합. 7장 |

## 템플릿 없이

| 코드 | 이름 | 한글 설명 |
|---|---|---|
| `new` | 신규 작성 | 템플릿을 쓰지 않고 내용에 맞춰 자유롭게 구성한다. 최신 런타임을 받아 새로 만든다 |

### `new` 선택 시

```bash
curl -fsSL https://bento.page/releases/slides/Bento_Slides.bento.html -o "<주제>.bento.html"
```

받은 파일(1.0.18+)의 `#bento-doc` 블록은 **비어 있다**(브라우저에서 열 때만 쇼케이스를 생성). 그 빈 블록에 문서 JSON을 써넣는다.
구버전 셸이면 쇼케이스 덱이 들어 있으므로 통째로 교체한다.
`size`·`theme`(`theme.fontFamily` 포함)은 필수이고, `docId`·`collab` 은 넣지 않는다.

## 공통 사양

| 항목 | 값 |
|---|---|
| 캔버스 | 1280 × 720 (공식 템플릿 공통) |
| 여백 | 좌우 96px — 가장 오른쪽 요소의 `x + w` ≤ 1184 |
| 색상 | 강조색 1개, 서체 2개 이하 |
| 노트 | 모든 슬라이드에 발표자 노트(`notes`) 필수 |
| 이미지·폰트 | `doc.assets` 에 data URI 로 임베드하고 `"asset:<키>"` 로 참조 |
| 텍스트 role | 제목·부제·본문 텍스트에 `role: title|subtitle|body|kicker` 부여 — 편집기 *레이아웃 적용*이 role 로 매칭 (1.0.18+) |
| 페이지·메타 | 페이지번호·제목·날짜는 텍스트에 `{{page}}` `{{pages}}` `{{title}}` `{{date}}` 토큰, 작성자·회사는 top-level `meta` + `{{author}}` `{{company}}` (1.0.18+) |
| 부록 슬라이드 | 발표에서 빼고 링크로만 가는 자료는 `hidden: true` (state 슬라이드와 다름) |
| 흐름도 화살표 | 요소 사이 선은 커넥터(`from`/`to: {el, side}`) — 요소 이동 시 따라감 |

## 읽기/쓰기 헬퍼

```python
import sys; sys.path.insert(0, r"C:\Users\kwcho\.claude\skills\bento-templates")
import bento_io

doc = bento_io.load("대상.bento.html")
doc["slides"][0]["name"] = "표지"
bento_io.save("대상.bento.html", doc)     # docId·collab·assets 보존, < 이스케이프

bento_io.check(doc, roles=True)          # notes 누락·여백 침범·role 누락 경고 목록
bento_io.runtime_version("대상.bento.html")   # 파일에 박힌 앱 버전 (예: '1.0.18')
bento_io.refresh_runtime("대상.bento.html")   # 앱 런타임만 최신으로 교체 (문서·docId·assets·title 보존, .bak 생성)
```

템플릿 파일 4종의 런타임: **1.0.18** (2026-08-18 갱신). 오래되면 `refresh_runtime` 으로 일괄 갱신.
