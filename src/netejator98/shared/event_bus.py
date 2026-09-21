"""In-process typed domain event bus for cross-context communication."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Type, TypeVar


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all immutable domain events."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


E = TypeVar("E", bound=DomainEvent)
EventHandler = Callable[[Any], None]


class EventBus:
    """Synchronous in-process event bus dispatching typed domain events."""

    def __init__(self) -> None:
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = defaultdict(list)
        self._recorded_events: List[DomainEvent] = []

    def subscribe(self, event_cls: Type[E], handler: Callable[[E], None]) -> None:
        """Register a handler callback for an event class."""
        self._handlers[event_cls].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all subscribed handlers and record it."""
        self._recorded_events.append(event)
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            handler(event)

    @property
    def recorded_events(self) -> List[DomainEvent]:
        """Return the list of published events (useful in tests)."""
        return list(self._recorded_events)

    def clear_recorded(self) -> None:
        """Clear recorded events history."""
        self._recorded_events.clear()

