"""CLI and GUI entry point for Netejator98."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import signal
import sys
import time

# Ensure UTF-8 output encoding with safe replacement on non-UTF-8 consoles (e.g. Windows cp1252)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from netejator98.composition_root import (
    create_admin_app,
    create_agent,
    create_client,
    create_kiosk_app,
    get_default_storage_dir,
)
from netejator98.presentation.i18n import set_language


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="netejator98",
        description="Netejator98 - Cross-platform shared-PC sanitizer with DDD architecture",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["ui", "agent", "admin", "verify-audit", "verify-log", "enable-daemon", "disable-daemon"],
        default=None,
        help="Command to execute: 'ui' (default kiosk), 'agent' (daemon), 'admin' (admin dashboard), 'verify-audit', 'enable-daemon', 'disable-daemon'",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Optional target path for commands (e.g. audit log file or storage directory for verify-audit)",
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Run as privileged background service / daemon (alias for 'agent' command)",
    )
    parser.add_argument(
        "--admin",
        action="store_true",
        help="Launch the Administration dashboard directly (alias for 'admin' command)",
    )
    parser.add_argument(
        "--lang",
        choices=["ca", "es", "en"],
        default="ca",
        help="UI Language (ca: Catalan [default], es: Spanish, en: English)",
    )
    parser.add_argument(
        "--storage",
        "--storage-dir",
        dest="storage_dir",
        type=str,
        default=None,
        help="Override protected storage directory path",
    )
    parser.add_argument(
        "--socket",
        type=str,
        default=None,
        help="Override IPC socket path",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Override IPC TCP port",
    )
    parser.add_argument(
        "--standalone",
        "--no-daemon",
        dest="standalone",
        action="store_true",
        help="Run without background daemon service (embedded in-process mode)",
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Verify all runtime dependencies (GUI and cryptography) are embedded and accessible",
    )

    args = parser.parse_args()
    set_language(args.lang)

    # Fast verification of embedded dependencies (used by build verification test)
    if args.check_deps:
        missing = []
        for mod in ["nacl", "cryptography", "yaml", "tkinter", "tkinter.ttk"]:
            try:
                __import__(mod)
            except Exception as e:
                missing.append(f"{mod} ({e})")
        if missing:
            print(f"[FAIL] Missing bundled dependencies: {', '.join(missing)}", file=sys.stderr)
            sys.exit(1)
        print("[OK] All runtime dependencies (PyNaCl, Cryptography, PyYAML, Tkinter) verified.")
        sys.exit(0)

    is_agent = args.agent or (args.command == "agent")
    is_admin = args.admin or (args.command == "admin")
    is_verify = args.command in ("verify-audit", "verify-log")

    # 1. Privileged Agent mode
    if is_agent:
        print("[Netejator98] Starting privileged agent daemon...")
        daemon, server = create_agent(
            storage_dir=args.storage_dir,
            socket_path=args.socket,
            port=args.port,
        )
        server.start()
        print(f"[Netejator98] Agent running. Storage: {daemon.storage_dir}")
        if server.socket_path:
            print(f"[Netejator98] Listening on Unix socket: {server.socket_path}")
        else:
            print(f"[Netejator98] Listening on port: {server.port}")

        def _handle_shutdown(signum, frame):
            print("\n[Netejator98] Stopping agent...")
            server.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, _handle_shutdown)
        signal.signal(signal.SIGTERM, _handle_shutdown)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            _handle_shutdown(None, None)
        sys.exit(0)

    # 2. Unauthenticated verify-audit / verify-log command (offline or online)
    if is_verify:
        # Check if verifying directly from disk path
        target_path = Path(args.target) if args.target else None
        storage_path = Path(args.storage_dir) if args.storage_dir else None

        if target_path and target_path.exists():
            from netejator98.audit.application.verify_chain import VerifyChainIntegrityUseCase
            from netejator98.audit.infrastructure.sealed_repo import EncryptedJsonlAuditRepository

            if target_path.is_file():
                repo = EncryptedJsonlAuditRepository(
                    storage_dir=target_path.parent,
                    filename=target_path.name,
                )
            else:
                repo = EncryptedJsonlAuditRepository(storage_dir=target_path)

            v = VerifyChainIntegrityUseCase(repo).execute()
            if v.is_valid:
                print(f"[OK] Hash chain integrity VALID. Total records verified: {v.total_entries}")
                sys.exit(0)
            else:
                print(f"[FAIL] Hash chain TAMPERING DETECTED at sequence {v.tampered_seq}!")
                print(f"  Reason: {v.failure_reason}")
                sys.exit(1)
        elif storage_path and (storage_path / "audit_trail.jsonl").exists():
            from netejator98.audit.application.verify_chain import VerifyChainIntegrityUseCase
            from netejator98.audit.infrastructure.sealed_repo import EncryptedJsonlAuditRepository

            repo = EncryptedJsonlAuditRepository(storage_dir=storage_path)
            v = VerifyChainIntegrityUseCase(repo).execute()
            if v.is_valid:
                print(f"[OK] Hash chain integrity VALID. Total records verified: {v.total_entries}")
                sys.exit(0)
            else:
                print(f"[FAIL] Hash chain TAMPERING DETECTED at sequence {v.tampered_seq}!")
                print(f"  Reason: {v.failure_reason}")
                sys.exit(1)
        else:
            # Fall back to IPC agent query
            client = create_client(storage_dir=args.storage_dir, socket_path=args.socket, port=args.port)
            res = client.admin_verify_chain()
            if res.is_ok():
                v = res.unwrap()
                if v.get("is_valid"):
                    print(f"[OK] Hash chain integrity VALID. Total records verified: {v.get('total_entries', 0)}")
                    sys.exit(0)
                else:
                    print(f"[FAIL] Hash chain TAMPERING DETECTED at sequence {v.get('tampered_seq')}!")
                    print(f"  Reason: {v.get('failure_reason')}")
                    sys.exit(1)
            else:
                print(f"Error connecting to agent daemon: {res.unwrap_err().message}")
                print("Tip: If the agent is offline, specify the file directly: 'netejator98 verify-audit /path/to/audit_trail.jsonl'")
                sys.exit(2)

    # 3. Enable / Disable Daemon state commands
    if args.command in ("enable-daemon", "disable-daemon"):
        import json
        new_state = (args.command == "enable-daemon")
        storage_path = Path(args.storage_dir) if args.storage_dir else get_default_storage_dir()
        state_file = storage_path / "daemon_state.json"
        storage_path.mkdir(parents=True, exist_ok=True)
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump({"enabled": new_state}, f)
            print(f"[Netejator98] Daemon state updated to: {'ENABLED' if new_state else 'DISABLED'} ({state_file})")
        except Exception as e:
            print(f"[Netejator98] Error updating daemon state file: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # 4. GUI Client modes
    print(f"[DEBUG-MAIN] Initializing GUI client. is_admin={is_admin}, standalone={args.standalone}, lang={args.lang}", flush=True)
    client = create_client(storage_dir=args.storage_dir, socket_path=args.socket, port=args.port)
    if args.standalone:
        print("[DEBUG-MAIN] Standalone mode: forcing in-process client (socket_path=None, port=None)", flush=True)
        client.socket_path = None
        client.port = None

    try:
        if is_admin:
            now_s = time.strftime("%H:%M:%S")
            try:
                os.write(2, f"[{now_s}] [DEBUG-MAIN] Starting Administration Dashboard...\n".encode("utf-8"))
                os.write(2, f"[{now_s}] [DEBUG-MAIN] Calling create_admin_app(client)...\n".encode("utf-8"))
            except Exception:
                pass
            app = create_admin_app(client)
            try:
                os.write(2, f"[{now_s}] [DEBUG-MAIN] create_admin_app returned successfully. Now calling app.show()...\n".encode("utf-8"))
            except Exception:
                pass
            app.show()
            try:
                os.write(2, f"[{now_s}] [DEBUG-MAIN] app.show() exited.\n".encode("utf-8"))
            except Exception:
                pass
        else:
            # Default: Kiosk prompt
            print("[Netejator98] Starting Kiosk User Interface...")
            app = create_kiosk_app(client)
            app.show()
    except ModuleNotFoundError as e:
        if "tkinter" in str(e).lower():
            print(f"\n[Netejator98] Error: Graphical interface requires 'tkinter' (Tcl/Tk): {e}", file=sys.stderr)
            print("If running from source, please install system Tkinter support on Linux:", file=sys.stderr)
            print("  Ubuntu / Debian: sudo apt install -y python3-tk", file=sys.stderr)
            print("  Fedora / RHEL:   sudo dnf install -y python3-tkinter", file=sys.stderr)
            print("  Arch Linux:      sudo pacman -S tk\n", file=sys.stderr)
            print("Or build/run the pre-built standalone release binary which bundles all dependencies.", file=sys.stderr)
        else:
            print(f"[Netejator98] Missing required module: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[Netejator98] Error launching graphical interface: {e}", file=sys.stderr)
        print("[Netejator98] If you are in a headless environment without an X11/Wayland display, use CLI commands like 'netejator98 agent' or 'netejator98 verify-audit'.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
