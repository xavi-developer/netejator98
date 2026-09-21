"""CLI and GUI entry point for Netejator98."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import signal
import sys
import time

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

    args = parser.parse_args()
    set_language(args.lang)

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
                print(f"✓ Hash chain integrity VALID. Total records verified: {v.total_entries}")
                sys.exit(0)
            else:
                print(f"✗ Hash chain TAMPERING DETECTED at sequence {v.tampered_seq}!")
                print(f"  Reason: {v.failure_reason}")
                sys.exit(1)
        elif storage_path and (storage_path / "audit_trail.jsonl").exists():
            from netejator98.audit.application.verify_chain import VerifyChainIntegrityUseCase
            from netejator98.audit.infrastructure.sealed_repo import EncryptedJsonlAuditRepository

            repo = EncryptedJsonlAuditRepository(storage_dir=storage_path)
            v = VerifyChainIntegrityUseCase(repo).execute()
            if v.is_valid:
                print(f"✓ Hash chain integrity VALID. Total records verified: {v.total_entries}")
                sys.exit(0)
            else:
                print(f"✗ Hash chain TAMPERING DETECTED at sequence {v.tampered_seq}!")
                print(f"  Reason: {v.failure_reason}")
                sys.exit(1)
        else:
            # Fall back to IPC agent query
            client = create_client(storage_dir=args.storage_dir, socket_path=args.socket, port=args.port)
            res = client.admin_verify_chain()
            if res.is_ok():
                v = res.unwrap()
                if v.get("is_valid"):
                    print(f"✓ Hash chain integrity VALID. Total records verified: {v.get('total_entries', 0)}")
                    sys.exit(0)
                else:
                    print(f"✗ Hash chain TAMPERING DETECTED at sequence {v.get('tampered_seq')}!")
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
    client = create_client(storage_dir=args.storage_dir, socket_path=args.socket, port=args.port)
    if args.standalone:
        client.socket_path = None
        client.port = None

    try:
        if is_admin:
            print("[Netejator98] Starting Administration Dashboard...")
            app = create_admin_app(client)
            app.show()
        else:
            # Default: Kiosk prompt
            print("[Netejator98] Starting Kiosk User Interface...")
            app = create_kiosk_app(client)
            app.show()
    except Exception as e:
        print(f"[Netejator98] Error launching graphical interface: {e}", file=sys.stderr)
        print("[Netejator98] If you are in a headless environment without an X11/Wayland display, use CLI commands like 'netejator98 agent' or 'netejator98 verify-audit'.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
