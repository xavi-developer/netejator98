"""IPC protocol message definitions, request/response models, and command constants."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Dict, Optional


class IPCCommands:
    GET_STATUS = "GET_STATUS"
    IDENTIFY_USER = "IDENTIFY_USER"
    ADMIN_AUTH = "ADMIN_AUTH"
    ADMIN_SETUP_PASSWORD = "ADMIN_SETUP_PASSWORD"
    ADMIN_GET_LOGS = "ADMIN_GET_LOGS"
    ADMIN_EXPORT_LOGS = "ADMIN_EXPORT_LOGS"
    ADMIN_VERIFY_CHAIN = "ADMIN_VERIFY_CHAIN"
    ADMIN_FORCE_CLEAN = "ADMIN_FORCE_CLEAN"
    ADMIN_GET_POLICY = "ADMIN_GET_POLICY"
    ADMIN_UPDATE_POLICY = "ADMIN_UPDATE_POLICY"
    ADMIN_RESET_POLICY = "ADMIN_RESET_POLICY"
    ADMIN_CHANGE_PASSWORD = "ADMIN_CHANGE_PASSWORD"
    ADMIN_BYPASS = "ADMIN_BYPASS"
    SET_DAEMON_STATE = "SET_DAEMON_STATE"


@dataclass(frozen=True)
class IPCRequest:
    """Structured request sent from presentation UI to privileged agent."""

    command: str
    payload: Dict[str, Any] = field(default_factory=dict)
    session_token: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "command": self.command,
                "payload": self.payload,
                "session_token": self.session_token,
            }
        )

    @classmethod
    def from_json(cls, data: str) -> IPCRequest:
        parsed = json.loads(data)
        return cls(
            command=parsed["command"],
            payload=parsed.get("payload", {}),
            session_token=parsed.get("session_token"),
        )


@dataclass(frozen=True)
class IPCResponse:
    """Structured response returned from privileged agent to presentation UI."""

    status: str  # "OK" or "ERROR"
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    @classmethod
    def ok(cls, data: Optional[Dict[str, Any]] = None) -> IPCResponse:
        return cls(status="OK", data=data or {})

    @classmethod
    def error(cls, code: str, message: str) -> IPCResponse:
        return cls(status="ERROR", error_code=code, error_message=message)

    def to_json(self) -> str:
        return json.dumps(
            {
                "status": self.status,
                "data": self.data,
                "error_code": self.error_code,
                "error_message": self.error_message,
            }
        )

    @classmethod
    def from_json(cls, data: str) -> IPCResponse:
        parsed = json.loads(data)
        return cls(
            status=parsed["status"],
            data=parsed.get("data"),
            error_code=parsed.get("error_code"),
            error_message=parsed.get("error_message"),
        )

