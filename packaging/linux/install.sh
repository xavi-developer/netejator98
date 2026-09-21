#!/usr/bin/env bash
# ==============================================================================
# Netejator98 Linux Installation Script
# Installs privileged daemon service and user session kiosk autostart.
# ==============================================================================

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "[-] Error: This installer must be run as root (e.g., sudo ./packaging/linux/install.sh)" >&2
    exit 1
fi

echo "[+] Installing Netejator98 on Linux..."

STORAGE_DIR="/var/lib/netejator98"
CONFIG_DIR="/etc/netejator98"
RUN_DIR="/run/netejator98"
BIN_DIR="/usr/local/bin"
APP_DIR="/opt/netejator98"
SYSTEMD_DIR="/etc/systemd/system"
AUTOSTART_DIR="/etc/xdg/autostart"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 1. Verify required Python modules
echo "[+] Checking required Python libraries..."
if ! python3 -c "import nacl, cryptography, yaml, tkinter" 2>/dev/null; then
    echo "[!] Missing required Python packages. Attempting to install via apt..."
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq
        apt-get install -y -qq python3-nacl python3-cryptography python3-yaml python3-tk
    else
        echo "[-] Please install python3-nacl, python3-cryptography, python3-yaml, and python3-tk using your system package manager." >&2
        exit 1
    fi
fi
echo "[+] Python dependencies verified."

# 2. Create secure storage directories with restrictive permissions
echo "[+] Creating secure storage directories..."
mkdir -p "${STORAGE_DIR}"
chmod 0700 "${STORAGE_DIR}"
chown root:root "${STORAGE_DIR}"

mkdir -p "${RUN_DIR}"
chmod 0755 "${RUN_DIR}"
chown root:root "${RUN_DIR}"

mkdir -p "${CONFIG_DIR}"
chmod 0755 "${CONFIG_DIR}"

# 3. Deploy application files to /opt/netejator98 (PEP 668 compliant, no pip needed)
echo "[+] Deploying application files to ${APP_DIR}..."
mkdir -p "${APP_DIR}"
rm -rf "${APP_DIR}/src" "${APP_DIR}/policies"
cp -r "${REPO_ROOT}/src" "${APP_DIR}/"
cp -r "${REPO_ROOT}/policies" "${APP_DIR}/"
chmod -R 0755 "${APP_DIR}"

# 4. Install /usr/local/bin/netejator98 wrapper executable
echo "[+] Installing ${BIN_DIR}/netejator98 executable wrapper..."
cat << 'EOF' > "${BIN_DIR}/netejator98"
#!/usr/bin/env bash
export PYTHONPATH="/opt/netejator98/src:${PYTHONPATH:-}"
exec /usr/bin/python3 -m netejator98.main "$@"
EOF
chmod 0755 "${BIN_DIR}/netejator98"

# 5. Copy default policy (ensuring safe dry-run mode and all targets disabled for testing)
if [[ -f "${REPO_ROOT}/policies/defaults/linux.yaml" ]]; then
    if [[ -f "${STORAGE_DIR}/config.yaml" ]]; then
        cp "${STORAGE_DIR}/config.yaml" "${STORAGE_DIR}/config.yaml.bak"
    fi
    cp "${REPO_ROOT}/policies/defaults/linux.yaml" "${STORAGE_DIR}/config.yaml"
    chmod 0640 "${STORAGE_DIR}/config.yaml"
    echo "[+] Linux cleaning policy deployed at ${STORAGE_DIR}/config.yaml (dry_run: true, targets disabled)."
fi

# Ensure daemon protection state is disabled by default for testing
if [[ ! -f "${STORAGE_DIR}/daemon_state.json" ]]; then
    echo '{"enabled": false}' > "${STORAGE_DIR}/daemon_state.json"
    chmod 0640 "${STORAGE_DIR}/daemon_state.json"
    echo "[+] Daemon protection initialized as DISABLED by default."
fi

# 6. Install systemd service unit
echo "[+] Installing systemd service unit..."
cp "${SCRIPT_DIR}/netejator98-agent.service" "${SYSTEMD_DIR}/netejator98-agent.service"
chmod 0644 "${SYSTEMD_DIR}/netejator98-agent.service"

systemctl daemon-reload
systemctl enable netejator98-agent.service
systemctl restart netejator98-agent.service
echo "[+] netejator98-agent.service enabled and started."

# 7. Install XDG autostart entry for graphical user desktop sessions
echo "[+] Installing desktop autostart entry..."
mkdir -p "${AUTOSTART_DIR}"
cp "${SCRIPT_DIR}/netejator98-ui.desktop" "${AUTOSTART_DIR}/netejator98-ui.desktop"
chmod 0644 "${AUTOSTART_DIR}/netejator98-ui.desktop"

echo ""
echo "=============================================================================="
echo "[✓] Netejator98 Linux installation completed successfully!"
echo "[i] Privileged daemon running via systemd (netejator98-agent.service)."
echo "[i] Kiosk will display automatically on next graphical desktop login."
echo "[i] You can test the kiosk UI now by running: netejator98 ui"
echo "=============================================================================="
