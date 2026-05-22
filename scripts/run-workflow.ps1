<#
.SYNOPSIS
    Trigger and watch the retrain workflow via GitHub CLI.
#>
param(
    [switch]$Force,
    [switch]$Watch
)

$ErrorActionPreference = "Stop"

# Check gh CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI not found. Install: winget install GitHub.cli"
    exit 1
}

# Check auth
$auth = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "==> Not authenticated. Running 'gh auth login'..." -ForegroundColor Yellow
    gh auth login
}

# Trigger
Write-Host "==> Triggering workflow 'train.yml'..." -ForegroundColor Cyan
if ($Force) {
    gh workflow run train.yml -f force=true
} else {
    gh workflow run train.yml
}

Start-Sleep -Seconds 3

# Get latest run
Write-Host "==> Latest runs:" -ForegroundColor Cyan
gh run list --workflow=train.yml --limit 3

if ($Watch) {
    Write-Host ""
    Write-Host "==> Watching latest run (Ctrl+C to stop)..." -ForegroundColor Cyan
    $runId = gh run list --workflow=train.yml --limit 1 --json databaseId --jq '.[0].databaseId'
    gh run watch $runId
}
