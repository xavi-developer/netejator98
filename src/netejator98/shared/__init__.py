"""Shared primitives, errors, result types, and event bus."""

from netejator98.shared.clock import ClockPort, FrozenClock, SystemClock
from netejator98.shared.errors import (
    AccessError,
    AdminAuthenticationError,
    AuditError,
    DeletionFailedError,
    DomainError,
    HashChainIntegrityError,
    InfrastructureError,
    InvalidDomainError,
    InvalidEmailError,
    InvalidPathPatternError,
    IPCCommunicationError,
    KeyUnwrapError,
    OpeningError,
    PolicyValidationError,
    ProtectedPathViolationError,
    RateLimitExceededError,
    SanitisationError,
    SealingError,
)
from netejator98.shared.event_bus import DomainEvent, EventBus
from netejator98.shared.machine_id import MachineId
from netejator98.shared.result import Err, Ok, Result

__all__ = [
    "Result",
    "Ok",
    "Err",
    "DomainError",
    "AccessError",
    "InvalidEmailError",
    "InvalidDomainError",
    "AdminAuthenticationError",
    "RateLimitExceededError",
    "SanitisationError",
    "ProtectedPathViolationError",
    "InvalidPathPatternError",
    "PolicyValidationError",
    "DeletionFailedError",
    "AuditError",
    "HashChainIntegrityError",
    "KeyUnwrapError",
    "SealingError",
    "OpeningError",
    "InfrastructureError",
    "IPCCommunicationError",
    "ClockPort",
    "SystemClock",
    "FrozenClock",
    "DomainEvent",
    "EventBus",
    "MachineId",
]

