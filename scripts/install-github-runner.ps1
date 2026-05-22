#requires -RunAsAdministrator
<#
.SYNOPSIS
    Install GitHub Actions self-hosted runner on Windows.

.DESCRIPTION
    Downloads, extracts, configures, and starts the runner as a service.
    Token must be generated from: Repo -> Settings -> Actions -> Runners -> New self-hosted runner

.EXAMPLE
    .\install-github-runner.ps1 -Token "ABCDEF123..." -RunnerName "ml-runner"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Token,

    [string]$RepoUrl = "https://github.com/coderiukl/rt-video-learning-analytics",

    [string]$InstallPath = "D:\actions-runner",

    [string]$RunnerName = $env:COMPUTERNAME,

    [string]$Labels = "self-hosted,windows,x64,ml",

    [string]$RunnerVersion = "2.319.1"
)

$ErrorActionPreference = "Stop"

Write-Host "==> GitHub Actions Runner Setup" -ForegroundColor Cyan
Write-Host "    Repo:    $RepoUrl"
Write-Host "    Path:    $InstallPath"
Write-Host "    Name:    $RunnerName"
Write-Host "    Labels:  $Labels"
Write-Host ""

# 1. Create install directory
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
}
Set-Location $InstallPath

# 2. Download runner if missing
$ZipFile = "actions-runner-win-x64-$RunnerVersion.zip"
$DownloadUrl = "https://github.com/actions/runner/releases/download/v$RunnerVersion/$ZipFile"

if (-not (Test-Path "config.cmd")) {
    Write-Host "==> Downloading runner v$RunnerVersion..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipFile -UseBasicParsing

    Write-Host "==> Extracting..." -ForegroundColor Yellow
    Expand-Archive -Path $ZipFile -DestinationPath . -Force
    Remove-Item $ZipFile
} else {
    Write-Host "==> Runner files already present, skipping download" -ForegroundColor Green
}

# 3. Remove old config if present
if (Test-Path ".runner") {
    Write-Host "==> Removing previous registration..." -ForegroundColor Yellow
    try { .\svc.cmd stop 2>&1 | Out-Null } catch {}
    try { .\svc.cmd uninstall 2>&1 | Out-Null } catch {}
    .\config.cmd remove --token $Token 2>&1 | Out-Null
}

# 4. Configure
Write-Host "==> Configuring runner..." -ForegroundColor Yellow
.\config.cmd `
    --url $RepoUrl `
    --token $Token `
    --name $RunnerName `
    --labels $Labels `
    --work "_work" `
    --unattended `
    --replace

if ($LASTEXITCODE -ne 0) {
    Write-Error "Runner configuration failed"
    exit 1
}

# 5. Register as scheduled task (auto-start at boot, run as SYSTEM)
$TaskName = "GitHubActionsRunner_$RunnerName"
$RunCmd   = Join-Path $InstallPath "run.cmd"

Write-Host "==> Registering scheduled task '$TaskName'..." -ForegroundColor Yellow

# Remove existing task if any
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$action    = New-ScheduledTaskAction -Execute $RunCmd -WorkingDirectory $InstallPath
$trigger   = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings  = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 0)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "GitHub Actions self-hosted runner for $RepoUrl" | Out-Null

Write-Host "==> Starting task..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 5

# 6. Verify
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$proc = Get-Process -Name "Runner.Listener" -ErrorAction SilentlyContinue

if ($task -and $proc) {
    Write-Host ""
    Write-Host "==> SUCCESS - Runner is running" -ForegroundColor Green
    Write-Host "    Task:    $TaskName"
    Write-Host "    State:   $($task.State)"
    Write-Host "    PID:     $($proc.Id)"
    Write-Host ""
    Write-Host "Next: visit $RepoUrl/settings/actions/runners - runner should show 'Idle'"
    Write-Host ""
    Write-Host "Manage task:"
    Write-Host "  Stop:    Stop-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Start:   Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Remove:  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
} else {
    Write-Warning "Runner process not detected. Check Task Scheduler and $InstallPath\_diag\ logs"
    Write-Host "Manual start: cd $InstallPath; .\run.cmd" -ForegroundColor Yellow
    exit 1
}
