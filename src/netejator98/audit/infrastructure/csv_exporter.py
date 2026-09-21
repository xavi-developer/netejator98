"""CsvExporter for exporting decrypted audit records to CSV format."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from netejator98.audit.domain.entry import AuditEntry
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Err, Ok, Result


class CsvExporter:
    """Exports decrypted audit entries to a clean CSV file."""

    HEADERS = [
        "timestamp_utc",
        "machine_id",
        "hostname",
        "event_type",
        "email",
        "outcome",
        "targets_cleaned",
        "errors",
    ]

    @classmethod
    def export_to_file(
        cls, entries: List[AuditEntry], target_path: str | Path
    ) -> Result[None, DomainError]:
        path = Path(target_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(cls.HEADERS)
                for entry in entries:
                    writer.writerow(
                        [
                            entry.timestamp.isoformat(),
                            entry.machine_id,
                            entry.hostname,
                            entry.event_type,
                            entry.email or "",
                            entry.outcome,
                            ";".join(entry.targets_cleaned),
                            ";".join(entry.errors),
                        ]
                    )
            return Ok(None)
        except Exception as e:
            return Err(DomainError(f"Failed to export CSV audit log: {e}"))

