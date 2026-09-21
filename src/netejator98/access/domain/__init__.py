"""Access domain models, value objects, events, and repository interfaces."""

from netejator98.access.domain.admin import AdminCredential, AdminSession
from netejator98.access.domain.detector import (
    UserChangeDecision,
    UserChangeDetector,
    UserChangeType,
)
from netejator98.access.domain.email import InstitutionalEmail
from netejator98.access.domain.events import (
    AdminAuthenticated,
    AdminAuthenticationFailed,
    AdminPasswordChanged,
    DifferentUserDetected,
    SameUserDetected,
    UserIdentified,
)
from netejator98.access.domain.policy import DomainPolicy
from netejator98.access.domain.repositories import (
    AdminCredentialRepositoryPort,
    LastUserRepositoryPort,
    PasswordHasherPort,
)
from netejator98.access.domain.user import LastUserRecord, User

__all__ = [
    "InstitutionalEmail",
    "DomainPolicy",
    "User",
    "LastUserRecord",
    "AdminCredential",
    "AdminSession",
    "UserChangeDecision",
    "UserChangeType",
    "UserChangeDetector",
    "UserIdentified",
    "DifferentUserDetected",
    "SameUserDetected",
    "AdminAuthenticated",
    "AdminAuthenticationFailed",
    "AdminPasswordChanged",
    "LastUserRepositoryPort",
    "AdminCredentialRepositoryPort",
    "PasswordHasherPort",
]

