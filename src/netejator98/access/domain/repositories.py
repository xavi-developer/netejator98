"""Repository and hasher interfaces (ports) for the Access context."""

from __future__ import annotations

from typing import Optional, Protocol, Tuple

from netejator98.access.domain.user import LastUserRecord
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Result


class LastUserRepositoryPort(Protocol):
    """Port for persisting machine-scoped last user records."""

    def get_last_user(self) -> Optional[LastUserRecord]:
        """Retrieve the last user record, or None if no prior user recorded."""
        ...

    def save_last_user(self, record: LastUserRecord) -> Result[None, DomainError]:
        """Persist a new last user record."""
        ...


class AdminCredentialRepositoryPort(Protocol):
    """Port for persisting administrator authentication verifiers."""

    def get_verifier(self) -> Optional[str]:
        """Retrieve the stored password verifier hash, or None if not set."""
        ...

    def save_verifier(self, verifier: str, salt: str) -> Result[None, DomainError]:
        """Persist a new password verifier."""
        ...

    def has_password(self) -> bool:
        """Check if an administrator password has been initialized."""
        ...


class PasswordHasherPort(Protocol):
    """Port for hashing and verifying passwords using Argon2id."""

    def hash_password(self, password: str) -> Tuple[str, str]:
        """Return (verifier_hash, salt)."""
        ...

    def verify_password(self, password: str, verifier: str) -> bool:
        """Verify password against stored verifier."""
        ...

