#!/usr/bin/env bash
# ==============================================================================
# Netejator98 macOS Installation Script
# Installs privileged LaunchDaemon and interactive LaunchAgent.
# ==============================================================================

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "[-] Error: This installer must be run with sudo (sudo ./install.sh)" >&2
    exit 1
fi

echo "[+] Installing Netejator98 on macOS..."

STORAGE_DIR="/var/lib/netejator98"
RUN_DIR="/var/run/netejator98"
BIN_DIR="/usr/local/bin"
DAEMON_DIR="/Library/LaunchDaemons"
AGENT_DIR="/Library/LaunchAgents"

# 1. Create secure storage directory
echo "[+] Creating secure storage directories..."
mkdir -p "${STORAGE_DIR}"
chmod 0700 "${STORAGE_DIR}"
chown root:wheel "${STORAGE_DIR}"

mkdir -p "${RUN_DIR}"
chmod 0755 "${RUN_DIR}"
chown root:wheel "${RUN_DIR}"

# 2. Install application binary or wrapper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if command -v pip3 >/dev/null 2>&1; then
    echo "[+] Installing Python package netejator98..."
    pip3 install "${REPO_ROOT}"
fi

mkdir -p "${BIN_DIR}"
if ! command -v netejator98 >/dev/null 2>&1; then
    cat << 'EOF' > "${BIN_DIR}/netejator98"
#!/usr/bin/env bash
exec python3 -m netejator98.main "$@"
EOF
    chmod 0755 "${BIN_DIR}/netejator98"
fi

# 3. Copy default policy
if [[ ! -f "${STORAGE_DIR}/config.yaml" ]]; then
    if [[ -f "${REPO_ROOT}/policies/defaults/macos.yaml" ]]; then
        cp "${REPO_ROOT}/policies/defaults/macos.yaml" "${STORAGE_DIR}/config.yaml"
        chmod 0640 "${STORAGE_DIR}/config.yaml"
        echo "[+] Default macOS cleaning policy installed at ${STORAGE_DIR}/config.yaml"
    fi
fi

# 4. Install LaunchDaemon
echo "[+] Installing LaunchDaemon (cat.insestatut.netejator98.agent)..."
cp "${SCRIPT_DIR}/cat.insestatut.netejator98.agent.plist" "${DAEMON_DIR}/cat.insestatut.netejator98.agent.plist"
chown root:wheel "${DAEMON_DIR}/cat.insestatut.netejator98.agent.plist"
chmod 0644 "${DAEMON_DIR}/cat.insestatut.netejator98.agent.plist"

launchctl unload "${DAEMON_DIR}/cat.insestatut.netejator98.agent.plist" 2>/dev/null || true
launchctl load -w "${DAEMON_DIR}/cat.insestatut.netejator98.agent.plist"
echo "[+] LaunchDaemon loaded."

# 5. Install LaunchAgent
echo "[+] Installing LaunchAgent (cat.insestatut.netejator98.ui)..."
mkdir -p "${AGENT_DIR}"
cp "${SCRIPT_DIR}/cat.insestatut.netejator98.ui.plist" "${AGENT_DIR}/cat.insestatut.netejator98.ui.plist"
chown root:wheel "${AGENT_DIR}/cat.insestatut.netejator98.ui.plist"
chmod 0644 "${AGENT_DIR}/cat.insestatut.netejator98.ui.plist"

echo "[✓] Netejator98 macOS installation completed successfully!"
echo "[i] Privileged daemon running. Kiosk prompt will appear on user Aqua session login."

