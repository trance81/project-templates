<div align="center">

# project-templates

**AI와 사람이 같은 문서를 읽는 프로젝트 지식관리 표준**

지식은 `pjt-docs/`에, 진행 중인 작업은 `.baton/`에. 도구 폴더에 가두지 않는다.

</div>

---

## 설치

새 PC의 Claude Code(또는 다른 AI CLI)에 이 한 줄을 던지면 끝난다.

```
https://github.com/trance81/project-templates.git 클론해서 SETUP.md대로 전역 세팅해줘
```

AI가 리포를 클론하고, 전역 지시를 등록하고, 설치할 스킬 목록을 보여주며 **한 번만** 묻는다.
답하면 나머지는 알아서 끝낸다. 절차 정본은 [SETUP.md](SETUP.md)에 있다.

세팅이 끝나면 어느 프로젝트에서 작업하든 AI가 이 구조를 알아서 인지하고 유지한다.

## 갱신

갱신 대상이 셋이고 서로 다르다. 무엇을 고쳤느냐에 따라 손댈 곳이 갈린다.

| 무엇을 | 언제 | 어떻게 |
|---|---|---|
| **표준 문서** | 리포에 커밋이 올라갈 때마다 | 따로 할 일 없음 |
| **PC의 스킬·플러그인** | 스킬 내용이나 목록이 바뀐 뒤 | `sync -Update` |
| **각 프로젝트의 구조** | 표준 갱신일이 올라간 뒤 | AI에게 한마디 |

**표준 문서는 저절로 따라온다.** 전역 지시가 로컬 클론 경로를 가리키고 AI가 그때그때
`STRUCTURE.md`를 읽는 구조라, 복사본이 어딘가 굳어 있지 않다. `sync`가 실행 첫 단계에서
`git pull`을 돌리므로 아래 둘 중 무엇을 하든 함께 최신이 된다.

**PC의 스킬·플러그인**은 이렇게 갱신한다. 새로 설치하지는 않고 이미 있는 것만 손댄다.

```powershell
cd global-skills; .\sync.ps1 -Update        # Windows
```
```bash
cd global-skills && ./sync.sh --update      # macOS / Linux
```

리포에 소스가 있는 스킬은 내용까지 대조해서 **다를 때만** 묻고 교체하므로, 로컬에서 고친
부분이 말없이 사라지지 않는다. 외부 스킬은 대조할 수 없어 설치 명령을 다시 돌릴지 물어본다.
플러그인 갱신은 Claude Code를 재시작해야 반영된다.

**각 프로젝트의 구조**는 그 프로젝트에서 AI에게 말하면 된다.

```
pjt-docs 최신 표준으로 갱신해줘
```

먼저 말하지 않아도 AI가 알아챈다. 각 프로젝트 `pjt-docs/README.md` 상단의 `표준 갱신일`을
[STRUCTURE.md](STRUCTURE.md)의 값과 비교해, 오래됐거나 아예 없으면 갱신을 제안한다.

갱신이 손대는 것은 템플릿에서 복사돼 굳은 파일뿐이다. `check-docs.py`, 진입점 두 곳의 규칙 줄,
`.gitignore`, 그리고 `.baton/`이 없으면 그것까지. **`pjt-docs/` 안의 문서와 기존 배턴 파일은
건드리지 않는다** — 그 프로젝트의 지식이자 작업 기록 그 자체이기 때문이다. 절차 정본은
[update.md](update.md)에 있다.

## 왜 필요한가

프로젝트 지식이 `.claude/`나 흩어진 md 파일에 쌓이면 세 가지가 무너진다.

- **도구에 묶인다.** Cursor로 열면 Claude가 쌓아둔 걸 못 읽는다.
- **기기에 묶인다.** 회사 PC의 맥락이 집 PC에 없다.
- **"왜"가 사라진다.** 코드에는 결과만 남고 판단 근거는 남지 않아, AI가 그 이유를 모른 채
  리팩토링으로 지워버린다.

`pjt-docs/`는 일반 폴더의 마크다운이다. git으로 따라다니고, 어떤 AI든 읽고, 사람도 읽는다.

## 두 레인

확정된 지식과 진행 중인 작업은 성격이 다르다. 그래서 자리도 나눈다.

| | `pjt-docs/` | `.baton/` |
|---|---|---|
| 담는 것 | 검증을 마친 확정 지식 | 아직 진행 중인 작업 상태 |
| 쓰는 주체 | 사람이 정제해서 남긴다 | 모델이 세션마다 갱신한다 |
| 언제 읽나 | 작업 전에 관련 문서를 | 세션 시작 때 `running`·`waiting`만 |
| 검사 | `check-docs.py` 대상 | 검사하지 않음 |

둘 다 기본 구성이라 도입할 때도 갱신할 때도 함께 처리한다. 배턴이 끝나면(`status: passed`)
지우지 않고, 그중 재사용할 가치가 있는 내용만 `pjt-docs/`로 **복사**해 올린다.

## 무엇이 생기나

```
<프로젝트루트>/
  CLAUDE.md · AGENTS.md                     얇은 진입점 — 지식 본문은 금지
  scripts/check-docs.py                     정합성 검사
  pjt-docs/
    README.md      지식 지도 — 표에 없는 문서는 없는 문서다
    CHANGELOG.md   지식이 왜 어떻게 바뀌었나
    HELP.md        사람용 치트시트
    overview.md    프로젝트 개요
    decisions/     왜 그렇게 정했나 + 언제 다시 논의하나
    domain/        업무 규칙·용어·프로세스
    reference/     외부 자료 (원본 보존 + 변환본)
    skills/        다른 프로젝트에 가져갈 노하우
    troubleshooting/
    local/         git 미추적 — 접속정보·개인메모
  .baton/
    README.md      운영 규칙
    <slug>.md      작업 단위 진행상태
```

빈 폴더는 만들지 않는다. 해당 유형의 지식이 처음 생길 때 만든다.

## 쓰는 법

전역 세팅이 끝났으면 AI에게 말로 시키면 된다.

| 하고 싶은 것 | AI에게 |
|---|---|
| 새 프로젝트에 도입 | `이 프로젝트에 pjt-docs 구조 도입해줘` |
| 기존 프로젝트에 도입 | 같은 말. 흩어진 지식을 유형별로 이관한다 ([adopt.md](adopt.md)) |
| 표준이 바뀐 뒤 갱신 | `pjt-docs 최신 표준으로 갱신해줘` (위 [갱신](#갱신) 참조) |
| 이 프로젝트에 baton만 | `이 프로젝트에 baton 추가해줘` |

`decisions/`에 남길 판단이 생기면 그때그때 AI에게 적어달라고 하면 된다. 표준이 요구하는
프론트매터와 인덱스 등재, CHANGELOG 갱신을 같이 처리한다.

<details>
<summary><b>PC의 스킬·플러그인 동기화</b></summary>

<br>

`global-skills/manifest.json`이 이 리포로 관리하는 마켓플레이스·플러그인·스킬 목록이다.
새 PC에서, 혹은 목록이 갱신된 뒤 실행하면 **아직 결정하지 않은 항목만** 물어본다.

```powershell
cd global-skills; .\sync.ps1        # Windows
```
```bash
cd global-skills && ./sync.sh       # macOS / Linux
```

| 옵션 | 하는 일 |
|---|---|
| `-List` / `--list` | 아무것도 바꾸지 않고 설치 후보만 출력 |
| `-Only a,b` / `--only a,b` | 고른 id만 묻지 않고 설치 |
| `-Yes` / `--yes` | 전부 묻지 않고 설치 (터미널이 아닌 곳에서) |
| `-Update` / `--update` | 새로 설치하지 않고 이미 설치된 것만 최신화 |
| `-Review` / `--review` | 과거에 건너뛴 항목도 다시 검토 |

결정은 `~/.claude/pjt-templates-skills-state.json`에 남아 재실행해도 다시 묻지 않는다.
`-Update`는 리포에 소스가 있는 스킬을 내용까지 대조해 **다를 때만** 교체하므로, 로컬에서
고친 내용을 말없이 덮어쓰지 않는다.

새 플러그인을 설치했으면 `manifest.json`에 항목을 추가해 다른 PC에도 전파되게 한다.

</details>

<details>
<summary><b>정합성 검사</b></summary>

<br>

```bash
python scripts/check-docs.py
```

프론트매터 누락, README 인덱스와 실제 파일의 불일치, 깨진 상대 링크, `status: active`인데
오래 방치된 문서를 잡는다. `pjt-docs/local/`과 `reference/원본/`은 검사에서 뺀다.

</details>

<details>
<summary><b>리포 구성</b></summary>

<br>

| 파일 | 설명 |
|---|---|
| [STRUCTURE.md](STRUCTURE.md) | 구조 표준 정의서 — **정본** |
| [template/](template/) | 새 프로젝트에 복사하는 뼈대 |
| [adopt.md](adopt.md) | 기존 프로젝트에 도입하는 절차 |
| [update.md](update.md) | 이미 도입한 프로젝트를 최신 표준으로 갱신하는 절차 |
| [SETUP.md](SETUP.md) | PC 전역 세팅 절차 |
| [global-skills/](global-skills/) | 플러그인·스킬 목록과 동기화 스크립트 |
| [global-skills/skills/baton-init/](global-skills/skills/baton-init/) | `.baton/` 도입 스킬 |

</details>
