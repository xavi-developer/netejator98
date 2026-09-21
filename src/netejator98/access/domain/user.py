"""User entity and LastUserRecord value object."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

from netejator98.access.domain.email import InstitutionalEmail


@dataclass(frozen=True)
class LastUserRecord:
    """Privacy-preserving record of the last user on the machine.

    Stores only a salted hash and timestamp, never the plaintext email address.
    """

    email_hash: str
    salt: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        if not self.email_hash or not self.salt:
            raise ValueError("email_hash and salt cannot be empty")


class User:
    """Entity representing an active student user during a session."""

    def __init__(
        self,
        email: InstitutionalEmail,
        session_id: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self._email = email
        self._session_id = session_id or uuid.uuid4().hex
        self._created_at = created_at or datetime.now(timezone.utc)

    @property
    def email(self) -> InstitutionalEmail:
        return self._email

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def __repr__(self) -> str:
        return f"User(email={self._email.value!r}, session_id={self._session_id!r})"

