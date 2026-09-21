"""Domain events for the Access bounded context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from netejator98.shared.event_bus import DomainEvent


@dataclass(frozen=True)
class UserIdentified(DomainEvent):
    """Fired when an institutional student user has been successfully identified."""

    email: str = ""


@dataclass(frozen=True)
class DifferentUserDetected(DomainEvent):
    """Fired when the current student differs from the last workstation user."""

    previous_hash: Optional[str] = None
    new_hash: str = ""


@dataclass(frozen=True)
class SameUserDetected(DomainEvent):
    """Fired when the current student is identical to the last recorded workstation user."""

    email_hash: str = ""


@dataclass(frozen=True)
class AdminAuthenticated(DomainEvent):
    """Fired when an administrator successfully authenticates."""

    session_id: str = ""


@dataclass(frozen=True)
class AdminAuthenticationFailed(DomainEvent):
    """Fired when an administrator authentication attempt fails."""

    reason: str = ""


@dataclass(frozen=True)
class AdminPasswordChanged(DomainEvent):
    """Fired when the administrator password is changed and keys re-wrapped."""

    pass

