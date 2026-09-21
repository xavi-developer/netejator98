"""Domain events for the Sanitisation bounded context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from netejator98.sanitisation.domain.outcome import SanitisationOutcome
from netejator98.shared.event_bus import DomainEvent


@dataclass(frozen=True)
class SanitisationRequested(DomainEvent):
    """Fired when workstation profile sanitisation has been requested."""

    user_email: Optional[str] = None
    dry_run: bool = False


@dataclass(frozen=True)
class SanitisationCompleted(DomainEvent):
    """Fired when a sanitisation run has completed successfully."""

    outcome: Optional[SanitisationOutcome] = None


@dataclass(frozen=True)
class SanitisationFailed(DomainEvent):
    """Fired when a sanitisation run fails due to a fatal error."""

    reason: str = ""
    errors: Tuple[str, ...] = ()

