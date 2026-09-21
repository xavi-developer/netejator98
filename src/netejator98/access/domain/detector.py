"""UserChangeDetector domain service and UserChangeDecision value object."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
from typing import Optional

from netejator98.access.domain.email import InstitutionalEmail
from netejator98.access.domain.user import LastUserRecord


class UserChangeType(str, Enum):
    """Classification of user identity comparison."""

    SAME_USER = "SAME_USER"
    DIFFERENT_USER = "DIFFERENT_USER"
    NO_PREVIOUS_USER = "NO_PREVIOUS_USER"


@dataclass(frozen=True)
class UserChangeDecision:
    """Decision object indicating whether the workstation user has changed."""

    decision: UserChangeType
    previous_hash: Optional[str]
    new_hash: str
    salt_used: str

    @property
    def requires_sanitisation_by_identity(self) -> bool:
        """True if the identity difference requires user profile sanitisation."""
        return self.decision in (UserChangeType.DIFFERENT_USER, UserChangeType.NO_PREVIOUS_USER)


class UserChangeDetector:
    """Domain service comparing entered identity against the machine-scoped last user record."""

    @staticmethod
    def compute_hash(email: InstitutionalEmail, salt: str) -> str:
        """Compute salted SHA-256 hash of an institutional email."""
        return hmac.new(
            salt.encode("utf-8"),
            email.value.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def evaluate(
        self,
        entered_email: InstitutionalEmail,
        last_record: Optional[LastUserRecord],
        new_salt_generator: Optional[callable] = None,
    ) -> UserChangeDecision:
        """Compare entered email against last user record and return a decision object."""
        if last_record is None:
            # First run or wiped record: generate salt for new user
            salt = new_salt_generator() if new_salt_generator else hashlib.sha256(entered_email.value.encode("utf-8")).hexdigest()[:16]
            new_hash = self.compute_hash(entered_email, salt)
            return UserChangeDecision(
                decision=UserChangeType.NO_PREVIOUS_USER,
                previous_hash=None,
                new_hash=new_hash,
                salt_used=salt,
            )

        # Hash entered email using the existing salt
        entered_hash = self.compute_hash(entered_email, last_record.salt)
        if hmac.compare_digest(entered_hash, last_record.email_hash):
            return UserChangeDecision(
                decision=UserChangeType.SAME_USER,
                previous_hash=last_record.email_hash,
                new_hash=entered_hash,
                salt_used=last_record.salt,
            )

        # Different user
        salt_for_new = new_salt_generator() if new_salt_generator else hashlib.sha256(entered_email.value.encode("utf-8")).hexdigest()[:16]
        new_hash = self.compute_hash(entered_email, salt_for_new)
        return UserChangeDecision(
            decision=UserChangeType.DIFFERENT_USER,
            previous_hash=last_record.email_hash,
            new_hash=new_hash,
            salt_used=salt_for_new,
        )

