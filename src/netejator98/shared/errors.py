"""Domain error hierarchy for Netejator98."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DomainError(Exception):
    """Base class for all domain errors."""

    message: str
    code: str = "DOMAIN_ERROR"
    details: Optional[str] = None

    def __str__(self) -> str:
        if self.details:
            return f"[{self.code}] {self.message} ({self.details})"
        return f"[{self.code}] {self.message}"


# Access bounded context errors
@dataclass(frozen=True)
class AccessError(DomainError):
    code: str = "ACCESS_ERROR"


@dataclass(frozen=True)
class InvalidEmailError(AccessError):
    code: str = "INVALID_EMAIL"


@dataclass(frozen=True)
class InvalidDomainError(AccessError):
    code: str = "INVALID_DOMAIN"


@dataclass(frozen=True)
class AdminAuthenticationError(AccessError):
    code: str = "ADMIN_AUTH_FAILED"


@dataclass(frozen=True)
class RateLimitExceededError(AccessError):
    code: str = "RATE_LIMIT_EXCEEDED"


# Sanitisation bounded context errors
@dataclass(frozen=True)
class SanitisationError(DomainError):
    code: str = "SANITISATION_ERROR"


@dataclass(frozen=True)
class ProtectedPathViolationError(SanitisationError):
    code: str = "PROTECTED_PATH_VIOLATION"


@dataclass(frozen=True)
class InvalidPathPatternError(SanitisationError):
    code: str = "INVALID_PATH_PATTERN"


@dataclass(frozen=True)
class PolicyValidationError(SanitisationError):
    code: str = "POLICY_VALIDATION_ERROR"


@dataclass(frozen=True)
class DeletionFailedError(SanitisationError):
    code: str = "DELETION_FAILED"


@dataclass(frozen=True)
class FileWriteError(SanitisationError):
    code: str = "FILE_WRITE_FAILED"


# Audit bounded context errors
@dataclass(frozen=True)
class AuditError(DomainError):
    code: str = "AUDIT_ERROR"


@dataclass(frozen=True)
class HashChainIntegrityError(AuditError):
    code: str = "HASH_CHAIN_INTEGRITY_BROKEN"


@dataclass(frozen=True)
class KeyUnwrapError(AuditError):
    code: str = "KEY_UNWRAP_FAILED"


@dataclass(frozen=True)
class SealingError(AuditError):
    code: str = "SEALING_FAILED"


@dataclass(frozen=True)
class OpeningError(AuditError):
    code: str = "OPENING_FAILED"


# Infrastructure / IPC errors
@dataclass(frozen=True)
class InfrastructureError(DomainError):
    code: str = "INFRASTRUCTURE_ERROR"


@dataclass(frozen=True)
class IPCCommunicationError(InfrastructureError):
    code: str = "IPC_COMMUNICATION_ERROR"

