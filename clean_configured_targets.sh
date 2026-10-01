#!/usr/bin/env bash
# ==============================================================================
# Netejator98 — Execució d'Objectius de Neteja Configurats
# ==============================================================================
# Aquest script executa TOTS els objectius de neteja configurats al JSON inferior,
# sense tenir en compte si estan inactius ("enabled": false) o si pertanyen a
# qualsevol altre sistema operatiu ("os": "Linux", "Windows", "macOS").
#
# Ús:
#   ./clean_configured_targets.sh [OPCIONS]
#
# Opcions:
#   -n, --dry-run        Mode simulació: no esborra cap fitxer, només mostra el que faria.
#   -u, --home <DIR>     Directori arrel d'usuari a netejar (per defecte: $HOME).
#   -v, --verbose        Mostra els fitxers i carpetes individuals que es netegen.
#   -h, --help           Mostra aquesta ajuda.
# ==============================================================================

set -o pipefail

# ==============================================================================
# OBJECTIUS DE NETEJA CONFIGURATS (JSON)
# ==============================================================================
# Podeu afegir, editar o eliminar objectius i patrons directament en aquest JSON:
# ==============================================================================
read -r -d '' OBJECTIVES_JSON << 'EOF' || true
[
  {
    "name": "UserDocuments",
    "os": "Linux",
    "category": "USER_DOCUMENTS",
    "description": "Student user document folders (Linux)",
    "enabled": false,
    "strategy": "PURGE_CHILDREN",
    "patterns": [
      "Desktop/*",
      "Escriptori/*",
      "Escritorio/*",
      "Documents/*",
      "Documentos/*",
      "Baixades/*",
      "Descàrregues/*",
      "Descargas/*",
      "Downloads/*",
      "Pictures/*",
      "Imatges/*",
      "Imágenes/*",
      "Videos/*",
      "Vídeos/*",
      "Music/*",
      "Música/*",
      "Templates/*",
      "Plantilles/*",
      "Plantillas/*",
      "Public/*",
      "Públic/*",
      "Público/*"
    ]
  },
  {
    "name": "DesktopShortcuts",
    "os": "Linux",
    "category": "DESKTOP_SHORTCUTS",
    "description": "User desktop application shortcuts (Linux)",
    "enabled": false,
    "strategy": "STANDARD",
    "patterns": [
      "Desktop/*.desktop",
      "Escriptori/*.desktop",
      "Escritorio/*.desktop"
    ]
  },
  {
    "name": "Trash",
    "os": "Linux",
    "category": "RECYCLE_BIN",
    "description": "FreeDesktop Trash items (Linux)",
    "enabled": false,
    "strategy": "EMPTY_TRASH",
    "patterns": [
      ".local/share/Trash/*"
    ]
  },
  {
    "name": "CachesAndTemp",
    "os": "Linux",
    "category": "TEMP_AND_CACHE",
    "description": "User cache, thumbnail and temp directories (Linux)",
    "enabled": false,
    "strategy": "PURGE_CHILDREN",
    "patterns": [
      ".cache/*",
      ".thumbnails/*",
      "/tmp/student-*"
    ]
  },
  {
    "name": "BrowserProfiles",
    "os": "Linux",
    "category": "BROWSER_PROFILES",
    "description": "Web browser caches, cookies, history, and saved credentials (Linux)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      ".config/google-chrome/*",
      ".config/chromium/*",
      ".config/microsoft-edge/*",
      ".mozilla/firefox/*",
      ".config/BraveSoftware/Brave-Browser/*",
      ".config/opera/*",
      "snap/chromium/current/*",
      "snap/firefox/common/.mozilla/firefox/*",
      "snap/brave/current/*",
      "snap/opera/current/*",
      ".var/app/com.google.Chrome/*",
      ".var/app/org.chromium.Chromium/*",
      ".var/app/org.mozilla.firefox/*",
      ".var/app/com.brave.Browser/*"
    ]
  },
  {
    "name": "BrowserGoogleChrome",
    "os": "Linux",
    "category": "BROWSER_PROFILES",
    "description": "Google Chrome - Historial, preferits, memòria cau, galetes i sessions (Linux)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      ".config/google-chrome/Default/Bookmarks*",
      ".config/google-chrome/Default/History*",
      ".config/google-chrome/Default/Favicons*",
      ".config/google-chrome/Default/Top Sites*",
      ".config/google-chrome/Default/Visited Links",
      ".config/google-chrome/Default/Shortcuts*",
      ".config/google-chrome/Default/Cookies*",
      ".config/google-chrome/Default/Network/Cookies*",
      ".config/google-chrome/Default/Login Data*",
      ".config/google-chrome/Default/Web Data*",
      ".config/google-chrome/Default/Sessions/*",
      ".config/google-chrome/Default/Current Session*",
      ".config/google-chrome/Default/Current Tabs*",
      ".config/google-chrome/Default/Last Session*",
      ".config/google-chrome/Default/Last Tabs*",
      ".config/google-chrome/Default/Cache/*",
      ".config/google-chrome/Default/Code Cache/*",
      ".config/google-chrome/Default/GPUCache/*",
      ".config/google-chrome/Default/Local Storage/*",
      ".config/google-chrome/Default/IndexedDB/*",
      ".config/google-chrome/Profile */*",
      ".config/google-chrome/ShaderCache/*",
      ".config/google-chrome/GrShaderCache/*",
      ".cache/google-chrome/*",
      ".var/app/com.google.Chrome/config/google-chrome/Default/*",
      ".var/app/com.google.Chrome/cache/google-chrome/*"
    ]
  },
  {
    "name": "BrowserMozillaFirefox",
    "os": "Linux",
    "category": "BROWSER_PROFILES",
    "description": "Mozilla Firefox - Historial, marcadors (places), memòria cau, galetes i sessions (Linux)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      ".mozilla/firefox/*.default*/places.sqlite*",
      ".mozilla/firefox/*.default*/favicons.sqlite*",
      ".mozilla/firefox/*.default*/bookmarkbackups/*",
      ".mozilla/firefox/*.default*/cookies.sqlite*",
      ".mozilla/firefox/*.default*/logins.json",
      ".mozilla/firefox/*.default*/key4.db",
      ".mozilla/firefox/*.default*/formhistory.sqlite*",
      ".mozilla/firefox/*.default*/sessionstore*",
      ".mozilla/firefox/*.default*/storage/*",
      ".mozilla/firefox/*.default*/cache2/*",
      ".cache/mozilla/firefox/*",
      "snap/firefox/common/.mozilla/firefox/*.default*/*",
      "snap/firefox/common/.cache/mozilla/firefox/*",
      ".var/app/org.mozilla.firefox/.mozilla/firefox/*.default*/*",
      ".var/app/org.mozilla.firefox/cache/mozilla/firefox/*"
    ]
  },
  {
    "name": "BrowserMicrosoftEdge",
    "os": "Linux",
    "category": "BROWSER_PROFILES",
    "description": "Microsoft Edge - Historial, preferits, memòria cau, galetes i credencials (Linux)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      ".config/microsoft-edge/Default/Bookmarks*",
      ".config/microsoft-edge/Default/History*",
      ".config/microsoft-edge/Default/Favicons*",
      ".config/microsoft-edge/Default/Top Sites*",
      ".config/microsoft-edge/Default/Visited Links",
      ".config/microsoft-edge/Default/Shortcuts*",
      ".config/microsoft-edge/Default/Cookies*",
      ".config/microsoft-edge/Default/Network/Cookies*",
      ".config/microsoft-edge/Default/Login Data*",
      ".config/microsoft-edge/Default/Web Data*",
      ".config/microsoft-edge/Default/Sessions/*",
      ".config/microsoft-edge/Default/Cache/*",
      ".config/microsoft-edge/Default/Code Cache/*",
      ".config/microsoft-edge/Default/GPUCache/*",
      ".config/microsoft-edge/Default/Local Storage/*",
      ".config/microsoft-edge/Default/IndexedDB/*",
      ".config/microsoft-edge/Profile */*",
      ".cache/microsoft-edge/*",
      ".var/app/com.microsoft.Edge/config/microsoft-edge/Default/*"
    ]
  },
  {
    "name": "BrowserBrave",
    "os": "Linux",
    "category": "BROWSER_PROFILES",
    "description": "Brave Browser - Historial, preferits, memòria cau, galetes i sessions (Linux)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      ".config/BraveSoftware/Brave-Browser/Default/Bookmarks*",
      ".config/BraveSoftware/Brave-Browser/Default/History*",
      ".config/BraveSoftware/Brave-Browser/Default/Favicons*",
      ".config/BraveSoftware/Brave-Browser/Default/Top Sites*",
      ".config/BraveSoftware/Brave-Browser/Default/Cookies*",
      ".config/BraveSoftware/Brave-Browser/Default/Network/Cookies*",
      ".config/BraveSoftware/Brave-Browser/Default/Login Data*",
      ".config/BraveSoftware/Brave-Browser/Default/Web Data*",
      ".config/BraveSoftware/Brave-Browser/Default/Sessions/*",
      ".config/BraveSoftware/Brave-Browser/Default/Cache/*",
      ".config/BraveSoftware/Brave-Browser/Default/Code Cache/*",
      ".config/BraveSoftware/Brave-Browser/Default/Local Storage/*",
      ".config/BraveSoftware/Brave-Browser/Default/IndexedDB/*",
      ".config/BraveSoftware/Brave-Browser/Profile */*",
      ".cache/BraveSoftware/Brave-Browser/*",
      "snap/brave/current/.config/BraveSoftware/Brave-Browser/Default/*",
      ".var/app/com.brave.Browser/config/BraveSoftware/Brave-Browser/Default/*"
    ]
  },
  {
    "name": "BrowserOpera",
    "os": "Linux",
    "category": "BROWSER_PROFILES",
    "description": "Opera - Historial, preferits, memòria cau, galetes i sessions (Linux)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      ".config/opera/Bookmarks*",
      ".config/opera/History*",
      ".config/opera/Favicons*",
      ".config/opera/Top Sites*",
      ".config/opera/Cookies*",
      ".config/opera/Network/Cookies*",
      ".config/opera/Login Data*",
      ".config/opera/Web Data*",
      ".config/opera/Sessions/*",
      ".config/opera/Local Storage/*",
      ".config/opera/IndexedDB/*",
      ".cache/opera/*",
      "snap/opera/current/.config/opera/*"
    ]
  },
  {
    "name": "BrowserChromium",
    "os": "Linux",
    "category": "BROWSER_PROFILES",
    "description": "Chromium - Historial, marcadors, memòria cau i perfils d'usuari (Linux)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      ".config/chromium/Default/Bookmarks*",
      ".config/chromium/Default/History*",
      ".config/chromium/Default/Favicons*",
      ".config/chromium/Default/Top Sites*",
      ".config/chromium/Default/Visited Links",
      ".config/chromium/Default/Cookies*",
      ".config/chromium/Default/Network/Cookies*",
      ".config/chromium/Default/Login Data*",
      ".config/chromium/Default/Web Data*",
      ".config/chromium/Default/Sessions/*",
      ".config/chromium/Default/Cache/*",
      ".config/chromium/Default/Code Cache/*",
      ".config/chromium/Default/Local Storage/*",
      ".config/chromium/Default/IndexedDB/*",
      ".config/chromium/Profile */*",
      ".cache/chromium/*",
      "snap/chromium/current/.config/chromium/Default/*",
      ".var/app/org.chromium.Chromium/config/chromium/Default/*"
    ]
  },
  {
    "name": "RecentFiles",
    "os": "Linux",
    "category": "RECENT_FILES",
    "description": "GTK and LibreOffice recently used files (Linux)",
    "enabled": false,
    "strategy": "TRUNCATE",
    "patterns": [
      ".local/share/recently-used.xbel",
      ".config/libreoffice/*/user/registrymodifications.xcu"
    ]
  },
  {
    "name": "UserCredentials",
    "os": "Linux",
    "category": "CREDENTIALS",
    "description": "SSH keys, AWS credentials, and GitHub CLI tokens (Linux)",
    "enabled": false,
    "strategy": "SHRED_NIST",
    "patterns": [
      ".ssh/*",
      ".aws/*",
      ".config/gh/*",
      ".git-credentials",
      ".config/git/credentials"
    ]
  },
  {
    "name": "CloudSync",
    "os": "Linux",
    "category": "CLOUD_SYNC",
    "description": "Local cloud sync storage folders (Linux)",
    "enabled": false,
    "strategy": "CLOUD_WIPE",
    "patterns": [
      "Nextcloud/*",
      "ownCloud/*",
      "Dropbox/*"
    ]
  },
  {
    "name": "ShellHistory",
    "os": "Linux",
    "category": "SHELL_HISTORY",
    "description": "Bash, Zsh, and Python interactive history logs (Linux)",
    "enabled": false,
    "strategy": "TRUNCATE",
    "patterns": [
      ".bash_history",
      ".zsh_history",
      ".python_history"
    ]
  },
  {
    "name": "GoldenProfileSync",
    "os": "Linux",
    "category": "GOLDEN_PROFILE",
    "description": "Desktop environment overrides reset to golden skel (Linux)",
    "enabled": false,
    "strategy": "GOLDEN_RESET",
    "patterns": [
      ".config/mimeapps.list",
      ".config/user-dirs.dirs"
    ]
  },
  {
    "name": "CustomWorkspace",
    "os": "Linux",
    "category": "CUSTOM",
    "description": "Student custom workspace and project build directories (Linux)",
    "enabled": false,
    "strategy": "CUSTOM_CLEAN",
    "patterns": [
      "Projects/*",
      "Workspace/*"
    ]
  },
  {
    "name": "UserDocuments",
    "os": "Windows",
    "category": "USER_DOCUMENTS",
    "description": "Student document libraries (Windows)",
    "enabled": false,
    "strategy": "PURGE_CHILDREN",
    "patterns": [
      "Desktop/*",
      "Documents/*",
      "Downloads/*",
      "Pictures/*",
      "Videos/*",
      "Music/*"
    ]
  },
  {
    "name": "DesktopShortcuts",
    "os": "Windows",
    "category": "DESKTOP_SHORTCUTS",
    "description": "User desktop shortcut links and URLs (Windows)",
    "enabled": false,
    "strategy": "STANDARD",
    "patterns": [
      "Desktop/*.lnk",
      "Desktop/*.url"
    ]
  },
  {
    "name": "RecycleBin",
    "os": "Windows",
    "category": "RECYCLE_BIN",
    "description": "Windows Recycle Bin items (Windows)",
    "enabled": false,
    "strategy": "EMPTY_TRASH",
    "patterns": [
      "C:/$Recycle.Bin/*"
    ]
  },
  {
    "name": "CachesAndTemp",
    "os": "Windows",
    "category": "TEMP_AND_CACHE",
    "description": "Temporary files, thumbnail caches, and crash dumps (Windows)",
    "enabled": false,
    "strategy": "PURGE_CHILDREN",
    "patterns": [
      "AppData/Local/Temp/*",
      "AppData/Local/CrashDumps/*",
      "AppData/Local/Microsoft/Windows/Explorer/thumbcache_*.db"
    ]
  },
  {
    "name": "BrowserProfiles",
    "os": "Windows",
    "category": "BROWSER_PROFILES",
    "description": "Chrome, Edge, Firefox, Brave, and Opera user profiles (Windows)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "AppData/Local/Google/Chrome/User Data/*",
      "AppData/Local/Microsoft/Edge/User Data/*",
      "AppData/Roaming/Mozilla/Firefox/Profiles/*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/*"
    ]
  },
  {
    "name": "BrowserGoogleChrome",
    "os": "Windows",
    "category": "BROWSER_PROFILES",
    "description": "Google Chrome - Historial, preferits, memòria cau, galetes i sessions (Windows)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "AppData/Local/Google/Chrome/User Data/Default/Bookmarks*",
      "AppData/Local/Google/Chrome/User Data/Default/History*",
      "AppData/Local/Google/Chrome/User Data/Default/Favicons*",
      "AppData/Local/Google/Chrome/User Data/Default/Top Sites*",
      "AppData/Local/Google/Chrome/User Data/Default/Visited Links",
      "AppData/Local/Google/Chrome/User Data/Default/Shortcuts*",
      "AppData/Local/Google/Chrome/User Data/Default/Cookies*",
      "AppData/Local/Google/Chrome/User Data/Default/Network/Cookies*",
      "AppData/Local/Google/Chrome/User Data/Default/Login Data*",
      "AppData/Local/Google/Chrome/User Data/Default/Web Data*",
      "AppData/Local/Google/Chrome/User Data/Default/Sessions/*",
      "AppData/Local/Google/Chrome/User Data/Default/Current Session*",
      "AppData/Local/Google/Chrome/User Data/Default/Current Tabs*",
      "AppData/Local/Google/Chrome/User Data/Default/Last Session*",
      "AppData/Local/Google/Chrome/User Data/Default/Last Tabs*",
      "AppData/Local/Google/Chrome/User Data/Default/Cache/*",
      "AppData/Local/Google/Chrome/User Data/Default/Code Cache/*",
      "AppData/Local/Google/Chrome/User Data/Default/GPUCache/*",
      "AppData/Local/Google/Chrome/User Data/Default/Local Storage/*",
      "AppData/Local/Google/Chrome/User Data/Default/IndexedDB/*",
      "AppData/Local/Google/Chrome/User Data/Profile */*",
      "AppData/Local/Google/Chrome/User Data/ShaderCache/*"
    ]
  },
  {
    "name": "BrowserMozillaFirefox",
    "os": "Windows",
    "category": "BROWSER_PROFILES",
    "description": "Mozilla Firefox - Historial, marcadors (places), memòria cau, galetes i sessions (Windows)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/places.sqlite*",
      "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/favicons.sqlite*",
      "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/bookmarkbackups/*",
      "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/cookies.sqlite*",
      "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/logins.json",
      "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/key4.db",
      "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/formhistory.sqlite*",
      "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/sessionstore*",
      "AppData/Roaming/Mozilla/Firefox/Profiles/*.default*/storage/*",
      "AppData/Local/Mozilla/Firefox/Profiles/*.default*/cache2/*",
      "AppData/Local/Mozilla/Firefox/Profiles/*.default*/jumpListCache/*",
      "AppData/Local/Mozilla/Firefox/Profiles/*.default*/startupCache/*"
    ]
  },
  {
    "name": "BrowserMicrosoftEdge",
    "os": "Windows",
    "category": "BROWSER_PROFILES",
    "description": "Microsoft Edge - Historial, preferits, memòria cau, galetes i credencials (Windows)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "AppData/Local/Microsoft/Edge/User Data/Default/Bookmarks*",
      "AppData/Local/Microsoft/Edge/User Data/Default/History*",
      "AppData/Local/Microsoft/Edge/User Data/Default/Favicons*",
      "AppData/Local/Microsoft/Edge/User Data/Default/Top Sites*",
      "AppData/Local/Microsoft/Edge/User Data/Default/Visited Links",
      "AppData/Local/Microsoft/Edge/User Data/Default/Shortcuts*",
      "AppData/Local/Microsoft/Edge/User Data/Default/Cookies*",
      "AppData/Local/Microsoft/Edge/User Data/Default/Network/Cookies*",
      "AppData/Local/Microsoft/Edge/User Data/Default/Login Data*",
      "AppData/Local/Microsoft/Edge/User Data/Default/Web Data*",
      "AppData/Local/Microsoft/Edge/User Data/Default/Sessions/*",
      "AppData/Local/Microsoft/Edge/User Data/Default/Cache/*",
      "AppData/Local/Microsoft/Edge/User Data/Default/Code Cache/*",
      "AppData/Local/Microsoft/Edge/User Data/Default/GPUCache/*",
      "AppData/Local/Microsoft/Edge/User Data/Default/Local Storage/*",
      "AppData/Local/Microsoft/Edge/User Data/Default/IndexedDB/*",
      "AppData/Local/Microsoft/Edge/User Data/Profile */*"
    ]
  },
  {
    "name": "BrowserBrave",
    "os": "Windows",
    "category": "BROWSER_PROFILES",
    "description": "Brave Browser - Historial, preferits, memòria cau, galetes i sessions (Windows)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Bookmarks*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/History*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Favicons*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Top Sites*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Cookies*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Network/Cookies*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Login Data*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Web Data*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Sessions/*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Cache/*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Code Cache/*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Local Storage/*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/IndexedDB/*",
      "AppData/Local/BraveSoftware/Brave-Browser/User Data/Profile */*"
    ]
  },
  {
    "name": "BrowserOpera",
    "os": "Windows",
    "category": "BROWSER_PROFILES",
    "description": "Opera - Historial, preferits, memòria cau, galetes i sessions (Windows)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "AppData/Roaming/Opera Software/Opera Stable/Bookmarks*",
      "AppData/Roaming/Opera Software/Opera Stable/History*",
      "AppData/Roaming/Opera Software/Opera Stable/Favicons*",
      "AppData/Roaming/Opera Software/Opera Stable/Top Sites*",
      "AppData/Roaming/Opera Software/Opera Stable/Cookies*",
      "AppData/Roaming/Opera Software/Opera Stable/Network/Cookies*",
      "AppData/Roaming/Opera Software/Opera Stable/Login Data*",
      "AppData/Roaming/Opera Software/Opera Stable/Web Data*",
      "AppData/Roaming/Opera Software/Opera Stable/Sessions/*",
      "AppData/Roaming/Opera Software/Opera Stable/Local Storage/*",
      "AppData/Roaming/Opera Software/Opera Stable/IndexedDB/*",
      "AppData/Local/Opera Software/Opera Stable/Cache/*"
    ]
  },
  {
    "name": "BrowserChromium",
    "os": "Windows",
    "category": "BROWSER_PROFILES",
    "description": "Chromium - Historial, marcadors, memòria cau i perfils d'usuari (Windows)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "AppData/Local/Chromium/User Data/Default/Bookmarks*",
      "AppData/Local/Chromium/User Data/Default/History*",
      "AppData/Local/Chromium/User Data/Default/Favicons*",
      "AppData/Local/Chromium/User Data/Default/Cookies*",
      "AppData/Local/Chromium/User Data/Default/Network/Cookies*",
      "AppData/Local/Chromium/User Data/Default/Login Data*",
      "AppData/Local/Chromium/User Data/Default/Web Data*",
      "AppData/Local/Chromium/User Data/Default/Sessions/*",
      "AppData/Local/Chromium/User Data/Default/Cache/*",
      "AppData/Local/Chromium/User Data/Default/Code Cache/*",
      "AppData/Local/Chromium/User Data/Default/Local Storage/*",
      "AppData/Local/Chromium/User Data/Default/IndexedDB/*",
      "AppData/Local/Chromium/User Data/Profile */*"
    ]
  },
  {
    "name": "RecentFiles",
    "os": "Windows",
    "category": "RECENT_FILES",
    "description": "Windows Recent files and Quick Access MRU lists (Windows)",
    "enabled": false,
    "strategy": "TRUNCATE",
    "patterns": [
      "AppData/Roaming/Microsoft/Windows/Recent/*",
      "AppData/Roaming/Microsoft/Office/Recent/*"
    ]
  },
  {
    "name": "UserCredentials",
    "os": "Windows",
    "category": "CREDENTIALS",
    "description": "SSH keys, AWS credentials, and Git credential caches (Windows)",
    "enabled": false,
    "strategy": "SHRED_NIST",
    "patterns": [
      ".ssh/*",
      ".aws/*",
      "AppData/Roaming/GitHub CLI/*",
      "_netrc"
    ]
  },
  {
    "name": "CloudSync",
    "os": "Windows",
    "category": "CLOUD_SYNC",
    "description": "Local OneDrive, Dropbox, and Google Drive caches (Windows)",
    "enabled": false,
    "strategy": "CLOUD_WIPE",
    "patterns": [
      "OneDrive/*",
      "Dropbox/*",
      "AppData/Local/Google/DriveFS/*"
    ]
  },
  {
    "name": "ShellHistory",
    "os": "Windows",
    "category": "SHELL_HISTORY",
    "description": "PowerShell PSReadLine console host command history (Windows)",
    "enabled": false,
    "strategy": "TRUNCATE",
    "patterns": [
      "AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt"
    ]
  },
  {
    "name": "GoldenProfileSync",
    "os": "Windows",
    "category": "GOLDEN_PROFILE",
    "description": "User startup shortcuts reset to default profile (Windows)",
    "enabled": false,
    "strategy": "GOLDEN_RESET",
    "patterns": [
      "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/*"
    ]
  },
  {
    "name": "CustomWorkspace",
    "os": "Windows",
    "category": "CUSTOM",
    "description": "Student custom workspaces and development directories (Windows)",
    "enabled": false,
    "strategy": "CUSTOM_CLEAN",
    "patterns": [
      "Workspace/*",
      "Projects/*"
    ]
  },
  {
    "name": "UserDocuments",
    "os": "macOS",
    "category": "USER_DOCUMENTS",
    "description": "Student user documents and downloads (macOS)",
    "enabled": false,
    "strategy": "PURGE_CHILDREN",
    "patterns": [
      "Desktop/*",
      "Documents/*",
      "Downloads/*",
      "Pictures/*",
      "Movies/*",
      "Music/*"
    ]
  },
  {
    "name": "DesktopShortcuts",
    "os": "macOS",
    "category": "DESKTOP_SHORTCUTS",
    "description": "User desktop webloc links and alias files (macOS)",
    "enabled": false,
    "strategy": "STANDARD",
    "patterns": [
      "Desktop/*.webloc",
      "Desktop/*.alias"
    ]
  },
  {
    "name": "TrashBin",
    "os": "macOS",
    "category": "RECYCLE_BIN",
    "description": "macOS Trash folder (macOS)",
    "enabled": false,
    "strategy": "EMPTY_TRASH",
    "patterns": [
      ".Trash/*"
    ]
  },
  {
    "name": "CachesAndTemp",
    "os": "macOS",
    "category": "TEMP_AND_CACHE",
    "description": "User library caches, logs, and QuickLook thumbnails (macOS)",
    "enabled": false,
    "strategy": "PURGE_CHILDREN",
    "patterns": [
      "Library/Caches/*",
      "Library/Logs/*"
    ]
  },
  {
    "name": "BrowserProfiles",
    "os": "macOS",
    "category": "BROWSER_PROFILES",
    "description": "Safari, Chrome, and Firefox user data (macOS)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "Library/Application Support/Google/Chrome/*",
      "Library/Application Support/Firefox/Profiles/*",
      "Library/Safari/LocalStorage/*"
    ]
  },
  {
    "name": "BrowserGoogleChrome",
    "os": "macOS",
    "category": "BROWSER_PROFILES",
    "description": "Google Chrome - Historial, preferits, memòria cau, galetes i sessions (macOS)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "Library/Application Support/Google/Chrome/Default/Bookmarks*",
      "Library/Application Support/Google/Chrome/Default/History*",
      "Library/Application Support/Google/Chrome/Default/Favicons*",
      "Library/Application Support/Google/Chrome/Default/Top Sites*",
      "Library/Application Support/Google/Chrome/Default/Visited Links",
      "Library/Application Support/Google/Chrome/Default/Shortcuts*",
      "Library/Application Support/Google/Chrome/Default/Cookies*",
      "Library/Application Support/Google/Chrome/Default/Network/Cookies*",
      "Library/Application Support/Google/Chrome/Default/Login Data*",
      "Library/Application Support/Google/Chrome/Default/Web Data*",
      "Library/Application Support/Google/Chrome/Default/Sessions/*",
      "Library/Application Support/Google/Chrome/Default/Current Session*",
      "Library/Application Support/Google/Chrome/Default/Current Tabs*",
      "Library/Application Support/Google/Chrome/Default/Last Session*",
      "Library/Application Support/Google/Chrome/Default/Last Tabs*",
      "Library/Application Support/Google/Chrome/Default/Local Storage/*",
      "Library/Application Support/Google/Chrome/Default/IndexedDB/*",
      "Library/Application Support/Google/Chrome/Profile */*",
      "Library/Caches/Google/Chrome/*",
      "Library/Caches/com.google.Chrome/*"
    ]
  },
  {
    "name": "BrowserMozillaFirefox",
    "os": "macOS",
    "category": "BROWSER_PROFILES",
    "description": "Mozilla Firefox - Historial, marcadors (places), memòria cau, galetes i sessions (macOS)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "Library/Application Support/Firefox/Profiles/*.default*/places.sqlite*",
      "Library/Application Support/Firefox/Profiles/*.default*/favicons.sqlite*",
      "Library/Application Support/Firefox/Profiles/*.default*/bookmarkbackups/*",
      "Library/Application Support/Firefox/Profiles/*.default*/cookies.sqlite*",
      "Library/Application Support/Firefox/Profiles/*.default*/logins.json",
      "Library/Application Support/Firefox/Profiles/*.default*/key4.db",
      "Library/Application Support/Firefox/Profiles/*.default*/formhistory.sqlite*",
      "Library/Application Support/Firefox/Profiles/*.default*/sessionstore*",
      "Library/Application Support/Firefox/Profiles/*.default*/storage/*",
      "Library/Caches/Firefox/Profiles/*.default*/cache2/*",
      "Library/Caches/org.mozilla.firefox/*"
    ]
  },
  {
    "name": "BrowserMicrosoftEdge",
    "os": "macOS",
    "category": "BROWSER_PROFILES",
    "description": "Microsoft Edge - Historial, preferits, memòria cau, galetes i credencials (macOS)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "Library/Application Support/Microsoft Edge/Default/Bookmarks*",
      "Library/Application Support/Microsoft Edge/Default/History*",
      "Library/Application Support/Microsoft Edge/Default/Favicons*",
      "Library/Application Support/Microsoft Edge/Default/Top Sites*",
      "Library/Application Support/Microsoft Edge/Default/Visited Links",
      "Library/Application Support/Microsoft Edge/Default/Cookies*",
      "Library/Application Support/Microsoft Edge/Default/Network/Cookies*",
      "Library/Application Support/Microsoft Edge/Default/Login Data*",
      "Library/Application Support/Microsoft Edge/Default/Web Data*",
      "Library/Application Support/Microsoft Edge/Default/Sessions/*",
      "Library/Application Support/Microsoft Edge/Default/Local Storage/*",
      "Library/Application Support/Microsoft Edge/Default/IndexedDB/*",
      "Library/Application Support/Microsoft Edge/Profile */*",
      "Library/Caches/Microsoft Edge/*",
      "Library/Caches/com.microsoft.edgemac/*"
    ]
  },
  {
    "name": "BrowserBrave",
    "os": "macOS",
    "category": "BROWSER_PROFILES",
    "description": "Brave Browser - Historial, preferits, memòria cau, galetes i sessions (macOS)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "Library/Application Support/BraveSoftware/Brave-Browser/Default/Bookmarks*",
      "Library/Application Support/BraveSoftware/Brave-Browser/Default/History*",
      "Library/Application Support/BraveSoftware/Brave-Browser/Default/Favicons*",
      "Library/Application Support/BraveSoftware/Brave-Browser/Default/Top Sites*",
      "Library/Application Support/BraveSoftware/Brave-Browser/Default/Cookies*",
      "Library/Application Support/BraveSoftware/Brave-Browser/Default/Network/Cookies*",
      "Library/Application Support/BraveSoftware/Brave-Browser/Default/Login Data*",
      "Library/Application Support/BraveSoftware/Brave-Browser/Default/Web Data*",
      "Library/Application Support/BraveSoftware/Brave-Browser/Default/Sessions/*",
      "Library/Application Support/BraveSoftware/Brave-Browser/Default/Local Storage/*",
      "Library/Application Support/BraveSoftware/Brave-Browser/Default/IndexedDB/*",
      "Library/Application Support/BraveSoftware/Brave-Browser/Profile */*",
      "Library/Caches/BraveSoftware/Brave-Browser/*"
    ]
  },
  {
    "name": "BrowserOpera",
    "os": "macOS",
    "category": "BROWSER_PROFILES",
    "description": "Opera - Historial, preferits, memòria cau, galetes i sessions (macOS)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "Library/Application Support/com.operasoftware.Opera/Bookmarks*",
      "Library/Application Support/com.operasoftware.Opera/History*",
      "Library/Application Support/com.operasoftware.Opera/Favicons*",
      "Library/Application Support/com.operasoftware.Opera/Top Sites*",
      "Library/Application Support/com.operasoftware.Opera/Cookies*",
      "Library/Application Support/com.operasoftware.Opera/Network/Cookies*",
      "Library/Application Support/com.operasoftware.Opera/Login Data*",
      "Library/Application Support/com.operasoftware.Opera/Web Data*",
      "Library/Application Support/com.operasoftware.Opera/Sessions/*",
      "Library/Application Support/com.operasoftware.Opera/Local Storage/*",
      "Library/Application Support/com.operasoftware.Opera/IndexedDB/*",
      "Library/Caches/com.operasoftware.Opera/*"
    ]
  },
  {
    "name": "BrowserSafari",
    "os": "macOS",
    "category": "BROWSER_PROFILES",
    "description": "Apple Safari - Historial, preferits, memòria cau, galetes i magatzem local (macOS)",
    "enabled": false,
    "strategy": "BROWSER_CLEAN",
    "patterns": [
      "Library/Safari/Bookmarks.plist",
      "Library/Safari/History.db*",
      "Library/Safari/TopSites.plist",
      "Library/Safari/Downloads.plist",
      "Library/Safari/LastSession.plist",
      "Library/Safari/Favicon Cache/*",
      "Library/Safari/Touch Icon Cache/*",
      "Library/Safari/LocalStorage/*",
      "Library/Safari/Databases/*",
      "Library/Safari/WebStorage/*",
      "Library/Cookies/Cookies.binarycookies",
      "Library/Caches/com.apple.Safari/*",
      "Library/Containers/com.apple.Safari/Data/Library/Caches/*"
    ]
  },
  {
    "name": "RecentFiles",
    "os": "macOS",
    "category": "RECENT_FILES",
    "description": "Finder and Application recent items lists (macOS)",
    "enabled": false,
    "strategy": "TRUNCATE",
    "patterns": [
      "Library/Application Support/com.apple.sharedfilelist/*"
    ]
  },
  {
    "name": "UserCredentials",
    "os": "macOS",
    "category": "CREDENTIALS",
    "description": "SSH keys, AWS credentials, and GitHub CLI tokens (macOS)",
    "enabled": false,
    "strategy": "SHRED_NIST",
    "patterns": [
      ".ssh/*",
      ".aws/*",
      ".config/gh/*",
      ".git-credentials"
    ]
  },
  {
    "name": "CloudSync",
    "os": "macOS",
    "category": "CLOUD_SYNC",
    "description": "Local iCloud, Dropbox, and Google Drive storage (macOS)",
    "enabled": false,
    "strategy": "CLOUD_WIPE",
    "patterns": [
      "Library/CloudStorage/*",
      "Dropbox/*"
    ]
  },
  {
    "name": "ShellHistory",
    "os": "macOS",
    "category": "SHELL_HISTORY",
    "description": "Zsh and Bash command histories (macOS)",
    "enabled": false,
    "strategy": "TRUNCATE",
    "patterns": [
      ".zsh_history",
      ".bash_history"
    ]
  },
  {
    "name": "GoldenProfileSync",
    "os": "macOS",
    "category": "GOLDEN_PROFILE",
    "description": "Dock and user preferences reset to template (macOS)",
    "enabled": false,
    "strategy": "GOLDEN_RESET",
    "patterns": [
      "Library/Preferences/com.apple.dock.plist"
    ]
  },
  {
    "name": "CustomWorkspace",
    "os": "macOS",
    "category": "CUSTOM",
    "description": "Student custom code workspaces and build folders (macOS)",
    "enabled": false,
    "strategy": "CUSTOM_CLEAN",
    "patterns": [
      "Workspace/*",
      "Projects/*"
    ]
  }
]
EOF

# ==============================================================================
# VALORS PER DEFECTE I GESTIÓ D'ARGUMENTS
# ==============================================================================
TARGET_HOME="${HOME}"
DRY_RUN=false
VERBOSE=false

show_help() {
    cat << 'HELP'
Netejator98 — Execució dels Objectius de Neteja Configurats

Ús:
  ./clean_configured_targets.sh [OPCIONS]

Opcions:
  -n, --dry-run        Mode simulació: inspecciona i mostra què s'esborraria sense tocar res.
  -u, --home <DIR>     Especifica el directori d'usuari a netejar (per defecte: $HOME).
  -v, --verbose        Mostra cada fitxer i directori afectat detalladament.
  -h, --help           Mostra aquesta ajuda i surt.

HELP
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -u|--home)
            if [[ -n "$2" ]]; then
                TARGET_HOME="$2"
                shift 2
            else
                echo "Error: L'opció $1 requereix un directori." >&2
                exit 1
            fi
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Opció desconeguda: $1" >&2
            show_help
            exit 1
            ;;
    esac
done

# Assegurar que TARGET_HOME existeix
if [[ ! -d "$TARGET_HOME" ]]; then
    echo "Error: El directori d'usuari especificat no existeix: $TARGET_HOME" >&2
    exit 1
fi

# Normalitzar ruta TARGET_HOME
TARGET_HOME="$(cd "$TARGET_HOME" && pwd -P)"

# ==============================================================================
# COMPROVACIÓ D'EINES PER PROCESSAR JSON (jq o python3)
# ==============================================================================
get_targets_data() {
    if command -v jq >/dev/null 2>&1; then
        echo "$OBJECTIVES_JSON" | jq -r '.[] as $t | $t.patterns[]? as $p | "\($t.name)	\($t.os)	\($t.category)	\($t.strategy)	\($t.description // "")	\($p)"'
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c '
import sys, json
data = json.loads(sys.stdin.read())
for t in data:
    name = t.get("name", "")
    os_name = t.get("os", "ALL")
    cat = t.get("category", "")
    strat = t.get("strategy", "STANDARD")
    desc = t.get("description", "")
    for p in t.get("patterns", []):
        print(f"{name}	{os_name}	{cat}	{strat}	{desc}	{p}")
' <<< "$OBJECTIVES_JSON"
    else
        echo "Error: Cal tenir 'jq' o 'python3' instal·lat per interpretar el JSON d'objectius." >&2
        exit 1
    fi
}

count_total_objectives() {
    if command -v jq >/dev/null 2>&1; then
        echo "$OBJECTIVES_JSON" | jq 'length'
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c 'import sys, json; print(len(json.loads(sys.stdin.read())))' <<< "$OBJECTIVES_JSON"
    else
        echo "51"
    fi
}

# ==============================================================================
# SEGURETAT: RUTES PROTEGIDES (INVARIANTS DE SEGURETAT)
# ==============================================================================
is_protected_path() {
    local candidate="$1"
    # Normalitzar ruta candidata
    candidate="$(readlink -m "$candidate" 2>/dev/null || realpath "$candidate" 2>/dev/null || echo "$candidate")"
    candidate="${candidate%/}"

    # Si la ruta és buida, l'arrel o el propi directori HOME d'usuari, protegir sempre!
    if [[ -z "$candidate" || "$candidate" == "/" || "$candidate" == "$TARGET_HOME" ]]; then
        return 0
    fi

    # Si el candidat és un directori pare del HOME (p. ex. /home)
    if [[ "$TARGET_HOME" == "$candidate"/* ]]; then
        return 0
    fi

    # Llista de directoris protegits del sistema
    local protected_roots=(
        "/bin" "/sbin" "/usr" "/etc" "/lib" "/lib64" "/boot"
        "/dev" "/proc" "/sys" "/root" "/var/lib/netejator98"
        "/System" "/Library" "/Applications"
    )

    local p
    for p in "${protected_roots[@]}"; do
        p="${p%/}"
        # Si coincideix exactament, si el candidat està dins la carpeta protegida, o és pare
        if [[ "$candidate" == "$p" || "$candidate" == "$p"/* || "$p" == "$candidate"/* ]]; then
            return 0
        fi
    done

    return 1
}

# ==============================================================================
# EXECUCIÓ D'ACCIONS DE NETEJA PER FITXER / CARPETA
# ==============================================================================
execute_cleanup_item() {
    local path="$1"
    local strategy="$2"
    local is_child="${3:-false}"

    # Comprovació de seguretat
    if is_protected_path "$path"; then
        echo "  [PROTEGIT] S'ha impedit la supressió de la ruta crítica: $path" >&2
        return 1
    fi

    if [[ ! -e "$path" && ! -L "$path" ]]; then
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        if [[ "$VERBOSE" == "true" ]]; then
            echo "  [DRY-RUN] ($strategy) -> $path"
        fi
        return 0
    fi

    # Desbloquejar atributs de només lectura si fos necessari (recursivament per a directoris)
    if [[ -d "$path" && ! -L "$path" ]]; then
        chmod -R u+w "$path" 2>/dev/null || true
    else
        chmod u+w "$path" 2>/dev/null || true
    fi

    case "$strategy" in
        TRUNCATE)
            if [[ -f "$path" || -L "$path" ]]; then
                : > "$path" 2>/dev/null || truncate -s 0 "$path" 2>/dev/null || true
            elif [[ -d "$path" ]]; then
                rm -rf "$path" 2>/dev/null || true
            fi
            ;;
        PURGE_CHILDREN)
            if [[ "$is_child" == "true" ]]; then
                # Quan l'element és fill fruit d'una expansió de patró (p. ex. Documents/*),
                # la carpeta, subcarpeta o fitxer s'ha d'eliminar completament.
                rm -rf "$path" 2>/dev/null || true
            elif [[ -d "$path" && ! -L "$path" ]]; then
                # Quan és el directori arrel mateix (p. ex. Documents), se'n buida el contingut
                # conservant l'estructura de la carpeta pare.
                find "$path" -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true
            else
                rm -rf "$path" 2>/dev/null || true
            fi
            ;;
        SHRED_NIST)
            if [[ -f "$path" && ! -L "$path" ]]; then
                if command -v shred >/dev/null 2>&1; then
                    shred -u -z -n 3 "$path" 2>/dev/null || rm -f "$path" 2>/dev/null || true
                else
                    local size
                    size=$(wc -c < "$path" 2>/dev/null || echo 0)
                    if [[ "$size" -gt 0 ]]; then
                        dd if=/dev/zero of="$path" bs=4096 count=$(( (size + 4095) / 4096 )) conv=notrunc status=none 2>/dev/null || true
                    fi
                    rm -f "$path" 2>/dev/null || true
                fi
            else
                rm -rf "$path" 2>/dev/null || true
            fi
            ;;
        SECURE)
            if [[ -f "$path" && ! -L "$path" ]]; then
                if command -v shred >/dev/null 2>&1; then
                    shred -u -z -n 1 "$path" 2>/dev/null || rm -f "$path" 2>/dev/null || true
                else
                    rm -f "$path" 2>/dev/null || true
                fi
            else
                rm -rf "$path" 2>/dev/null || true
            fi
            ;;
        STANDARD|EMPTY_TRASH|BROWSER_CLEAN|CLOUD_WIPE|GOLDEN_RESET|CUSTOM_CLEAN|*)
            rm -rf "$path" 2>/dev/null || true
            ;;
    esac

    if [[ "$VERBOSE" == "true" ]]; then
        echo "  [NETEJAT] ($strategy) -> $path"
    fi

    return 0
}

# ==============================================================================
# BUCLE PRINCIPAL D'EXECUCIÓ
# ==============================================================================
TOTAL_OBJECTIVES=$(count_total_objectives)
echo "=============================================================================="
echo " Netejator98 — Execució dels Objectius de Neteja Configurats"
echo "=============================================================================="
echo " Directori destí d'usuari: $TARGET_HOME"
echo " Total objectius definits: $TOTAL_OBJECTIVES"
echo " Filtre de SO / inactius : DESACTIVAT (S'executen TOTS els objectius)"
if [[ "$DRY_RUN" == "true" ]]; then
    echo " Mode d'execució        : SIMULACIÓ (Dry-run — Cap fitxer serà modificat)"
else
    echo " Mode d'execució        : REAL (Els elements coincidents seran netejats)"
fi
echo "=============================================================================="
echo ""

TOTAL_ITEMS_CLEANED=0
PROCESSED_OBJECTIVES=0

# Utilitzem nullglob i dotglob per a una expansió exhaustiva de fitxers (inclosos ocults)
shopt -s nullglob dotglob

CURRENT_OBJ=""
OBJ_ITEMS_COUNT=0

while IFS=$'\t' read -r name target_os category strategy desc pattern; do
    [[ -z "$name" ]] && continue

    if [[ "$name::$target_os" != "$CURRENT_OBJ" ]]; then
        if [[ -n "$CURRENT_OBJ" ]]; then
            if [[ $OBJ_ITEMS_COUNT -gt 0 ]]; then
                echo "     -> $OBJ_ITEMS_COUNT element(s) trobat(s) i processat(s)."
            elif [[ "$VERBOSE" == "true" ]]; then
                echo "     -> Cap fitxer o directori coincident."
            fi
        fi
        CURRENT_OBJ="$name::$target_os"
        OBJ_ITEMS_COUNT=0
        ((PROCESSED_OBJECTIVES++))
        printf "[%2d/%d] [%-7s] %s (%s)\n" "$PROCESSED_OBJECTIVES" "$TOTAL_OBJECTIVES" "$target_os" "$name" "$strategy"
        if [[ -n "$desc" && "$VERBOSE" == "true" ]]; then
            echo "       Descripció: $desc"
        fi
    fi

    # Determinar si el patró és absolut o relatiu
    matches=()
    OLD_IFS="$IFS"
    IFS=
    if [[ "$pattern" =~ ^/ ]] || [[ "$pattern" =~ ^[a-zA-Z]: ]]; then
        # Patró absolut
        matches=( $pattern )
    else
        # Patró relatiu al directori d'usuari
        matches=( "$TARGET_HOME"/$pattern )
    fi
    IFS="$OLD_IFS"

    # Si el patró apunta a fills d'un directori (acaba en /* o /*.*) o
    # pertany a USER_DOCUMENTS amb comodí:
    # Les coincidències són elements fills continguts dins de la carpeta pare.
    # Per tant, cadascun d'aquests elements (incloent carpetes i subcarpetes)
    # s'ha d'eliminar completament preservant la carpeta contenidora mare.
    is_child=false
    if [[ "$pattern" == *"/*" || "$pattern" == *"/*."* || ( "$category" == "USER_DOCUMENTS" && "$pattern" == *"*"* ) ]]; then
        is_child=true
    fi

    for m in "${matches[@]}"; do
        if [[ -e "$m" || -L "$m" ]]; then
            if execute_cleanup_item "$m" "$strategy" "$is_child"; then
                ((OBJ_ITEMS_COUNT++))
                ((TOTAL_ITEMS_CLEANED++))
            fi
        fi
    done

done < <(get_targets_data)

# Mostrar el recompte de l'últim objectiu
if [[ $OBJ_ITEMS_COUNT -gt 0 ]]; then
    echo "     -> $OBJ_ITEMS_COUNT element(s) trobat(s) i processat(s)."
elif [[ "$VERBOSE" == "true" ]]; then
    echo "     -> Cap fitxer o directori coincident."
fi

echo ""
echo "=============================================================================="
echo " Resum de la neteja:"
echo "   - Objectius de neteja executats : $PROCESSED_OBJECTIVES de $TOTAL_OBJECTIVES"
echo "   - Total d'elements processats   : $TOTAL_ITEMS_CLEANED"
if [[ "$DRY_RUN" == "true" ]]; then
    echo "   - Estat: Simulació finalitzada sense canvis en el disc."
else
    echo "   - Estat: Neteja completada correctament."
fi
echo "=============================================================================="
