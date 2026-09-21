"""StartSessionUseCase orchestrating email validation and user change detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from netejator98.access.domain.detector import (
    UserChangeDecision,
    UserChangeDetector,
    UserChangeType,
)
from netejator98.access.domain.email import InstitutionalEmail
from netejator98.access.domain.events import (
    DifferentUserDetected,
    SameUserDetected,
    UserIdentified,
)
from netejator98.access.domain.policy import DomainPolicy
from netejator98.access.domain.repositories import LastUserRepositoryPort
from netejator98.access.domain.user import LastUserRecord, User
from netejator98.shared.clock import ClockPort, SystemClock
from netejator98.shared.errors import AccessError, InvalidEmailError
from netejator98.shared.event_bus import EventBus
from netejator98.shared.result import Err, Ok, Result


@dataclass(frozen=True)
class SessionStartResult:
    """Outcome of session initiation."""

    user: User
    decision: UserChangeDecision
    requires_sanitisation: bool


class StartSessionUseCase:
    """Evaluates student email entry and determines whether sanitisation is required."""

    def __init__(
        self,
        last_user_repo: LastUserRepositoryPort,
        event_bus: EventBus,
        detector: Optional[UserChangeDetector] = None,
        clock: Optional[ClockPort] = None,
    ) -> None:
        self._last_user_repo = last_user_repo
        self._event_bus = event_bus
        self._detector = detector or UserChangeDetector()
        self._clock = clock or SystemClock()

    def execute(
        self,
        raw_email: str,
        policy: Optional[DomainPolicy] = None,
        always_clean_on_boot: bool = False,
    ) -> Result[SessionStartResult, AccessError]:
        # 1. Validate institutional email
        try:
            email = InstitutionalEmail(raw_email, policy)
        except ValueError as e:
            return Err(InvalidEmailError(str(e)))

        now = self._clock.now_utc()
        user = User(email=email, created_at=now)

        # 2. Check last user record
        last_record = self._last_user_repo.get_last_user()
        decision = self._detector.evaluate(email, last_record)

        # 3. Determine sanitisation necessity
        requires_sanitisation = (
            decision.requires_sanitisation_by_identity or always_clean_on_boot
        )

        if decision.decision == UserChangeType.SAME_USER:
            self._event_bus.publish(
                SameUserDetected(email_hash=decision.new_hash, timestamp=now)
            )
        else:
            self._event_bus.publish(
                DifferentUserDetected(
                    previous_hash=decision.previous_hash,
                    new_hash=decision.new_hash,
                    timestamp=now,
                )
            )

        # If no sanitisation needed, record user immediately
        if not requires_sanitisation:
            self._last_user_repo.save_last_user(
                LastUserRecord(
                    email_hash=decision.new_hash,
                    salt=decision.salt_used,
                    recorded_at=now,
                )
            )
            self._event_bus.publish(UserIdentified(email=email.value, timestamp=now))

        return Ok(
            SessionStartResult(
                user=user,
                decision=decision,
                requires_sanitisation=requires_sanitisation,
            )
        )

    def commit_sanitised_user(
        self, user: User, decision: UserChangeDecision
    ) -> Result[None, AccessError]:
        """Commit new user to the last user repository after successful sanitisation."""
        now = self._clock.now_utc()
        record = LastUserRecord(
            email_hash=decision.new_hash,
            salt=decision.salt_used,
            recorded_at=now,
        )
        save_res = self._last_user_repo.save_last_user(record)
        if save_res.is_err():
            return Err(AccessError(save_res.unwrap_err().message))

        self._event_bus.publish(UserIdentified(email=user.email.value, timestamp=now))
        return Ok(None)

