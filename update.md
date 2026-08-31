# 기존 프로젝트 갱신 절차

이미 pjt-docs 구조를 도입한 프로젝트를 최신 표준에 맞추는 절차. AI에게 "pjt-docs 최신 표준으로
갱신해줘"라고 요청하면 이 절차를 따른다. 최초 도입은 [adopt.md](adopt.md)를 본다.

기준이 되는 것은 이 git 저장소다. 갱신은 항상 저장소를 최신으로 맞추는 것에서 시작한다.

## 0. 기준 저장소 최신화

```bash
cd <project-templates 클론 경로>   # 전역 CLAUDE.md 블록에 기록돼 있다
git pull --ff-only
```

로컬 클론 경로를 모르면 `~/.claude/CLAUDE.md`의 "프로젝트 지식관리 표준" 블록에서 확인한다.

## 1. 무엇이 프로젝트에 복사되는지 알기

표준 문서(`STRUCTURE.md`)는 프로젝트로 복사되지 않는다. 전역 CLAUDE.md가 저장소를 가리키고
AI가 그때그때 읽는 구조라서, 저장소를 pull 하면 저절로 최신이 된다. 따라서 **손으로 갱신해야
하는 대상은 프로젝트에 복사돼 굳어 있는 파일뿐이다.**

| 대상 | 갱신 방식 |
|---|---|
| `scripts/check-docs.py` | 저장소의 최신 파일로 덮어쓴다. 프로젝트가 손대는 파일이 아니다 |
| `CLAUDE.md`, `AGENTS.md` | 규칙 줄만 대조해 빠진 것을 더한다. 프로젝트 고유 내용은 보존한다 |
| `.gitignore` | 빠진 줄만 더한다. 기존 줄은 지우지 않는다 |
| `.baton/` | 없으면 `baton-init` 스킬로 만든다 (아래 참조). 있으면 배턴 파일의 내용은 손대지 않되, 구 구조(사용자 폴더 없음, `status` 어휘 다름)면 스킬이 사용자 확인 후 옮긴다 |
| `scripts/baton-hook.mjs`, `.claude/settings.json`의 훅 | 스킬이 최신으로 맞춘다. 구 버전 `baton-stop-hook.mjs`와 구 버전이 설치한 git pre-commit 은 지운다 |
| `pjt-docs/` 하위 문서 | **건드리지 않는다.** 프로젝트의 지식 그 자체다 |

`pjt-docs/HELP.md`처럼 템플릿에서 통째로 가져온 사람용 문서는, 프로젝트에서 고친 흔적이
없을 때만 저장소의 최신 파일로 교체한다. 고친 흔적이 있으면 차이를 사용자에게 보여주고 판단을 받는다.

### .baton/이 없으면 이 단계에서 도입한다

`.baton/`은 표준의 기본 구성이므로, 갱신 대상 프로젝트에 없으면 이때 만든다. 직접 파일을
쓰지 말고 `baton-init` 스킬을 실행한다. 그 스킬이 `.baton/README.md` 작성, 진입점 포인터 줄
추가, 세션 시작·턴 종료 훅 등록, `.gitignore` 정리를 한 번에 처리하며, 이미 있는 조각은
건드리지 않는다.

이미 `.baton/`이 있는 프로젝트라면 그 안의 배턴 파일 **내용**은 손대지 않는다. `pjt-docs/`
하위 문서와 같은 이유로, 그 프로젝트의 작업 기록 그 자체다. 다만 다음 두 경우는 구 구조이므로
`baton-init` 스킬을 다시 실행해 옮긴다. 스킬이 옮길 목록을 보여주고 사용자 확인을 받는다.

- `.baton/` 최상위에 배턴 파일이 바로 있다 (사용자 폴더 `<이름>/` 없음)
- `status` 값이 `running | waiting | passed`가 아니다 (예: `in-progress | done`)
- 훅이 `PreToolUse`나 `StopFailure`에 걸려 있거나 스크립트 이름이 `baton-stop-hook.mjs`다.
  새 스크립트는 `SessionStart`와 `Stop` 둘만 처리하므로 나머지 이벤트 항목은 지운다
- `.git/hooks/pre-commit`(또는 husky 등)에 `baton-hook.mjs --pre-commit` 호출이 남아 있다.
  새 스크립트에는 그 진입점이 없어서 그대로 두면 커밋할 때마다 오류가 난다. 그 줄을 지운다

`.baton/`이 `.gitignore`나 `.git/info/exclude`에 통째로 올라 있으면 제외를 푼다. 수정 이력이
배턴에 쌓이는 구조라 git 밖에 두면 다른 PC와 팀원이 볼 수 없다. pjt-docs가 독립 저장소인
구성이면 `.baton/`을 그 저장소 안으로 옮긴다.

## 2. 대조

저장소의 `template/`과 프로젝트를 파일별로 대조한다. 표준이 바뀐 부분만 반영하고, 프로젝트가
의도적으로 다르게 둔 부분은 그대로 남긴다. 판단이 서지 않으면 덮어쓰지 말고 묻는다.

진입점 파일은 규칙 줄 단위로 비교한다. 템플릿에 있는데 프로젝트에 없는 줄이 이번에 추가된
표준이다. 반대로 프로젝트에만 있는 줄은 그 프로젝트 고유 규칙이므로 지우지 않는다.

## 3. 검사

```bash
python scripts/check-docs.py
```

갱신 전에도 한 번 돌려서 원래 있던 문제와 갱신이 만든 문제를 구분한다.

## 4. 마무리

- `pjt-docs/README.md` 상단의 `표준 갱신일`을 기준 문서 `STRUCTURE.md`의 값과 맞춘다.
- 커밋: `docs: pjt-docs 표준 갱신 (YYYY-MM-DD 기준)`
- 훅 설정이 바뀌었으면 Claude Code를 재시작한다. 세션 시작 때 읽은 훅 설정을 그 세션 동안
  쓰기 때문에, 재시작 전에는 새 훅이 돌지 않고 지운 구 스크립트를 찾는 오류가 보일 수 있다

## 스킬 갱신은 따로다

`~/.claude/skills/`에 설치된 스킬은 프로젝트가 아니라 PC에 붙는다. `baton-init` 스킬을 최신으로
맞추려면 클론해 둔 project-templates 에서 `git pull` 한 뒤 세팅 스크립트를 다시 실행한다.

```powershell
cd project-templates
git pull
.\setup.ps1        # Windows
```

```bash
cd project-templates
git pull
./setup.sh         # macOS / Linux
```

스크립트는 전역 지시가 이미 있으면 건너뛰고, 스킬은 내용이 다를 때만 다시 복사한다.
