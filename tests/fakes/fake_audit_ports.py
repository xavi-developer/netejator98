"""In-memory test doubles for Audit repository and cryptographic ports."""

from __future__ import annotations

import base64
from typing import List, Optional

from netejator98.audit.domain.ports import (
    AuditLogRepositoryPort,
    EntryOpenerPort,
    EntrySealerPort,
)
from netejator98.audit.domain.sealed_entry import SealedEntry
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Ok, Result


class FakeAuditLogRepository(AuditLogRepositoryPort):
    """In-memory audit log repository storing sealed entries."""

    def __init__(self, initial_entries: Optional[List[SealedEntry]] = None) -> None:
        self.entries: List[SealedEntry] = list(initial_entries or [])

    def append_entry(self, entry: SealedEntry) -> Result[None, DomainError]:
        self.entries.append(entry)
        return Ok(None)

    def get_last_entry(self) -> Optional[SealedEntry]:
        return self.entries[-1] if self.entries else None

    def get_all_entries(self) -> List[SealedEntry]:
        return list(self.entries)

    def count(self) -> int:
        return len(self.entries)


class FakeSimpleSealer(EntrySealerPort):
    """Deterministic in-memory sealer encoding to base64."""

    def seal(self, plaintext: bytes) -> Result[str, DomainError]:
        b64 = base64.b64encode(b"FAKE_SEALED:" + plaintext).decode("ascii")
        return Ok(b64)


class FakeSimpleOpener(EntryOpenerPort):
    """Deterministic in-memory opener decoding fake sealed base64."""

    def open(self, sealed_base64: str) -> Result[bytes, DomainError]:
        raw = base64.b64decode(sealed_base64.encode("ascii"))
        prefix = b"FAKE_SEALED:"
        if raw.startswith(prefix):
            return Ok(raw[len(prefix):])
        return Ok(raw)

