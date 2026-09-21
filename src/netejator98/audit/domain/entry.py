"""AuditEntry value object representing plaintext security event data."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AuditEntry:
    """Plaintext audit event entry before sealing."""

    timestamp: datetime
    machine_id: str
    hostname: str
    event_type: str
    email: Optional[str]
    outcome: str
    targets_cleaned: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json_bytes(self) -> bytes:
        """Serialize entry to canonical UTF-8 JSON bytes for cryptographic sealing."""
        payload = {
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
            "machine_id": self.machine_id,
            "hostname": self.hostname,
            "event_type": self.event_type,
            "email": self.email,
            "outcome": self.outcome,
            "targets_cleaned": self.targets_cleaned,
            "errors": self.errors,
            "metadata": self.metadata,
        }
        return json.dumps(payload, sort_keys=True).encode("utf-8")

    @classmethod
    def from_json_bytes(cls, data: bytes) -> AuditEntry:
        """Deserialize from decrypted JSON bytes."""
        payload = json.loads(data.decode("utf-8"))
        return cls(
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            machine_id=payload["machine_id"],
            hostname=payload["hostname"],
            event_type=payload["event_type"],
            email=payload.get("email"),
            outcome=payload.get("outcome", "SUCCESS"),
            targets_cleaned=payload.get("targets_cleaned", []),
            errors=payload.get("errors", []),
            metadata=payload.get("metadata", {}),
        )

