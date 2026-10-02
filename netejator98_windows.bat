<# :
@echo off
set "bat_path=%~f0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Command -ScriptBlock ([scriptblock]::Create([System.IO.File]::ReadAllText($env:bat_path)))"
pause
exit /b
#>

# ==============================================================================
# CONFIGURACIO DE L'EXECUCIO
# ==============================================================================
$DryRun = $false          # Canvia a $true per fer una simulacio sense esborrar res
$VerboseMode = $true      # Canvia a $false si no vols veure la llista de fitxers
$TargetHome = $HOME

$ErrorActionPreference = "SilentlyContinue"

# ==============================================================================
# OBJECTIUS DE NETEJA CONFIGURATS (JSON)
# ==============================================================================
$ObjectivesJson = @"
[
  { "name": "UserDocuments", "os": "Windows", "category": "USER_DOCUMENTS", "strategy": "PURGE_CHILDREN", "patterns": ["*", "Desktop/*", "Documents/*", "Downloads/*", "Pictures/*", "Videos/*", "Music/*"] },
  { "name": "DesktopShortcuts", "os": "Windows", "category": "DESKTOP_SHORTCUTS", "strategy": "STANDARD", "patterns": ["Desktop/*.lnk", "Desktop/*.url"] },
  { "name": "RecycleBin", "os": "Windows", "category": "RECYCLE_BIN", "strategy": "EMPTY_TRASH", "patterns": ["C:/`$Recycle.Bin/*"] },
  { "name": "CachesAndTemp", "os": "Windows", "category": "TEMP_AND_CACHE", "strategy": "PURGE_CHILDREN", "patterns": ["AppData/Local/Temp/*", "AppData/Local/CrashDumps/*", "AppData/Local/Microsoft/Windows/Explorer/thumbcache_*.db"] },
  { "name": "BrowserProfiles", "os": "Windows", "category": "BROWSER_PROFILES", "strategy": "BROWSER_CLEAN", "patterns": ["AppData/Local/Google/Chrome/User Data/*", "AppData/Local/Microsoft/Edge/User Data/*", "AppData/Roaming/Mozilla/Firefox/Profiles/*", "AppData/Local/BraveSoftware/Brave-Browser/User Data/*"] },
  { "name": "BrowserGoogleChrome", "os": "Windows", "category": "BROWSER_PROFILES", "strategy": "BROWSER_CLEAN", "patterns": ["AppData/Local/Google/Chrome/User Data/Default/Bookmarks*", "AppData/Local/Google/Chrome/User Data/Default/History*", "AppData/Local/Google/Chrome/User Data/Default/Favicons*", "AppData/Local/Google/Chrome/User Data/Default/Cookies*", "AppData/Local/Google/Chrome/User Data/Default/Network/Cookies*", "AppData/Local/Google/Chrome/User Data/Default/Login Data*", "AppData/Local/Google/Chrome/User Data/Default/Web Data*", "AppData/Local/Google/Chrome/User Data/Default/Sessions/*", "AppData/Local/Google/Chrome/User Data/Default/Cache/*"] },
  { "name": "BrowserMozillaFirefox", "os": "Windows", "category": "BROWSER_PROFILES", "strategy": "BROWSER_CLEAN", "patterns": ["AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/places.sqlite*", "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/cookies.sqlite*", "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/logins.json", "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/sessionstore*", "AppData/Local/Mozilla/Firefox/Profiles/*.default*/cache2/*"] },
  { "name": "BrowserMicrosoftEdge", "os": "Windows", "category": "BROWSER_PROFILES", "strategy": "BROWSER_CLEAN", "patterns": ["AppData/Local/Microsoft/Edge/User Data/Default/Bookmarks*", "AppData/Local/Microsoft/Edge/User Data/Default/History*", "AppData/Local/Microsoft/Edge/User Data/Default/Cookies*", "AppData/Local/Microsoft/Edge/User Data/Default/Login Data*", "AppData/Local/Microsoft/Edge/User Data/Default/Cache/*"] },
  { "name": "RecentFiles", "os": "Windows", "category": "RECENT_FILES", "strategy": "TRUNCATE", "patterns": ["AppData/Roaming/Microsoft/Windows/Recent/*", "AppData/Roaming/Microsoft/Office/Recent/*"] },
  { "name": "UserCredentials", "os": "Windows", "category": "CREDENTIALS", "strategy": "SHRED_NIST", "patterns": [".ssh/*", ".aws/*", "AppData/Roaming/GitHub CLI/*", "_netrc"] },
  { "name": "CloudSync", "os": "Windows", "category": "CLOUD_SYNC", "strategy": "CLOUD_WIPE", "patterns": ["OneDrive/*", "Dropbox/*", "AppData/Local/Google/DriveFS/*"] },
  { "name": "ShellHistory", "os": "Windows", "category": "SHELL_HISTORY", "strategy": "TRUNCATE", "patterns": ["AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt"] },
  { "name": "CustomWorkspace", "os": "Windows", "category": "CUSTOM", "strategy": "CUSTOM_CLEAN", "patterns": ["Workspace/*", "Projects/*"] }
]
"@

# ==============================================================================
# SEGURETAT I UTILITATS
# ==============================================================================
if (-not (Test-Path $TargetHome)) {
    Write-Host "Error: El directori d'usuari especificat no existeix: $TargetHome" -ForegroundColor Red
    exit 1
}
$TargetHome = (Resolve-Path$TargetHome).Path

function Is-ProtectedPath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path) -or$Path -eq "C:\" -or $Path -eq$TargetHome) { return $true }$ProtectedRoots = @("C:\Windows", "C:\Program Files", "C:\Program Files (x86)", "C:\ProgramData")
    foreach ($Root in$ProtectedRoots) {
        if ($Path.StartsWith($Root, [StringComparison]::OrdinalIgnoreCase)) { return$true }
    }
    
    $FileName = Split-Path $Path -Leaf$ProtectedFiles = @("NTUSER.DAT", "ntuser.ini", "desktop.ini")
    if ($ProtectedFiles -contains $FileName) { return$true }

    return $false
}

function Invoke-CleanupItem {
    param([string]$ItemPath, [string]$Strategy)
    
    if (Is-ProtectedPath $ItemPath) {
        if ($VerboseMode) { Write-Host "  [PROTEGIT] -> $ItemPath" -ForegroundColor Yellow }
        return $false
    }

    if ($DryRun) {
        if ($VerboseMode) { Write-Host "  [DRY-RUN] ($Strategy) ->$ItemPath" -ForegroundColor Gray }
        return $true
    }

    # Desbloquejar atributs de nomes lectura
    if (Test-Path $ItemPath) {
        Set-ItemProperty $ItemPath -Name IsReadOnly -Value$false -ErrorAction SilentlyContinue
    }

    switch ($Strategy) {
        "TRUNCATE" {
            if (Test-Path $ItemPath -PathType Leaf) { Clear-Content$ItemPath -Force }
            elseif (Test-Path $ItemPath -PathType Container) { Remove-Item$ItemPath -Recurse -Force }
        }
        "PURGE_CHILDREN" {
            if (Test-Path $ItemPath -PathType Container) {
                Get-ChildItem $ItemPath -Force | Remove-Item -Recurse -Force
            } else { Remove-Item $ItemPath -Force }
        }
        "SHRED_NIST" {
            if (Test-Path $ItemPath -PathType Leaf) {
                $Bytes = New-Object Byte[] 4096$Random = New-Object System.Random
                $Random.NextBytes($Bytes)
                [System.IO.File]::WriteAllBytes($ItemPath,$Bytes)
                Remove-Item $ItemPath -Force
            } else { Remove-Item $ItemPath -Recurse -Force }
        }
        "EMPTY_TRASH" {
            Clear-RecycleBin -Force -ErrorAction SilentlyContinue
        }
        Default {
            Remove-Item $ItemPath -Recurse -Force
        }
    }

    if ($VerboseMode) { Write-Host "  [NETEJAT] ($Strategy) ->$ItemPath" -ForegroundColor Green }
    return $true
}

# ==============================================================================
# BUCLE PRINCIPAL D'EXECUCIO
# ==============================================================================
$Objectives =$ObjectivesJson | ConvertFrom-Json
$TotalObjectives =$Objectives.Count

Write-Host "=============================================================================="
Write-Host " Netejator98 - Execucio dels Objectius de Neteja"
Write-Host "=============================================================================="
Write-Host " Directori desti: $TargetHome"
if ($DryRun) { Write-Host " Mode: SIMULACIO (Dry-run - Cap fitxer sera modificat)" -ForegroundColor Cyan }
else { Write-Host " Mode: REAL (Els elements seran netejats)" -ForegroundColor Red }
Write-Host "==============================================================================`n"

$TotalItemsCleaned = 0
$ProcessedObjectives = 0

foreach ($Obj in $Objectives) {
    $ProcessedObjectives++
    $OsStr = if ($Obj.os) { $Obj.os } else { "ALL" }
    Write-Host ("[{0,2}/{1}] [{2,-7}] {3} ({4})" -f $ProcessedObjectives, $TotalObjectives, $OsStr, $Obj.name, $Obj.strategy)

    $ObjItemsCount = 0

    foreach ($Pattern in $Obj.patterns) {
        $FullPathPattern = if ($Pattern -match "^[A-Za-z]:") { $Pattern } else { Join-Path $TargetHome $Pattern }
        
        # Resolvem el wildcard
        $Matches = Get-ChildItem -Path (Split-Path $FullPathPattern) -Filter (Split-Path $FullPathPattern -Leaf) -Force -ErrorAction SilentlyContinue

        foreach ($Match in $Matches) {
            $MatchPath = $Match.FullName
            
            # Seguretat per al patro "*" al directori arrel (no esborrar carpetes arrel)
            if ($Pattern -eq "*" -and (Test-Path $MatchPath -PathType Container)) { continue }

            if (Invoke-CleanupItem -ItemPath $MatchPath -Strategy $Obj.strategy) {
                $ObjItemsCount++
                $TotalItemsCleaned++
            }
        }
    }
    if ($ObjItemsCount -gt 0) { Write-Host "     -> $ObjItemsCount element(s) processat(s)." -ForegroundColor DarkGray }
}

Write-Host "`n=============================================================================="
Write-Host " Resum de la neteja:"
Write-Host "   - Objectius executats : $ProcessedObjectives de$TotalObjectives"
Write-Host "   - Elements processats : $TotalItemsCleaned"
Write-Host "=============================================================================="
