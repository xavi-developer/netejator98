"""VerifyChainIntegrityUseCase for unauthenticated cryptographic hash chain verification."""

from __future__ import annotations

from netejator98.audit.domain.hash_chain import (
    ChainVerificationResult,
    HashChain,
)
from netejator98.audit.domain.ports import AuditLogRepositoryPort


class VerifyChainIntegrityUseCase:
    """Verifies the hash-chain integrity of the audit log completely unauthenticated."""

    def __init__(self, repository: AuditLogRepositoryPort) -> None:
        self._repo = repository

    def execute(self) -> ChainVerificationResult:
        try:
            entries = self._repo.get_all_entries()
        except Exception as e:
            return ChainVerificationResult(
                is_valid=False,
                total_entries=0,
                failure_reason=f"Log corruption: {e}",
            )
        return HashChain.verify_chain(entries)
