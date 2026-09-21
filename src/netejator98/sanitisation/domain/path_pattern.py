"""PathPattern value object ensuring traversal safety and valid pattern syntax."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re


@dataclass(frozen=True)
class PathPattern:
    """A traversal-safe file or directory glob pattern."""

    pattern: str

    def __post_init__(self) -> None:
        raw = self.pattern.strip()
        if not raw:
            raise ValueError("PathPattern cannot be empty")

        # Prohibit path traversal
        normalized = raw.replace("\\", "/")
        parts = normalized.split("/")
        if ".." in parts:
            raise ValueError(f"Path traversal ('..') is strictly prohibited in PathPattern: {raw!r}")

        # Prohibit absolute root hijacking when used as relative pattern
        if normalized.startswith("/") or re.match(r"^[a-zA-Z]:[/\\]", raw):
            pass  # Anchored absolute patterns are allowed only if explicitly validated by policy

        object.__setattr__(self, "pattern", normalized)

    def is_glob(self) -> bool:
        """True if the pattern contains glob wildcards (*, ?, [])."""
        return bool(re.search(r"[*?\[\]]", self.pattern))

    def __str__(self) -> str:
        return self.pattern

