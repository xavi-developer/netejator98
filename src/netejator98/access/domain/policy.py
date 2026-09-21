"""Domain policy value object specifying allowed institutional email domain."""

from __future__ import annotations

from dataclasses import dataclass
import re

DOMAIN_REGEX = re.compile(r"^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,}$")


@dataclass(frozen=True)
class DomainPolicy:
    """Operational policy defining the authorized institutional domain."""

    allowed_domain: str

    def __post_init__(self) -> None:
        cleaned = self.allowed_domain.strip().lower()
        if cleaned.startswith("@"):
            cleaned = cleaned[1:]

        if not cleaned:
            raise ValueError("Allowed domain cannot be empty")

        if not DOMAIN_REGEX.match(cleaned):
            raise ValueError(f"Invalid domain format: {cleaned}")

        object.__setattr__(self, "allowed_domain", cleaned)

    def is_allowed(self, domain: str) -> bool:
        """Check if a domain matches the allowed institutional domain."""
        return domain.strip().lower() == self.allowed_domain

