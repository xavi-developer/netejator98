"""HashChain domain service verifying cryptographic continuity across ciphertexts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from netejator98.audit.domain.sealed_entry import GENESIS_PREV_HASH, SealedEntry


@dataclass(frozen=True)
class ChainVerificationResult:
    """Outcome of unauthenticated audit log hash-chain verification."""

    is_valid: bool
    total_entries: int
    tampered_seq: Optional[int] = None
    failure_reason: Optional[str] = None


class HashChain:
    """Domain service enforcing and verifying cryptographic hash chain invariants."""

    @classmethod
    def verify_chain(cls, entries: Sequence[SealedEntry]) -> ChainVerificationResult:
        """Verify the integrity of an ordered sequence of sealed entries without decrypting."""
        if not entries:
            return ChainVerificationResult(is_valid=True, total_entries=0)

        expected_prev = GENESIS_PREV_HASH
        expected_seq = 1

        for i, entry in enumerate(entries):
            # 1. Verify sequence order
            if entry.seq != expected_seq:
                return ChainVerificationResult(
                    is_valid=False,
                    total_entries=len(entries),
                    tampered_seq=entry.seq,
                    failure_reason=(
                        f"Sequence break at index {i}: expected sequence {expected_seq}, got {entry.seq}"
                    ),
                )

            # 2. Verify previous hash continuity
            if entry.prev_hash != expected_prev:
                return ChainVerificationResult(
                    is_valid=False,
                    total_entries=len(entries),
                    tampered_seq=entry.seq,
                    failure_reason=(
                        f"Hash chain broken at seq {entry.seq}: expected prev_hash {expected_prev}, got {entry.prev_hash}"
                    ),
                )

            # 3. Verify internal entry hash over ciphertext
            calculated_hash = SealedEntry.calculate_hash(
                entry.seq, entry.prev_hash, entry.sealed
            )
            if entry.entry_hash != calculated_hash:
                return ChainVerificationResult(
                    is_valid=False,
                    total_entries=len(entries),
                    tampered_seq=entry.seq,
                    failure_reason=(
                        f"Corrupted entry hash at seq {entry.seq}: expected {calculated_hash}, got {entry.entry_hash}"
                    ),
                )

            expected_prev = entry.entry_hash
            expected_seq += 1

        return ChainVerificationResult(is_valid=True, total_entries=len(entries))

