"""AuditTrail aggregate root managing hash chain continuity and monotonic ordering."""

from __future__ import annotations

from typing import Optional

from netejator98.audit.domain.sealed_entry import GENESIS_PREV_HASH, SealedEntry


class AuditTrail:
    """Aggregate root governing append-only audit trail invariants."""

    def __init__(self, last_entry: Optional[SealedEntry] = None) -> None:
        if last_entry is not None:
            self._current_seq = last_entry.seq
            self._last_hash = last_entry.entry_hash
        else:
            self._current_seq = 0
            self._last_hash = GENESIS_PREV_HASH

    @property
    def current_seq(self) -> int:
        return self._current_seq

    @property
    def last_hash(self) -> str:
        return self._last_hash

    def prepare_next_entry(self, sealed_base64: str) -> SealedEntry:
        """Create the next SealedEntry in the chain, incrementing sequence and chaining hash."""
        next_seq = self._current_seq + 1
        entry = SealedEntry.create(
            seq=next_seq,
            prev_hash=self._last_hash,
            sealed_base64=sealed_base64,
        )
        self._current_seq = next_seq
        self._last_hash = entry.entry_hash
        return entry

