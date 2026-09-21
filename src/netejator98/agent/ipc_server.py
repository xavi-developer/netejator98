"""IPCServer providing Unix Domain Socket / Named Pipe local endpoint."""

from __future__ import annotations

import os
from pathlib import Path
import socket
import threading
from typing import Optional

from netejator98.agent.daemon import AgentDaemon
from netejator98.agent.protocol import IPCRequest, IPCResponse


class IPCServer:
    """Multi-threaded local IPC server communicating over Unix Domain Sockets or TCP loopback."""

    def __init__(
        self,
        daemon: AgentDaemon,
        socket_path: Optional[str | Path] = None,
        port: Optional[int] = None,
    ) -> None:
        self.daemon = daemon
        self.socket_path = str(socket_path) if socket_path else None
        self.port = port
        self._running = False
        self._server_socket: Optional[socket.socket] = None
        self._server_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the IPC server in a background thread."""
        self._running = True

        if self.socket_path:
            # Unix domain socket
            sock_p = Path(self.socket_path)
            sock_p.parent.mkdir(parents=True, exist_ok=True)
            if sock_p.exists():
                try:
                    sock_p.unlink()
                except OSError:
                    pass

            old_umask = os.umask(0)
            try:
                self._server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self._server_socket.bind(self.socket_path)
                os.chmod(self.socket_path, 0o666)
            finally:
                os.umask(old_umask)
        else:
            # TCP loopback fallback (e.g. for Windows or dev testing)
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind(("127.0.0.1", self.port or 0))
            self.port = self._server_socket.getsockname()[1]

        self._server_socket.listen(16)
        self._server_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._server_thread.start()

    def _listen_loop(self) -> None:
        while self._running and self._server_socket:
            try:
                client_sock, _ = self._server_socket.accept()
                t = threading.Thread(
                    target=self._handle_client, args=(client_sock,), daemon=True
                )
                t.start()
            except OSError:
                break

    def _handle_client(self, client_sock: socket.socket) -> None:
        with client_sock:
            client_sock.settimeout(30.0)
            buffer = ""
            while self._running:
                try:
                    data = client_sock.recv(4096)
                    if not data:
                        break
                    buffer += data.decode("utf-8")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            req = IPCRequest.from_json(line)
                            resp = self.daemon.dispatch(req)
                        except Exception as e:
                            resp = IPCResponse.error("PROTOCOL_ERROR", str(e))

                        resp_bytes = (resp.to_json() + "\n").encode("utf-8")
                        client_sock.sendall(resp_bytes)
                except (socket.timeout, OSError):
                    break

    def stop(self) -> None:
        """Stop server and clean up socket file."""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None

        if self.socket_path and os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except OSError:
                pass

        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=1.0)

