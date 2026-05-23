# Deploy script chạy trên Windows host sau khi Jenkins build green.
# Cách dùng:
#   .\deploy.ps1                 # deploy nếu có build mới
#   .\deploy.ps1 -Force          # luôn deploy
#   .\deploy.ps1 -Watch          # poll mỗi 30s

[CmdletBinding()]
param(
    [switch]$Force,
    [switch]$Watch,
    [int]$IntervalSec = 30
)

$ErrorActionPreference = "Stop"
$markerFile = ".\.last-deployed-build"
$jenkinsVolume = "rt-video-learning-analytics_jenkins-data"

function Get-LastGreenBuild {
    $out = docker run --rm -v "${jenkinsVolume}:/jh" alpine sh -c "cat /jh/last-green-build 2>/dev/null || echo ''"
    return $out.Trim()
}

function Get-LastDeployed {
    if (Test-Path $markerFile) { (Get-Content $markerFile).Trim() } else { "" }
}

function Invoke-Deploy {
    param([string]$BuildNum)
    Write-Host "==> Deploying build #$BuildNum" -ForegroundColor Cyan
    docker compose up -d --no-deps --force-recreate backend frontend
    if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }
    Set-Content -Path $markerFile -Value $BuildNum -NoNewline
    Write-Host "==> Deploy OK. backend=8000 frontend=5173" -ForegroundColor Green
    docker compose ps
}

function Try-Deploy {
    $latest = Get-LastGreenBuild
    if ([string]::IsNullOrEmpty($latest)) {
        Write-Host "No green build yet (Jenkins chưa thành công lần nào)." -ForegroundColor Yellow
        return
    }
    $deployed = Get-LastDeployed
    if (-not $Force -and $latest -eq $deployed) {
        Write-Host "Build #$latest đã được deploy. Bỏ qua." -ForegroundColor DarkGray
        return
    }
    Invoke-Deploy -BuildNum $latest
}

if ($Watch) {
    Write-Host "Watching for new Jenkins builds (Ctrl+C to stop)..." -ForegroundColor Cyan
    while ($true) {
        try { Try-Deploy } catch { Write-Warning $_.Exception.Message }
        Start-Sleep -Seconds $IntervalSec
    }
} else {
    Try-Deploy
}
