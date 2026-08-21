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

받은 파일에는 쇼케이스 덱이 들어 있으므로 `#bento-doc` JSON을 통째로 교체한다.
`size`·`theme`(`theme.fontFamily` 포함)은 필수이고, `docId`·`collab` 은 넣지 않는다.

## 공통 사양

| 항목 | 값 |
|---|---|
| 캔버스 | 1280 × 720 (공식 템플릿 공통) |
| 여백 | 좌우 96px — 가장 오른쪽 요소의 `x + w` ≤ 1184 |
| 색상 | 강조색 1개, 서체 2개 이하 |
| 노트 | 모든 슬라이드에 발표자 노트(`notes`) 필수 |
| 이미지·폰트 | `doc.assets` 에 data URI 로 임베드하고 `"asset:<키>"` 로 참조 |

## 읽기/쓰기 헬퍼

```python
import sys; sys.path.insert(0, r"C:\Users\kwcho\.claude\skills\bento-templates")
import bento_io

doc = bento_io.load("대상.bento.html")
doc["slides"][0]["name"] = "표지"
bento_io.save("대상.bento.html", doc)     # docId·collab·assets 보존, < 이스케이프
```
