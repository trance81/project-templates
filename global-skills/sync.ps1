# 전역 플러그인/스킬 동기화 (Windows)
# manifest.json 과 로컬 상태를 비교해, 아직 결정 안 한 항목만 하나씩 물어보고 설치한다.
# 리포가 갱신된 뒤 재실행하면 새로 추가된 항목만 새로 물어본다(기존 결정은 재사용).
param(
    [switch]$Review,   # 과거에 "건너뜀" 한 항목도 다시 물어보고 싶을 때
    [switch]$Update,   # 설치는 하지 않고, 이미 설치된 것을 리포 최신 내용으로 갱신할 때
    [switch]$Yes,      # 묻지 않고 전부 y 로 답한다. 터미널이 아닌 곳에서 돌릴 때 쓴다
    [switch]$List,     # 아무것도 설치하지 않고, 물어볼 항목만 출력한다
    [string]$Only      # 지정한 id 만 묻지 않고 설치한다 (쉼표로 구분)
)
$ErrorActionPreference = "Stop"

# Git Bash 등을 거쳐 실행하면 콘솔 코드페이지가 cp949 라서 한글이 깨진다.
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# 이 스크립트는 항목마다 y/N 을 물어본다. 입력이 리다이렉트된 환경(파이프, `!` 프리픽스 등)에서는
# 물음에 답할 수 없는데, 그대로 두면 EOF 를 "아니오"로 읽어 묻지도 않은 항목을 skipped 로
# 기록해 버린다. 그런 결정이 상태 파일에 남으면 다음 실행 때 다시 묻지 않으므로 미리 막는다.
$OnlySet = $null
if ($Only) {
    $OnlySet = @($Only.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    $Yes = $true   # 고를 항목을 이미 받았으니 다시 묻지 않는다
}

if ([Console]::IsInputRedirected -and -not ($Yes -or $List)) {
    Write-Host "입력이 리다이렉트된 상태여서 y/N 을 물어볼 수 없다. 아무것도 바꾸지 않고 끝낸다." -ForegroundColor Yellow
    Write-Host "실제 터미널에서 실행하거나, 전부 설치할 생각이면 -Yes 를 붙여라."
    exit 2
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$manifestPath = Join-Path $PSScriptRoot "manifest.json"
$stateDir = Join-Path $HOME ".claude"
$statePath = Join-Path $stateDir "pjt-templates-skills-state.json"

# 정본은 이 git 리포다. 대조·갱신 전에 먼저 최신으로 맞춘다.
Write-Host "1) 리포 최신화 ($repoRoot)"
Push-Location $repoRoot
try { git pull --ff-only 2>&1 | Write-Host } catch { Write-Host "  경고: git pull 실패 — 로컬 내용으로 계속 진행" }
Pop-Location

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

if (-not (Test-Path $stateDir)) { New-Item -ItemType Directory -Path $stateDir | Out-Null }
if (Test-Path $statePath) {
    $state = Get-Content $statePath -Raw | ConvertFrom-Json -AsHashtable
} else {
    $state = @{}
}

function Save-State { $state | ConvertTo-Json -Depth 5 | Set-Content -Path $statePath -Encoding utf8 }

$failures = @()

# action 을 실행하고 결과를 state 에 남긴다. 실패해도 sync 전체를 멈추지 않는다.
function Install-Item($key, [scriptblock]$action) {
    try {
        & $action
        $state[$key] = "installed"
    } catch {
        Write-Host "  X 실패: $($_.Exception.Message)" -ForegroundColor Red
        $script:failures += $key
        $state.Remove($key)   # 결정을 남기지 않아 재실행 시 다시 묻는다
    }
    Save-State
}

function Ask-Install($id, $desc, $itemId) {
    if ($state.ContainsKey($id) -and -not $Review) {
        return $null   # 이미 결정됨 — 건너뜀 (조용히)
    }
    if ($null -ne $OnlySet -and $OnlySet -notcontains $itemId) {
        return $null   # 고르지 않은 항목은 결정도 남기지 않는다
    }
    Write-Host ""
    Write-Host "[$id]" -ForegroundColor Cyan
    Write-Host "  $desc"
    if ($Yes) { Write-Host "  설치할까? (y/N) y"; return $true }
    $ans = Read-Host "  설치할까? (y/N)"
    return ($ans -eq "y" -or $ans -eq "Y")
}

# manifest 의 path 는 manifest.json 이 있는 global-skills/ 기준 상대경로다.
$skillsBase = $PSScriptRoot

# 실행 중 저절로 생기는 것들. 대조에서 빼지 않으면 갱신할 게 없는데도 매번 "다르다"고 나온다.
$IgnoredDirs = @("__pycache__", ".git", "node_modules", ".venv")
$IgnoredNames = @(".DS_Store", "Thumbs.db")

# 폴더 안 모든 파일의 상대경로와 내용을 합쳐 해시한다. 내용이 같으면 같은 값이 나온다.
function Get-TreeHash($root) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $buf = [System.IO.MemoryStream]::new()
    Get-ChildItem -Recurse -File $root | Sort-Object FullName | ForEach-Object {
        $rel = $_.FullName.Substring($root.Length).TrimStart('\','/') -replace '\\','/'
        $parts = $rel.Split('/')
        if ($parts | Where-Object { $IgnoredDirs -contains $_ }) { return }
        if ($IgnoredNames -contains $_.Name) { return }
        if ($_.Extension -eq ".pyc") { return }
        $b = [System.Text.Encoding]::UTF8.GetBytes($rel)
        $buf.Write($b, 0, $b.Length)
        $c = [System.IO.File]::ReadAllBytes($_.FullName)
        $buf.Write($c, 0, $c.Length)
    }
    return [System.BitConverter]::ToString($sha.ComputeHash($buf.ToArray()))
}

# 홈에서 실행한다. `npx skills add` 류는 전역 플래그가 빠지면 현재 폴더에 설치하는데,
# 리포 안에서 sync 를 돌리는 게 보통이라 그대로 두면 리포를 오염시킨다.
function Invoke-InHome([string]$cmd) {
    Push-Location $HOME
    try { Invoke-Expression $cmd } finally { Pop-Location }
}

# 설치 명령이 성공했다고 해서 전역에 들어갔다는 보장이 없다. 실제로 확인한다.
function Assert-SkillInstalled($skillId) {
    if (-not (Test-Path (Join-Path $HOME ".claude\skills\$skillId"))) {
        throw "명령은 끝났지만 ~/.claude/skills/$skillId 가 없다. 설치 명령에 전역 플래그(-g)가 빠졌을 수 있다"
    }
}

function Confirm-Yes($prompt) {
    if ($Yes) { Write-Host "  $prompt (y/N) y  [-Yes]"; return $true }
    return (Read-Host "  $prompt (y/N)") -match '^[yY]$'
}

$installedMarketplaceIds = @{}
$mpF = Join-Path $HOME ".claude\plugins\known_marketplaces.json"
if (Test-Path $mpF) {
    (Get-Content $mpF -Raw | ConvertFrom-Json).PSObject.Properties.Name | ForEach-Object { $installedMarketplaceIds[$_] = $true }
}
$installedPluginIds = @{}
$plF = Join-Path $HOME ".claude\plugins\installed_plugins.json"
if (Test-Path $plF) {
    (Get-Content $plF -Raw | ConvertFrom-Json).plugins.PSObject.Properties.Name | ForEach-Object { $installedPluginIds[$_] = $true }
}

# 아직 설치도 안 됐고 결정도 안 난 항목인가. 물어볼 대상인지 판단한다.
function Test-Pending($kind, $itemId, $stateKey) {
    switch ($kind) {
        "marketplace" { if ($installedMarketplaceIds.ContainsKey($itemId)) { return $false } }
        "plugin"      { if ($installedPluginIds.ContainsKey($itemId)) { return $false } }
        "skill"       { if (Test-Path (Join-Path $HOME ".claude\skills\$itemId")) { return $false } }
    }
    return (-not $state.ContainsKey($stateKey)) -or $Review
}

if ($List) {
    # 아무것도 바꾸지 않고, 물어볼 항목만 보여준다. AI 가 이 목록을 사용자에게 제시하고
    # 답을 받아 -Only 로 되돌려주는 흐름을 염두에 둔 출력이다.
    $groups = @(
        @{ Label = "마켓플레이스"; Kind = "marketplace"; Items = $manifest.marketplaces },
        @{ Label = "플러그인";     Kind = "plugin";      Items = $manifest.plugins },
        @{ Label = "스킬";         Kind = "skill";       Items = $manifest.skills }
    )
    $total = 0
    foreach ($g in $groups) {
        $rows = @($g.Items | Where-Object { Test-Pending $g.Kind $_.id "$($g.Kind):$($_.id)" })
        if ($rows.Count -eq 0) { continue }
        Write-Host ""
        Write-Host "[$($g.Label)]" -ForegroundColor Cyan
        foreach ($i in $rows) {
            Write-Host "  $($i.id)"
            Write-Host "      $($i.desc)"
        }
        $total += $rows.Count
    }
    if ($total -eq 0) {
        Write-Host "설치할 새 항목이 없다. 전부 설치됐거나 이미 결정된 상태다."
    } else {
        Write-Host ""
        Write-Host "총 $total 건. 설치하려면 -Only 에 id 를 쉼표로 이어 넘긴다."
        Write-Host "예: -Only baton-init,hallmark"
    }
    exit 0
}

if ($Update) {
    Write-Host ""
    Write-Host "설치는 하지 않고, 이미 설치된 것만 갱신한다."

    Write-Host ""
    Write-Host "2) 마켓플레이스 갱신"
    $mpFile = Join-Path $HOME ".claude\plugins\known_marketplaces.json"
    if (Test-Path $mpFile) {
        Install-Item "update:marketplaces" { claude plugin marketplace update }
    } else { Write-Host "  설치된 마켓플레이스 없음" }

    Write-Host ""
    Write-Host "3) 플러그인 갱신"
    $installed = @{}
    $plFile = Join-Path $HOME ".claude\plugins\installed_plugins.json"
    if (Test-Path $plFile) {
        (Get-Content $plFile -Raw | ConvertFrom-Json).plugins.PSObject.Properties.Name | ForEach-Object { $installed[$_] = $true }
    }
    $targets = @($manifest.plugins | Where-Object { $installed.ContainsKey($_.id) })
    if ($targets.Count -eq 0) { Write-Host "  설치된 플러그인 없음" }
    foreach ($p in $targets) {
        Write-Host "  $($p.id)"
        Install-Item "update:plugin:$($p.id)" { claude plugin update $p.id }
    }

    Write-Host ""
    Write-Host "4) 스킬 갱신"
    foreach ($s in $manifest.skills) {
        $dest = Join-Path $HOME ".claude\skills\$($s.id)"
        if (-not (Test-Path $dest)) { continue }   # 설치 안 된 것은 갱신 대상이 아니다

        if ($s.installCmd) {
            # 정본이 외부에 있어 내용을 대조할 수 없다. 재실행 여부를 사용자에게 맡긴다.
            Write-Host ""
            Write-Host "[$($s.id)] 외부 스킬이라 최신 여부를 대조할 수 없다" -ForegroundColor Cyan
            Write-Host "  설치 명령: $($s.installCmd)"
            if (Confirm-Yes "설치 명령을 다시 실행할까?") {
                Install-Item "update:skill:$($s.id)" {
                    Invoke-InHome $s.installCmd
                    Assert-SkillInstalled $s.id
                }
            }
            continue
        }

        $src = Join-Path $skillsBase $s.path
        if (-not (Test-Path $src)) {
            Write-Host ""
            Write-Host "[$($s.id)] X 리포에 소스 폴더 없음: $src" -ForegroundColor Red
            $failures += "update:skill:$($s.id)"
            continue
        }
        if ((Get-TreeHash $src) -eq (Get-TreeHash $dest)) {
            Write-Host "  $($s.id): 최신"
            continue
        }

        # 내용이 다를 때만 묻는다. 로컬에서 손댄 내용을 말없이 덮어쓰지 않기 위해서다.
        Write-Host ""
        Write-Host "[$($s.id)] 리포 내용과 다르다" -ForegroundColor Cyan
        Write-Host "  $dest 를 리포 내용으로 교체한다. 로컬에서 고친 부분이 있으면 사라진다."
        if (-not (Confirm-Yes "교체할까?")) { Write-Host "  건너뜀"; continue }
        Install-Item "update:skill:$($s.id)" {
            Remove-Item -Recurse -Force $dest
            Copy-Item -Path $src -Destination $dest -Recurse
        }
    }

    Save-State
    if ($failures.Count -gt 0) {
        Write-Host ""
        Write-Host "경고: 실패 $($failures.Count)건 — $($failures -join ', ')" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "갱신 완료. 플러그인 갱신은 Claude Code 재시작 후 반영된다."
    exit $(if ($failures.Count -gt 0) { 1 } else { 0 })
}

Write-Host ""
Write-Host "2) 마켓플레이스 확인"
$installedMarketplaces = @{}
$mpFile = Join-Path $HOME ".claude\plugins\known_marketplaces.json"
if (Test-Path $mpFile) {
    (Get-Content $mpFile -Raw | ConvertFrom-Json).PSObject.Properties.Name | ForEach-Object { $installedMarketplaces[$_] = $true }
}
foreach ($m in $manifest.marketplaces) {
    $key = "marketplace:$($m.id)"
    if ($installedMarketplaces.ContainsKey($m.id)) {
        $state[$key] = "installed(기존)"
        continue
    }
    $want = Ask-Install $key $m.desc $m.id
    if ($null -eq $want) { continue }
    if ($want) {
        $src = if ($m.type -eq "github") { $m.repo } else { $m.url }
        Install-Item $key { claude plugin marketplace add $src }
    } else {
        $state[$key] = "skipped"
        Save-State
    }
}

Write-Host ""
Write-Host "3) 플러그인 확인"
$installedPlugins = @{}
$plFile = Join-Path $HOME ".claude\plugins\installed_plugins.json"
if (Test-Path $plFile) {
    (Get-Content $plFile -Raw | ConvertFrom-Json).plugins.PSObject.Properties.Name | ForEach-Object { $installedPlugins[$_] = $true }
}
foreach ($p in $manifest.plugins) {
    $key = "plugin:$($p.id)"
    if ($installedPlugins.ContainsKey($p.id)) {
        $state[$key] = "installed(기존)"
        continue
    }
    $want = Ask-Install $key $p.desc $p.id
    if ($null -eq $want) { continue }
    if ($want) {
        Install-Item $key { claude plugin install $p.id }
    } else {
        $state[$key] = "skipped"
        Save-State
    }
}

Write-Host ""
Write-Host "4) 스킬 확인 (installCmd 로 설치하거나, 이 리포에서 복사)"
foreach ($s in $manifest.skills) {
    $key = "skill:$($s.id)"
    $dest = Join-Path $HOME ".claude\skills\$($s.id)"
    if (Test-Path $dest) {
        $state[$key] = "installed(기존)"
        continue
    }
    $want = Ask-Install $key $s.desc $s.id
    if ($null -eq $want) { continue }
    if ($want) {
        Install-Item $key {
            if ($s.installCmd) {
                Invoke-InHome $s.installCmd
            } else {
                $src = Join-Path $skillsBase $s.path
                if (-not (Test-Path $src)) { throw "리포에 소스 폴더 없음: $src" }
                Copy-Item -Path $src -Destination $dest -Recurse
            }
            Assert-SkillInstalled $s.id
        }
    } else {
        $state[$key] = "skipped"
        Save-State
    }
}

Save-State
Write-Host ""
Write-Host "완료. 상태 기록: $statePath"
if ($failures.Count -gt 0) {
    Write-Host "경고: 실패 $($failures.Count)건 — $($failures -join ', ') — 재실행하면 다시 물어본다" -ForegroundColor Yellow
}
Write-Host "건너뛴 항목을 다시 검토하려면: .\sync.ps1 -Review"
