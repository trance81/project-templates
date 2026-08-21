# 기존 프로젝트 갱신 절차

이미 pjt-docs 구조를 도입한 프로젝트를 최신 표준에 맞추는 절차. AI에게 "pjt-docs 최신 표준으로
갱신해줘"라고 요청하면 이 절차를 따른다. 최초 도입은 [adopt.md](adopt.md)를 본다.

정본은 이 git 리포다. 갱신은 항상 리포를 최신으로 맞추는 것에서 시작한다.

## 0. 정본 최신화

```bash
cd <project-templates 클론 경로>   # 전역 CLAUDE.md 블록에 기록돼 있다
git pull --ff-only
```

로컬 클론 경로를 모르면 `~/.claude/CLAUDE.md`의 "프로젝트 지식관리 표준" 블록에서 확인한다.

## 1. 무엇이 프로젝트에 복사되는지 알기

표준 문서(`STRUCTURE.md`)는 프로젝트로 복사되지 않는다. 전역 CLAUDE.md가 리포를 가리키고
AI가 그때그때 읽는 구조라서, 리포를 pull 하면 저절로 최신이 된다. 따라서 **손으로 갱신해야
하는 대상은 프로젝트에 복사돼 굳어 있는 파일뿐이다.**

| 대상 | 갱신 방식 |
|---|---|
| `scripts/check-docs.py` | 정본으로 덮어쓴다. 프로젝트가 손대는 파일이 아니다 |
| `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/pjt-docs.mdc` | 규칙 줄만 대조해 빠진 것을 더한다. 프로젝트 고유 내용은 보존한다 |
| `.gitignore` | 빠진 줄만 더한다. 기존 줄은 지우지 않는다 |
| `pjt-docs/` 하위 문서 | **건드리지 않는다.** 프로젝트의 지식 그 자체다 |

`pjt-docs/HELP.md`처럼 템플릿에서 통째로 가져온 사람용 문서는, 프로젝트에서 고친 흔적이
없을 때만 정본으로 교체한다. 고친 흔적이 있으면 차이를 사용자에게 보여주고 판단을 받는다.

## 2. 대조

정본 `template/`과 프로젝트를 파일별로 대조한다. 표준이 바뀐 부분만 반영하고, 프로젝트가
의도적으로 다르게 둔 부분은 그대로 남긴다. 판단이 서지 않으면 덮어쓰지 말고 묻는다.

진입점 파일은 규칙 줄 단위로 비교한다. 정본에 있는데 프로젝트에 없는 줄이 이번에 추가된
표준이다. 반대로 프로젝트에만 있는 줄은 그 프로젝트 고유 규칙이므로 지우지 않는다.

## 3. 검사

```bash
python scripts/check-docs.py
```

갱신 전에도 한 번 돌려서 원래 있던 문제와 갱신이 만든 문제를 구분한다.

## 4. 마무리

- `pjt-docs/README.md` 상단의 `표준 갱신일`을 정본 `STRUCTURE.md`의 값과 맞춘다.
- `pjt-docs/CHANGELOG.md`에 무엇이 바뀌었는지 한 줄 남긴다.
- 커밋: `docs: pjt-docs 표준 갱신 (YYYY-MM-DD 기준)`

## 스킬 갱신은 따로다

`~/.claude/skills/`에 설치된 스킬은 프로젝트가 아니라 PC에 붙는다. 갱신은 sync가 한다.

```powershell
cd project-templates\global-skills
.\sync.ps1 -Update      # Windows
```

```bash
cd project-templates/global-skills
./sync.sh --update      # macOS / Linux
```

`--update`는 새로 설치하지 않고 이미 설치된 것만 최신으로 맞춘다. 리포에 소스가 있는 스킬은
내용을 대조해서 다를 때만 묻고 교체하므로, 로컬에서 고친 내용을 말없이 덮어쓰지 않는다.
외부 스킬은 내용을 대조할 수 없어서 설치 명령을 다시 실행할지 물어본다. 플러그인 갱신은
Claude Code를 재시작해야 반영된다.
