"""InstitutionalEmail value object."""

from __future__ import annotations

from dataclasses import dataclass
import re

from netejator98.access.domain.policy import DomainPolicy

EMAIL_REGEX = re.compile(r"^[a-z0-9]+([._%+-][a-z0-9]+)*@[a-z0-9]+([.-][a-z0-9]+)*\.[a-z]{2,}$")


@dataclass(frozen=True)
class InstitutionalEmail:
    """Immutable, validated institutional email address belonging to an authorized domain."""

    value: str
    local_part: str
    domain: str

    def __init__(self, raw_email: str, policy: DomainPolicy | None = None) -> None:
        if policy is None:
            policy = DomainPolicy("insestatut.cat")

        cleaned = raw_email.strip().lower()
        if not cleaned or "@" not in cleaned:
            raise ValueError(f"Malformed email address: {raw_email!r}")

        parts = cleaned.split("@", 1)
        local_part = parts[0]
        domain = parts[1]

        if not EMAIL_REGEX.match(cleaned):
            raise ValueError(f"Invalid email syntax: {cleaned!r}")

        if not policy.is_allowed(domain):
            raise ValueError(
                f"Email domain '@{domain}' does not match institutional domain '@{policy.allowed_domain}'"
            )

        object.__setattr__(self, "value", cleaned)
        object.__setattr__(self, "local_part", local_part)
        object.__setattr__(self, "domain", domain)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"InstitutionalEmail({self.value!r})"

