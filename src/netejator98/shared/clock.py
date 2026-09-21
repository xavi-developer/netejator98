"""Clock port and implementations for deterministic time handling in domain logic."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol


class ClockPort(Protocol):
    """Port for retrieving current time in UTC."""

    def now_utc(self) -> datetime:
        """Return the current UTC datetime."""
        ...


class SystemClock:
    """Production clock implementation returning real UTC system time."""

    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)


class FrozenClock:
    """Test double clock with deterministic frozen time."""

    def __init__(self, fixed_time: datetime | None = None) -> None:
        self._time = fixed_time or datetime.now(timezone.utc)

    def now_utc(self) -> datetime:
        return self._time

    def set_time(self, new_time: datetime) -> None:
        self._time = new_time

    def advance_seconds(self, seconds: float) -> None:
        from datetime import timedelta
        self._time += timedelta(seconds=seconds)

