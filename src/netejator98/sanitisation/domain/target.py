"""CleaningTarget and TargetCategory in the sanitisation domain."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from netejator98.sanitisation.domain.path_pattern import PathPattern
from netejator98.sanitisation.domain.strategy import DeletionStrategy


class TargetCategory(str, Enum):
    """Categorization of sanitisation surfaces."""

    USER_DOCUMENTS = "USER_DOCUMENTS"
    DESKTOP_SHORTCUTS = "DESKTOP_SHORTCUTS"
    RECYCLE_BIN = "RECYCLE_BIN"
    TEMP_AND_CACHE = "TEMP_AND_CACHE"
    BROWSER_PROFILES = "BROWSER_PROFILES"
    RECENT_FILES = "RECENT_FILES"
    CREDENTIALS = "CREDENTIALS"
    CLOUD_SYNC = "CLOUD_SYNC"
    SHELL_HISTORY = "SHELL_HISTORY"
    GOLDEN_PROFILE = "GOLDEN_PROFILE"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True)
class CleaningTarget:
    """A declared target category containing path patterns and a deletion strategy."""

    name: str
    category: TargetCategory
    patterns: Tuple[PathPattern, ...]
    strategy: DeletionStrategy = DeletionStrategy.STANDARD
    description: str = ""
    enabled: bool = True
    os: str = "ALL"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("CleaningTarget name cannot be empty")
        if not self.patterns:
            raise ValueError(f"CleaningTarget {self.name!r} must define at least one PathPattern")

    def applies_to_os(self, current_os: str) -> bool:
        """Check if target applies to given OS platform name."""
        if not self.os or self.os.upper() in ("ALL", "TOTS", "*"):
            return True
        c = current_os.strip().lower()
        t_os = self.os.strip().lower()
        if t_os in ("mac", "macos", "darwin", "osx"):
            return c in ("mac", "macos", "darwin", "osx")
        if t_os in ("win", "windows", "win32"):
            return c in ("win", "windows", "win32")
        if t_os in ("linux", "unix"):
            return c in ("linux", "unix")
        return t_os == c

