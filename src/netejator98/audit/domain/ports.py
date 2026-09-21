"""Ports (interfaces) for the Audit bounded context."""

from __future__ import annotations

from typing import List, Optional, Protocol

from netejator98.audit.domain.sealed_entry import SealedEntry
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Result


class EntrySealerPort(Protocol):
    """Port for encrypting audit entries using the public key alone."""

    def seal(self, plaintext: bytes) -> Result[str, DomainError]:
        """Seal plaintext bytes and return base64-encoded ciphertext."""
        ...


class EntryOpenerPort(Protocol):
    """Port for decrypting sealed entries using the unwrapped private key in memory."""

    def open(self, sealed_base64: str) -> Result[bytes, DomainError]:
        """Decrypt base64 ciphertext and return plaintext bytes."""
        ...


class KeyWrapperPort(Protocol):
    """Port for wrapping and unwrapping the X25519 private key using password-derived KEK."""

    def wrap_key(self, private_key_bytes: bytes, password: str) -> Result[bytes, DomainError]:
        """Wrap private key bytes using Argon2id derived key."""
        ...

    def unwrap_key(self, wrapped_blob: bytes, password: str) -> Result[bytes, DomainError]:
        """Unwrap private key bytes given the correct password."""
        ...

    def wrap_with_recovery_key(
        self, private_key_bytes: bytes, recovery_key: str
    ) -> Result[bytes, DomainError]:
        """Wrap private key using high-entropy recovery key."""
        ...

    def unwrap_with_recovery_key(
        self, wrapped_blob: bytes, recovery_key: str
    ) -> Result[bytes, DomainError]:
        """Unwrap private key using recovery key."""
        ...


class AuditLogRepositoryPort(Protocol):
    """Port for append-only storage and raw retrieval of sealed audit entries."""

    def append_entry(self, entry: SealedEntry) -> Result[None, DomainError]:
        """Append a validated sealed entry to disk."""
        ...

    def get_last_entry(self) -> Optional[SealedEntry]:
        """Retrieve the latest sealed entry, or None if the log is empty."""
        ...

    def get_all_entries(self) -> List[SealedEntry]:
        """Retrieve all sealed entries in chronological sequence."""
        ...

    def count(self) -> int:
        """Count total entries recorded."""
        ...

