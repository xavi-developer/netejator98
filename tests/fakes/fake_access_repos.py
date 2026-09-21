"""In-memory test doubles for Access repositories and hasher."""

from __future__ import annotations

import hashlib
from typing import Optional, Tuple

from netejator98.access.domain.repositories import (
    AdminCredentialRepositoryPort,
    LastUserRepositoryPort,
    PasswordHasherPort,
)
from netejator98.access.domain.user import LastUserRecord
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Ok, Result


class FakeLastUserRepository(LastUserRepositoryPort):
    """In-memory fake implementation of LastUserRepositoryPort."""

    def __init__(self, initial_record: Optional[LastUserRecord] = None) -> None:
        self.record: Optional[LastUserRecord] = initial_record
        self.save_count = 0

    def get_last_user(self) -> Optional[LastUserRecord]:
        return self.record

    def save_last_user(self, record: LastUserRecord) -> Result[None, DomainError]:
        self.record = record
        self.save_count += 1
        return Ok(None)


class FakeAdminCredentialRepository(AdminCredentialRepositoryPort):
    """In-memory fake implementation of AdminCredentialRepositoryPort."""

    def __init__(self, initial_verifier: Optional[str] = None) -> None:
        self.verifier: Optional[str] = initial_verifier
        self.salt: Optional[str] = "fake_salt" if initial_verifier else None

    def get_verifier(self) -> Optional[str]:
        return self.verifier

    def save_verifier(self, verifier: str, salt: str) -> Result[None, DomainError]:
        self.verifier = verifier
        self.salt = salt
        return Ok(None)

    def has_password(self) -> bool:
        return self.verifier is not None


class FakePasswordHasher(PasswordHasherPort):
    """Fast, deterministic in-memory password hasher for unit tests."""

    def hash_password(self, password: str) -> Tuple[str, str]:
        salt = "test_salt_123"
        verifier = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return verifier, salt

    def verify_password(self, password: str, verifier: str) -> bool:
        salt = "test_salt_123"
        expected = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return verifier == expected

