"""ExportAuditLogUseCase structurally requiring an authenticated AdminSession to export decrypted entries."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from netejator98.access.domain.admin import AdminSession
from netejator98.audit.application.query_log import QueryAuditLogUseCase
from netejator98.audit.domain.ports import AuditLogRepositoryPort, EntryOpenerPort
from netejator98.audit.infrastructure.csv_exporter import CsvExporter
from netejator98.shared.clock import ClockPort, SystemClock
from netejator98.shared.errors import AdminAuthenticationError, AuditError
from netejator98.shared.result import Err, Ok, Result


class ExportAuditLogUseCase:
    """Exports decrypted audit logs to a CSV file destination, strictly requiring AdminSession."""

    def __init__(
        self,
        repository: AuditLogRepositoryPort,
        opener: EntryOpenerPort,
        clock: Optional[ClockPort] = None,
    ) -> None:
        self._query_use_case = QueryAuditLogUseCase(repository, opener, clock)
        self._clock = clock or SystemClock()

    def execute(
        self,
        session: AdminSession,
        target_csv_path: str | Path,
    ) -> Result[None, AuditError]:
        now = self._clock.now_utc()
        if not session.is_valid(now):
            return Err(AdminAuthenticationError("AdminSession has expired or is invalid"))

        query_res = self._query_use_case.execute(session)
        if query_res.is_err():
            return Err(query_res.unwrap_err())

        entries = query_res.unwrap()
        export_res = CsvExporter.export_to_file(entries, target_csv_path)
        if export_res.is_err():
            return Err(AuditError(export_res.unwrap_err().message))

        return Ok(None)

