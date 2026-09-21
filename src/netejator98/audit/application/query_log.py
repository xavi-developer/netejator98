"""QueryAuditLogUseCase structurally requiring an authenticated AdminSession to decrypt entries."""

from __future__ import annotations

from typing import List, Optional

from netejator98.access.domain.admin import AdminSession
from netejator98.audit.domain.entry import AuditEntry
from netejator98.audit.domain.ports import AuditLogRepositoryPort, EntryOpenerPort
from netejator98.shared.clock import ClockPort, SystemClock
from netejator98.shared.errors import AdminAuthenticationError, AuditError
from netejator98.shared.result import Err, Ok, Result


class QueryAuditLogUseCase:
    """Decrypts and retrieves audit log records, strictly requiring an authenticated AdminSession."""

    def __init__(
        self,
        repository: AuditLogRepositoryPort,
        opener: EntryOpenerPort,
        clock: Optional[ClockPort] = None,
    ) -> None:
        self._repo = repository
        self._opener = opener
        self._clock = clock or SystemClock()

    def execute(
        self,
        session: AdminSession,
        limit: Optional[int] = None,
        email_filter: Optional[str] = None,
    ) -> Result[List[AuditEntry], AuditError]:
        # Structurally enforces that session cannot be None and must be valid
        now = self._clock.now_utc()
        if not session.is_valid(now):
            return Err(AdminAuthenticationError("AdminSession has expired or is invalid"))

        sealed_entries = self._repo.get_all_entries()
        decrypted_entries: List[AuditEntry] = []

        for sealed in sealed_entries:
            open_res = self._opener.open(sealed.sealed)
            if open_res.is_err():
                return Err(
                    AuditError(
                        f"Failed to decrypt entry seq {sealed.seq}: {open_res.unwrap_err().message}"
                    )
                )

            try:
                entry = AuditEntry.from_json_bytes(open_res.unwrap())
            except Exception as e:
                return Err(AuditError(f"Corrupted decrypted entry seq {sealed.seq}: {e}"))

            if email_filter and entry.email != email_filter:
                continue

            decrypted_entries.append(entry)

        if limit is not None and limit > 0:
            decrypted_entries = decrypted_entries[-limit:]

        return Ok(decrypted_entries)

