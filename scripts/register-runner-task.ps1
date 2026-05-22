#requires -RunAsAdministrator
<#
.SYNOPSIS
    Register already-configured runner as a Scheduled Task (auto-start at boot).
    Use this when svc.cmd is not available (newer runner versions).
#>
param(
    [string]$InstallPath = "D:\actions-runner",
    [string]$TaskName    = "GitHubActionsRunner"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path (Join-Path $InstallPath "run.cmd"))) {
    Write-Error "run.cmd not found at $InstallPath. Run config.cmd first."
    exit 1
}

if (-not (Test-Path (Join-Path $InstallPath ".runner"))) {
    Write-Error "Runner not configured (.runner file missing). Run config.cmd first."
    exit 1
}

$RunCmd = Join-Path $InstallPath "run.cmd"

Write-Host "==> Removing old task if exists..." -ForegroundColor Yellow
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

Write-Host "==> Registering '$TaskName'..." -ForegroundColor Yellow

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
    -Description "GitHub Actions self-hosted runner" | Out-Null

Write-Host "==> Starting task..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 5

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$proc = Get-Process -Name "Runner.Listener" -ErrorAction SilentlyContinue

if ($proc) {
    Write-Host ""
    Write-Host "==> SUCCESS - Runner is running" -ForegroundColor Green
    Write-Host "    Task:  $TaskName"
    Write-Host "    State: $($task.State)"
    Write-Host "    PID:   $($proc.Id)"
    Write-Host ""
    Write-Host "Verify at: https://github.com/coderiukl/rt-video-learning-analytics/settings/actions/runners"
} else {
    Write-Warning "Runner.Listener not detected yet. Check Task Scheduler -> $TaskName"
    Write-Host "Manual fallback: cd $InstallPath; .\run.cmd" -ForegroundColor Yellow
}
