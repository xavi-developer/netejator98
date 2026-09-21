"""AuthenticateAdminUseCase with rate limiting and exponential backoff."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
from typing import Optional

from netejator98.access.domain.admin import AdminCredential, AdminSession
from netejator98.access.domain.events import (
    AdminAuthenticated,
    AdminAuthenticationFailed,
)
from netejator98.access.domain.repositories import (
    AdminCredentialRepositoryPort,
    PasswordHasherPort,
)
from netejator98.shared.clock import ClockPort, SystemClock
from netejator98.shared.errors import (
    AccessError,
    AdminAuthenticationError,
    RateLimitExceededError,
)
from netejator98.shared.event_bus import EventBus
from netejator98.shared.result import Err, Ok, Result


class AuthenticateAdminUseCase:
    """Authenticates administrator credentials with rate limiting and exponential backoff."""

    def __init__(
        self,
        credential_repo: AdminCredentialRepositoryPort,
        hasher: PasswordHasherPort,
        event_bus: EventBus,
        clock: Optional[ClockPort] = None,
        max_free_attempts: int = 3,
        base_backoff_seconds: float = 2.0,
    ) -> None:
        self._repo = credential_repo
        self._hasher = hasher
        self._event_bus = event_bus
        self._clock = clock or SystemClock()
        self._max_free_attempts = max_free_attempts
        self._base_backoff_seconds = base_backoff_seconds

        self._consecutive_failures = 0
        self._locked_until: Optional[datetime] = None

    def execute(
        self, credential: AdminCredential
    ) -> Result[AdminSession, AccessError]:
        now = self._clock.now_utc()

        # Check rate limit backoff
        if self._locked_until is not None and now < self._locked_until:
            wait_seconds = int((self._locked_until - now).total_seconds()) + 1
            return Err(
                RateLimitExceededError(
                    f"Too many failed attempts. Please wait {wait_seconds} seconds.",
                    details=str(wait_seconds),
                )
            )

        verifier = self._repo.get_verifier()
        if verifier is None:
            # First-run state: no password set yet
            return Err(
                AdminAuthenticationError(
                    "Administrator password has not been initialized. Initial setup required."
                )
            )

        # Verify password against verifier
        is_valid = self._hasher.verify_password(credential.password, verifier)

        if not is_valid:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_free_attempts:
                backoff_exp = self._consecutive_failures - self._max_free_attempts
                delay = self._base_backoff_seconds * math.pow(2, min(backoff_exp, 6))
                self._locked_until = now + timedelta(seconds=delay)

            self._event_bus.publish(
                AdminAuthenticationFailed(
                    reason="Invalid password",
                    timestamp=now,
                )
            )
            return Err(AdminAuthenticationError("Invalid administrator password."))

        # Success: reset backoff and create session
        self._consecutive_failures = 0
        self._locked_until = None
        session = AdminSession.create(ttl_minutes=15, current_time=now)
        self._event_bus.publish(
            AdminAuthenticated(session_id=session.session_id, timestamp=now)
        )
        return Ok(session)

    def initialize_first_password(
        self, new_credential: AdminCredential
    ) -> Result[AdminSession, AccessError]:
        """Allow setting the initial admin password if none exists."""
        now = self._clock.now_utc()
        if self._repo.has_password():
            return Err(AdminAuthenticationError("Password is already initialized"))

        try:
            new_credential.validate_strength(min_length=8)
        except ValueError as e:
            return Err(AdminAuthenticationError(str(e)))

        verifier, salt = self._hasher.hash_password(new_credential.password)
        save_res = self._repo.save_verifier(verifier, salt)
        if save_res.is_err():
            return Err(AccessError(save_res.unwrap_err().message))

        session = AdminSession.create(ttl_minutes=15, current_time=now)
        self._event_bus.publish(
            AdminAuthenticated(session_id=session.session_id, timestamp=now)
        )
        return Ok(session)

