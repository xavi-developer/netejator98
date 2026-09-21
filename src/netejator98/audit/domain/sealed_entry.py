"""SealedEntry value object representing an on-disk encrypted audit record in the hash chain."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict

GENESIS_PREV_HASH = "0" * 64


@dataclass(frozen=True)
class SealedEntry:
    """An encrypted line in the audit log committing to the cryptographic hash chain."""

    seq: int
    sealed: str
    prev_hash: str
    entry_hash: str

    def __post_init__(self) -> None:
        if self.seq < 1:
            raise ValueError(f"Sequence number must be positive, got {self.seq}")
        if not self.sealed:
            raise ValueError("Sealed payload cannot be empty")
        if not self.prev_hash:
            raise ValueError("Previous hash cannot be empty")
        if not self.entry_hash:
            raise ValueError("Entry hash cannot be empty")

    def is_hash_valid(self) -> bool:
        """Check if entry_hash matches calculation over seq, prev_hash, and sealed."""
        return self.entry_hash == self.calculate_hash(self.seq, self.prev_hash, self.sealed)

    @staticmethod
    def calculate_hash(seq: int, prev_hash: str, sealed: str) -> str:
        """Compute entry hash over sequence, previous entry hash, and ciphertext."""
        data = f"{seq}:{prev_hash}:{sealed}".encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def create(cls, seq: int, prev_hash: str, sealed_base64: str) -> SealedEntry:
        """Factory creating a SealedEntry with automatically calculated entry hash."""
        entry_hash = cls.calculate_hash(seq, prev_hash, sealed_base64)
        return cls(
            seq=seq,
            sealed=sealed_base64,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )

    def to_json_str(self) -> str:
        """Serialize to a single JSON line on disk."""
        return json.dumps(
            {
                "seq": self.seq,
                "sealed": self.sealed,
                "prev_hash": self.prev_hash,
                "entry_hash": self.entry_hash,
            }
        )

    @classmethod
    def from_json_str(cls, line: str) -> SealedEntry:
        """Parse from a JSON line on disk."""
        data = json.loads(line)
        return cls(
            seq=data["seq"],
            sealed=data["sealed"],
            prev_hash=data["prev_hash"],
            entry_hash=data["entry_hash"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seq": self.seq,
            "sealed": self.sealed,
            "prev_hash": self.prev_hash,
            "entry_hash": self.entry_hash,
        }
