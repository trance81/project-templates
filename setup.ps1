# project-templates 전역 세팅 (Windows)
# ~/.claude/CLAUDE.md 에 표준 참조 블록을 추가한다. 이미 있으면 건너뛴다.
$ErrorActionPreference = "Stop"

$repoPath = $PSScriptRoot
$claudeDir = Join-Path $HOME ".claude"
$globalMd = Join-Path $claudeDir "CLAUDE.md"
$marker = "## 프로젝트 지식관리 표준 (project-templates)"

if (-not (Test-Path $claudeDir)) { New-Item -ItemType Directory -Path $claudeDir | Out-Null }
if ((Test-Path $globalMd) -and (Select-String -Path $globalMd -SimpleMatch $marker -Quiet)) {
    Write-Host "이미 등록됨: $globalMd"
} else {
    $block = @"

$marker
- 정본: https://github.com/trance81/project-templates.git (로컬: $repoPath)
- 새 프로젝트 시작, 기존 프로젝트 분석/개발 시 STRUCTURE.md의 pjt-docs/ 구조로 지식을 구성·유지할 것
- 프로젝트에 pjt-docs/가 없으면 도입을 제안할 것
- ~/.claude/pjt-templates-skills-state.json 이 없으면(스킬 동기화를 한 번도 안 돌린 PC) global-skills/sync 실행을 먼저 안내할 것
"@
    Add-Content -Path $globalMd -Value $block -Encoding utf8
    Write-Host "등록 완료: $globalMd"
}
Write-Host ""
Write-Host "Cursor는 수동 등록 필요 — SETUP.md의 Cursor 절 참조 (Settings > Rules > User Rules)"
