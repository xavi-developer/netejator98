<#
.SYNOPSIS
    Configures a Task Scheduler job to launch the Netejator98 Kiosk UI on user logon.
.DESCRIPTION
    Creates a scheduled task triggered at logon for all users in the interactive session.
.NOTES
    Must be run as an elevated Administrator.
#>

#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [string]$InstallDir = "C:\Program Files\Netejator98",
    [string]$TaskName = "Netejator98KioskPrompt"
)

$ErrorActionPreference = "Stop"

Write-Host "[+] Configuring Netejator98 Logon Task..." -ForegroundColor Cyan

$pythonExe = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
$exePath = Join-Path $InstallDir "netejator98.exe"

if (Test-Path $exePath) {
    $action = New-ScheduledTaskAction -Execute $exePath -Argument "ui"
} elseif ($pythonExe) {
    $action = New-ScheduledTaskAction -Execute $pythonExe -Argument "-m netejator98.main ui"
} else {
    Write-Error "Neither netejator98.exe nor python.exe was found."
    exit 1
}

# Trigger on logon of any user
$trigger = New-ScheduledTaskTrigger -AtLogOn

# Settings: run interactively in the user's desktop session, do not stop if battery, restart if fails
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -Priority 1 `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Principal: Users group (interactive logon session)
$principal = New-ScheduledTaskPrincipal -GroupId "BUILTIN\Users" -RunLevel Limited

# Register the scheduled task
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Launches the Netejator98 shared-PC kiosk prompt on user desktop logon."

Write-Host "[✓] Scheduled task '$TaskName' registered successfully!" -ForegroundColor Green

