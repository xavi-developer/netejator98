<#
.SYNOPSIS
    Installs the Netejator98 Privileged Agent Service on Windows 10/11.
.DESCRIPTION
    Sets up C:\ProgramData\netejator98 with restricted ACLs, installs the Python
    package or standalone executable, and configures the background Windows Service.
.NOTES
    Must be run as an elevated Administrator.
#>

#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [string]$InstallDir = "C:\Program Files\Netejator98",
    [string]$DataDir = "C:\ProgramData\netejator98",
    [string]$ServiceName = "Netejator98Agent"
)

$ErrorActionPreference = "Stop"

Write-Host "[+] Installing Netejator98 Windows Service..." -ForegroundColor Cyan

# 1. Create secure data directory with restricted ACLs
if (!(Test-Path -Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
}

Write-Host "[+] Configuring secure ACLs on $DataDir..." -ForegroundColor Yellow
$acl = Get-Acl $DataDir
$acl.SetAccessRuleProtection($true, $false) # Disable inheritance and remove inherited rules
$adminGroup = New-Object System.Security.Principal.NTAccount("BUILTIN\Administrators")
$systemGroup = New-Object System.Security.Principal.NTAccount("NT AUTHORITY\SYSTEM")
$adminAccess = New-Object System.Security.AccessControl.FileSystemAccessRule($adminGroup, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$systemAccess = New-Object System.Security.AccessControl.FileSystemAccessRule($systemGroup, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.AddAccessRule($adminAccess)
$acl.AddAccessRule($systemAccess)
Set-Acl -Path $DataDir -AclObject $acl

# 2. Copy default policy
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$defaultPolicy = Join-Path $repoRoot "policies\defaults\windows.yaml"
$targetConfig = Join-Path $DataDir "config.yaml"

if ((Test-Path $defaultPolicy) -and !(Test-Path $targetConfig)) {
    Copy-Item -Path $defaultPolicy -Destination $targetConfig
    Write-Host "[+] Default Windows cleaning policy copied to $targetConfig" -ForegroundColor Green
}

# 2.1 Initialize daemon state (disabled by default)
$targetState = Join-Path $DataDir "daemon_state.json"
if (!(Test-Path $targetState)) {
    Set-Content -Path $targetState -Value '{"enabled": false}' -Encoding UTF8
    Write-Host "[+] Initialized daemon_state.json (daemon disabled by default)" -ForegroundColor Green
}

# 3. Register and Start Windows Service
# If compiled binary exists, use it; otherwise use python -m netejator98.main
$pythonExe = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
$exePath = Join-Path $InstallDir "netejator98.exe"

if (Test-Path $exePath) {
    $binaryPath = "`"$exePath`" agent --storage `"$DataDir`""
} elseif ($pythonExe) {
    $binaryPath = "`"$pythonExe`" -m netejator98.main agent --storage `"$DataDir`""
} else {
    Write-Error "Neither netejator98.exe nor python.exe was found on PATH."
    exit 1
}

# Check if service already exists
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "[*] Stopping existing service $ServiceName..." -ForegroundColor Yellow
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

Write-Host "[+] Creating Windows Service '$ServiceName'..." -ForegroundColor Cyan
sc.exe create $ServiceName binPath= $binaryPath start= auto DisplayName= "Netejator98 Privileged Agent" obj= "NT AUTHORITY\SYSTEM"
sc.exe description $ServiceName "Secures shared PC workstations by running session identification and sanitisation."

# Configure failure recovery: restart after 5 seconds
sc.exe failure $ServiceName reset= 86400 actions= restart/5000/restart/5000/restart/5000

Write-Host "[+] Starting service $ServiceName..." -ForegroundColor Green
Start-Service -Name $ServiceName

Write-Host "[✓] Netejator98 Agent service installed and started successfully!" -ForegroundColor Green

