"""AdminCredential and AdminSession value objects in access domain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid


@dataclass(frozen=True)
class AdminCredential:
    """Administrator password input value object."""

    password: str

    def __post_init__(self) -> None:
        if not self.password:
            raise ValueError("Admin password cannot be empty")

    def validate_strength(self, min_length: int = 8) -> None:
        """Enforce password strength policy for setting or changing admin password."""
        if len(self.password) < min_length:
            raise ValueError(f"Admin password must be at least {min_length} characters long")


@dataclass(frozen=True)
class AdminSession:
    """Authenticated administrator session token required for privileged operations."""

    session_id: str
    authenticated_at: datetime
    expires_at: datetime

    @classmethod
    def create(cls, ttl_minutes: int = 15, current_time: datetime | None = None) -> AdminSession:
        now = current_time or datetime.now(timezone.utc)
        return cls(
            session_id=uuid.uuid4().hex,
            authenticated_at=now,
            expires_at=now + timedelta(minutes=ttl_minutes),
        )

    def is_valid(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        return current < self.expires_at

