"""Composition root wiring OS-specific adapters, storage directories, and presentation layers."""

from __future__ import annotations

import os
from pathlib import Path
import platform
from typing import Optional

from netejator98.agent.daemon import AgentDaemon
from netejator98.agent.ipc_server import IPCServer
from netejator98.presentation.admin_view import AdminView
from netejator98.presentation.ipc_client import IPCClient
from netejator98.presentation.kiosk_view import KioskView
from netejator98.presentation.view_models import AdminViewModel, KioskViewModel


def get_default_storage_dir() -> Path:
    """Return platform protected persistence directory with fallback for dev mode."""
    system = platform.system().lower()

    if system == "windows":
        prog_data = os.environ.get("ProgramData", "C:/ProgramData")
        candidate = Path(prog_data) / "Netejator98"
    elif system == "darwin":
        candidate = Path("/Library/Application Support/Netejator98")
    else:
        candidate = Path("/var/lib/netejator98")

    # If system directory is not writable by current user, fallback to user dev dir
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        test_file = candidate / ".perm_check"
        test_file.touch()
        test_file.unlink()
        return candidate
    except OSError:
        fallback = Path.home() / ".local" / "share" / "netejator98"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def get_default_ipc_endpoint(storage_dir: str | Path | None = None) -> tuple[str | None, int | None]:
    """Return (socket_path, port) for the current platform and storage directory."""
    if storage_dir:
        sock_path = Path(storage_dir) / "agent.sock"
        return str(sock_path), None

    system = platform.system().lower()
    if system == "windows":
        # Windows loopback port fallback
        return None, 49898
    else:
        primary = Path("/run/netejator98/agent.sock")
        fallback = Path(f"/tmp/netejator98_{os.getuid()}.sock")
        if primary.exists():
            return str(primary), None
        try:
            primary.parent.mkdir(parents=True, exist_ok=True)
            if os.access(primary.parent, os.W_OK):
                return str(primary), None
        except OSError:
            pass
        return str(fallback), None


def create_agent(
    storage_dir: str | Path | None = None,
    socket_path: str | Path | None = None,
    port: int | None = None,
) -> tuple[AgentDaemon, IPCServer]:
    """Wire and return privileged AgentDaemon and IPCServer."""
    s_dir = Path(storage_dir) if storage_dir else get_default_storage_dir()
    default_sock, default_port = get_default_ipc_endpoint(storage_dir)

    sock = str(socket_path) if socket_path else default_sock
    p = port or default_port

    daemon = AgentDaemon(storage_dir=s_dir)
    server = IPCServer(daemon, socket_path=sock, port=p)
    return daemon, server


def create_client(
    storage_dir: str | Path | None = None,
    socket_path: str | Path | None = None,
    port: int | None = None,
) -> IPCClient:
    """Wire IPCClient pointing to agent endpoint."""
    default_sock, default_port = get_default_ipc_endpoint(storage_dir)
    sock = str(socket_path) if socket_path else default_sock
    p = port or default_port
    return IPCClient(socket_path=sock, port=p, storage_dir=storage_dir)


def create_kiosk_app(client: IPCClient) -> KioskView:
    """Wire KioskView with KioskViewModel and AdminView trigger."""
    kiosk_vm = KioskViewModel(client)
    admin_vm = AdminViewModel(client)

    app_holder: list[Optional[KioskView]] = [None]

    def open_admin() -> None:
        parent_root = app_holder[0].root if app_holder[0] else None
        admin_view = AdminView(admin_vm, parent=parent_root)
        admin_view.show()

    app = KioskView(view_model=kiosk_vm, on_admin_requested=open_admin)
    app_holder[0] = app
    return app


def create_admin_app(client: IPCClient) -> AdminView:
    """Wire standalone AdminView."""
    admin_vm = AdminViewModel(client)
    return AdminView(admin_vm)

