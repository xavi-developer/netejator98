"""IPCClient providing high-level typed communication to the privileged Agent daemon."""

from __future__ import annotations

import os
from pathlib import Path
import socket
from typing import Any, Dict, List, Optional

from netejator98.agent.protocol import IPCCommands, IPCRequest, IPCResponse
from netejator98.shared.errors import DomainError, IPCCommunicationError
from netejator98.shared.result import Err, Ok, Result


class IPCClient:
    """Client used by presentation UI to interact with agent daemon over IPC or direct in-process fallback."""

    def __init__(
        self,
        socket_path: Optional[str | Path] = None,
        port: Optional[int] = None,
        timeout_seconds: float = 30.0,
        storage_dir: Optional[str | Path] = None,
        allow_in_process_fallback: bool = True,
    ) -> None:
        self.socket_path = str(socket_path) if socket_path else None
        self.port = port
        self.timeout = timeout_seconds
        self.storage_dir = Path(storage_dir) if storage_dir else None
        self.allow_in_process_fallback = allow_in_process_fallback
        self._in_process_daemon: Optional[Any] = None
        self._is_in_process_mode = False

    @property
    def in_process_daemon(self) -> Any:
        if self._in_process_daemon is None:
            from netejator98.agent.daemon import AgentDaemon
            from netejator98.composition_root import get_default_storage_dir
            s_dir = self.storage_dir or get_default_storage_dir()
            self._in_process_daemon = AgentDaemon(storage_dir=s_dir)
        return self._in_process_daemon

    @property
    def is_in_process(self) -> bool:
        return self._is_in_process_mode

    def _send_request(self, request: IPCRequest) -> Result[IPCResponse, DomainError]:
        # If socket path is configured and exists on disk, or port is configured, try socket first
        socket_exists = bool(self.socket_path and Path(self.socket_path).exists())
        if socket_exists or self.port:
            try:
                if self.socket_path and socket_exists:
                    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    sock.settimeout(self.timeout)
                    sock.connect(self.socket_path)
                elif self.port:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(self.timeout)
                    sock.connect(("127.0.0.1", self.port))
                else:
                    sock = None

                if sock is not None:
                    with sock:
                        msg = (request.to_json() + "\n").encode("utf-8")
                        sock.sendall(msg)

                        response_line = ""
                        while "\n" not in response_line:
                            chunk = sock.recv(4096).decode("utf-8")
                            if not chunk:
                                break
                            response_line += chunk

                        if not response_line.strip():
                            return Err(IPCCommunicationError("Empty response from agent daemon"))

                        resp = IPCResponse.from_json(response_line.strip())
                        self._is_in_process_mode = False
                        return Ok(resp)
            except OSError as e:
                if not self.allow_in_process_fallback:
                    return Err(IPCCommunicationError(f"Could not connect to Netejator98 agent daemon: {e}"))

        # Fallback to direct in-process execution when daemon service is not running
        if self.allow_in_process_fallback:
            self._is_in_process_mode = True
            resp = self.in_process_daemon.dispatch(request)
            return Ok(resp)

        return Err(IPCCommunicationError("Neither socket_path nor port configured or reachable for IPCClient"))

    def get_status(self) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(command=IPCCommands.GET_STATUS)
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Failed to get status", code=resp.error_code or "ERROR"))
        return Ok(resp.data or {})

    def admin_setup_password(self, new_password: str) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(
            command=IPCCommands.ADMIN_SETUP_PASSWORD,
            payload={"new_password": new_password},
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Setup failed", code=resp.error_code or "ERROR"))
        return Ok(resp.data or {})

    def admin_auth(self, password: str) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(
            command=IPCCommands.ADMIN_AUTH,
            payload={"password": password},
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Auth failed", code=resp.error_code or "AUTH_FAILED"))
        return Ok(resp.data or {})

    def identify_user(
        self, email: str, target_user_home: Optional[str] = None
    ) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(
            command=IPCCommands.IDENTIFY_USER,
            payload={"email": email, "target_user_home": target_user_home},
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Identification failed", code=resp.error_code or "ID_FAILED"))
        return Ok(resp.data or {})

    def admin_verify_chain(self) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(command=IPCCommands.ADMIN_VERIFY_CHAIN)
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Verification failed", code=resp.error_code or "VERIFY_FAILED"))
        return Ok(resp.data or {})

    def admin_get_logs(
        self, session_token: str, limit: Optional[int] = None
    ) -> Result[List[Dict[str, Any]], DomainError]:
        req = IPCRequest(
            command=IPCCommands.ADMIN_GET_LOGS,
            session_token=session_token,
            payload={"limit": limit},
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Get logs failed", code=resp.error_code or "QUERY_FAILED"))
        return Ok(resp.data.get("entries", []) if resp.data else [])

    def admin_export_logs(
        self, session_token: str, export_path: str
    ) -> Result[str, DomainError]:
        req = IPCRequest(
            command=IPCCommands.ADMIN_EXPORT_LOGS,
            session_token=session_token,
            payload={"export_path": export_path},
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Export failed", code=resp.error_code or "EXPORT_FAILED"))
        return Ok(export_path)

    def admin_force_clean(
        self, session_token: str, target_user_home: Optional[str] = None
    ) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(
            command=IPCCommands.ADMIN_FORCE_CLEAN,
            session_token=session_token,
            payload={"target_user_home": target_user_home},
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Force clean failed", code=resp.error_code or "CLEAN_FAILED"))
        return Ok(resp.data or {})

    def admin_get_policy(self, session_token: str) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(
            command=IPCCommands.ADMIN_GET_POLICY,
            session_token=session_token,
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Get policy failed", code=resp.error_code or "POLICY_FAILED"))
        return Ok(resp.data.get("policy", {}) if resp.data else {})

    def admin_update_policy(
        self, session_token: str, policy_data: Dict[str, Any]
    ) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(
            command=IPCCommands.ADMIN_UPDATE_POLICY,
            session_token=session_token,
            payload={"policy": policy_data},
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Update policy failed", code=resp.error_code or "POLICY_FAILED"))
        return Ok(resp.data.get("policy", {}) if resp.data else {})

    def admin_reset_policy(self, session_token: str) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(
            command=IPCCommands.ADMIN_RESET_POLICY,
            session_token=session_token,
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Reset policy failed", code=resp.error_code or "POLICY_FAILED"))
        return Ok(resp.data.get("policy", {}) if resp.data else {})

    def admin_change_password(
        self, session_token: str, old_password: str, new_password: str
    ) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(
            command=IPCCommands.ADMIN_CHANGE_PASSWORD,
            session_token=session_token,
            payload={"old_password": old_password, "new_password": new_password},
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Change password failed", code=resp.error_code or "PWD_FAILED"))
        return Ok(resp.data or {})

    def admin_bypass(self, password: str) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(
            command=IPCCommands.ADMIN_BYPASS,
            payload={"password": password},
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Admin bypass failed", code=resp.error_code or "BYPASS_FAILED"))
        return Ok(resp.data or {})

    def set_daemon_state(self, session_token: str, enabled: bool) -> Result[Dict[str, Any], DomainError]:
        req = IPCRequest(
            command=IPCCommands.SET_DAEMON_STATE,
            session_token=session_token,
            payload={"enabled": enabled},
        )
        res = self._send_request(req)
        if res.is_err():
            return Err(res.unwrap_err())
        resp = res.unwrap()
        if resp.status != "OK":
            return Err(DomainError(resp.error_message or "Set daemon state failed", code=resp.error_code or "STATE_FAILED"))
        return Ok(resp.data or {})

