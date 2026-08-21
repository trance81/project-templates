# 전역 플러그인/스킬 동기화 (Windows)
# manifest.json 과 로컬 상태를 비교해, 아직 결정 안 한 항목만 하나씩 물어보고 설치한다.
# 리포가 갱신된 뒤 재실행하면 새로 추가된 항목만 새로 물어본다(기존 결정은 재사용).
param(
    [switch]$Review,  # 과거에 "건너뜀" 한 항목도 다시 물어보고 싶을 때
    [switch]$Update   # 설치는 하지 않고, 이미 설치된 것을 리포 최신 내용으로 갱신할 때
)
$ErrorActionPreference = "Stop"

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

function Ask-Install($id, $desc) {
    if ($state.ContainsKey($id) -and -not $Review) {
        return $null   # 이미 결정됨 — 건너뜀 (조용히)
    }
    Write-Host ""
    Write-Host "[$id]" -ForegroundColor Cyan
    Write-Host "  $desc"
    $ans = Read-Host "  설치할까? (y/N)"
    return ($ans -eq "y" -or $ans -eq "Y")
}

# manifest 의 path 는 manifest.json 이 있는 global-skills/ 기준 상대경로다.
$skillsBase = $PSScriptRoot

# 폴더 안 모든 파일의 상대경로와 내용을 합쳐 해시한다. 내용이 같으면 같은 값이 나온다.
function Get-TreeHash($root) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $buf = [System.IO.MemoryStream]::new()
    Get-ChildItem -Recurse -File $root | Sort-Object FullName | ForEach-Object {
        $rel = $_.FullName.Substring($root.Length).TrimStart('\','/') -replace '\\','/'
        $b = [System.Text.Encoding]::UTF8.GetBytes($rel)
        $buf.Write($b, 0, $b.Length)
        $c = [System.IO.File]::ReadAllBytes($_.FullName)
        $buf.Write($c, 0, $c.Length)
    }
    return [System.BitConverter]::ToString($sha.ComputeHash($buf.ToArray()))
}

function Confirm-Yes($prompt) { return (Read-Host "  $prompt (y/N)") -match '^[yY]$' }

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
                Install-Item "update:skill:$($s.id)" { Invoke-Expression $s.installCmd }
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
    $want = Ask-Install $key $m.desc
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
    $want = Ask-Install $key $p.desc
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
    $want = Ask-Install $key $s.desc
    if ($null -eq $want) { continue }
    if ($want) {
        Install-Item $key {
            if ($s.installCmd) {
                Invoke-Expression $s.installCmd
            } else {
                $src = Join-Path $skillsBase $s.path
                if (-not (Test-Path $src)) { throw "리포에 소스 폴더 없음: $src" }
                Copy-Item -Path $src -Destination $dest -Recurse
            }
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
