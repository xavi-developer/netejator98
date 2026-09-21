"""ChangeAdminPasswordUseCase for authorized password updates."""

from __future__ import annotations

from typing import Optional

from netejator98.access.domain.admin import AdminCredential, AdminSession
from netejator98.access.domain.events import AdminPasswordChanged
from netejator98.access.domain.repositories import (
    AdminCredentialRepositoryPort,
    PasswordHasherPort,
)
from netejator98.shared.clock import ClockPort, SystemClock
from netejator98.shared.errors import AccessError, AdminAuthenticationError
from netejator98.shared.event_bus import EventBus
from netejator98.shared.result import Err, Ok, Result


class ChangeAdminPasswordUseCase:
    """Changes the administrator password, requiring an active AdminSession."""

    def __init__(
        self,
        credential_repo: AdminCredentialRepositoryPort,
        hasher: PasswordHasherPort,
        event_bus: EventBus,
        clock: Optional[ClockPort] = None,
    ) -> None:
        self._repo = credential_repo
        self._hasher = hasher
        self._event_bus = event_bus
        self._clock = clock or SystemClock()

    def execute(
        self, session: AdminSession, new_credential: AdminCredential
    ) -> Result[None, AccessError]:
        now = self._clock.now_utc()

        if not session.is_valid(now):
            return Err(AdminAuthenticationError("Administrator session has expired"))

        try:
            new_credential.validate_strength(min_length=8)
        except ValueError as e:
            return Err(AdminAuthenticationError(str(e)))

        verifier, salt = self._hasher.hash_password(new_credential.password)
        save_res = self._repo.save_verifier(verifier, salt)
        if save_res.is_err():
            return Err(AccessError(save_res.unwrap_err().message))

        self._event_bus.publish(AdminPasswordChanged(timestamp=now))
        return Ok(None)

