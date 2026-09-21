"""RecordSanitisationUseCase for appending sanitisation outcomes to the sealed audit log."""

from __future__ import annotations

import platform
from typing import List, Optional

from netejator98.audit.domain.entry import AuditEntry
from netejator98.audit.domain.ports import AuditLogRepositoryPort, EntrySealerPort
from netejator98.audit.domain.trail import AuditTrail
from netejator98.shared.clock import ClockPort, SystemClock
from netejator98.shared.errors import AuditError
from netejator98.shared.machine_id import MachineId
from netejator98.shared.result import Err, Ok, Result


class RecordSanitisationUseCase:
    """Seals and appends sanitisation execution records to the tamper-evident audit trail."""

    def __init__(
        self,
        repository: AuditLogRepositoryPort,
        sealer: EntrySealerPort,
        machine_id: Optional[MachineId] = None,
        clock: Optional[ClockPort] = None,
    ) -> None:
        self._repo = repository
        self._sealer = sealer
        self._machine_id = machine_id or MachineId.current()
        self._clock = clock or SystemClock()
        self._hostname = platform.node() or "localhost"

    def execute(
        self,
        event_type: str,
        email: Optional[str],
        outcome: str,
        targets_cleaned: List[str],
        errors: List[str],
    ) -> Result[None, AuditError]:
        now = self._clock.now_utc()
        entry = AuditEntry(
            timestamp=now,
            machine_id=str(self._machine_id),
            hostname=self._hostname,
            event_type=event_type,
            email=email,
            outcome=outcome,
            targets_cleaned=targets_cleaned,
            errors=errors,
        )

        seal_res = self._sealer.seal(entry.to_json_bytes())
        if seal_res.is_err():
            return Err(AuditError(f"Failed to seal sanitisation entry: {seal_res.unwrap_err().message}"))

        sealed_b64 = seal_res.unwrap()
        last_entry = self._repo.get_last_entry()
        trail = AuditTrail(last_entry)
        next_sealed = trail.prepare_next_entry(sealed_b64)

        append_res = self._repo.append_entry(next_sealed)
        if append_res.is_err():
            return Err(AuditError(f"Failed to append to audit log: {append_res.unwrap_err().message}"))

        return Ok(None)

