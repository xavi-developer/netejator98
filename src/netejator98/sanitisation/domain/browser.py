"""BrowserProfile and browser types for the sanitisation domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class BrowserType(str, Enum):
    """Supported web browser families."""

    CHROME = "CHROME"
    CHROMIUM = "CHROMIUM"
    EDGE = "EDGE"
    FIREFOX = "FIREFOX"
    BRAVE = "BRAVE"
    OPERA = "OPERA"
    SAFARI = "SAFARI"


class BrowserVariant(str, Enum):
    """Packaging and installation variants for browsers."""

    NATIVE = "NATIVE"
    SNAP = "SNAP"
    FLATPAK = "FLATPAK"
    PORTABLE = "PORTABLE"


@dataclass(frozen=True)
class BrowserProfile:
    """Represents a discovered or declared browser profile on disk."""

    browser_type: BrowserType
    variant: BrowserVariant
    profile_path: str
    target_subpaths: List[str] = field(
        default_factory=lambda: [
            "Default/History",
            "Default/Cookies",
            "Default/Login Data",
            "Default/Web Data",
            "Default/Network",
            "Default/Sessions",
            "Default/Cache",
            "Default/Code Cache",
            "Default/GPUCache",
            "Default/Extensions",
            # Firefox profile targets
            "places.sqlite",
            "cookies.sqlite",
            "logins.json",
            "key4.db",
            "formhistory.sqlite",
            "sessionstore.jsonlz4",
            "storage",
            "cache2",
        ]
    )

