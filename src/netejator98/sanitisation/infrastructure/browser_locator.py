"""BrowserProfileLocator discovering browser profile installations across platforms."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from netejator98.sanitisation.domain.browser import (
    BrowserProfile,
    BrowserType,
    BrowserVariant,
)


class BrowserProfileLocator:
    """Discovers web browser installations and profiles on Windows, Linux, and macOS."""

    @classmethod
    def locate_all(cls, user_home: str) -> List[BrowserProfile]:
        profiles: List[BrowserProfile] = []
        home = Path(user_home)

        # Linux Native / XDG
        linux_defs = [
            (BrowserType.CHROME, BrowserVariant.NATIVE, home / ".config/google-chrome"),
            (BrowserType.CHROMIUM, BrowserVariant.NATIVE, home / ".config/chromium"),
            (BrowserType.EDGE, BrowserVariant.NATIVE, home / ".config/microsoft-edge"),
            (BrowserType.FIREFOX, BrowserVariant.NATIVE, home / ".mozilla/firefox"),
            (BrowserType.BRAVE, BrowserVariant.NATIVE, home / ".config/BraveSoftware/Brave-Browser"),
            (BrowserType.OPERA, BrowserVariant.NATIVE, home / ".config/opera"),
        ]

        # Linux Snap packages
        snap_defs = [
            (BrowserType.CHROMIUM, BrowserVariant.SNAP, home / "snap/chromium/current"),
            (BrowserType.FIREFOX, BrowserVariant.SNAP, home / "snap/firefox/common/.mozilla/firefox"),
            (BrowserType.BRAVE, BrowserVariant.SNAP, home / "snap/brave/current/.config/BraveSoftware/Brave-Browser"),
            (BrowserType.OPERA, BrowserVariant.SNAP, home / "snap/opera/current/.config/opera"),
        ]

        # Linux Flatpak packages
        flatpak_defs = [
            (BrowserType.CHROME, BrowserVariant.FLATPAK, home / ".var/app/com.google.Chrome/config/google-chrome"),
            (BrowserType.CHROMIUM, BrowserVariant.FLATPAK, home / ".var/app/org.chromium.Chromium/config/chromium"),
            (BrowserType.FIREFOX, BrowserVariant.FLATPAK, home / ".var/app/org.mozilla.firefox/.mozilla/firefox"),
            (BrowserType.BRAVE, BrowserVariant.FLATPAK, home / ".var/app/com.brave.Browser/config/BraveSoftware/Brave-Browser"),
            (BrowserType.EDGE, BrowserVariant.FLATPAK, home / ".var/app/com.microsoft.Edge/config/microsoft-edge"),
        ]

        # Windows AppData / LocalAppData paths
        win_local = home / "AppData/Local"
        win_roaming = home / "AppData/Roaming"
        win_defs = [
            (BrowserType.CHROME, BrowserVariant.NATIVE, win_local / "Google/Chrome/User Data"),
            (BrowserType.EDGE, BrowserVariant.NATIVE, win_local / "Microsoft/Edge/User Data"),
            (BrowserType.BRAVE, BrowserVariant.NATIVE, win_local / "BraveSoftware/Brave-Browser/User Data"),
            (BrowserType.OPERA, BrowserVariant.NATIVE, win_roaming / "Opera Software/Opera Stable"),
            (BrowserType.FIREFOX, BrowserVariant.NATIVE, win_roaming / "Mozilla/Firefox/Profiles"),
        ]

        # macOS Application Support paths
        mac_support = home / "Library/Application Support"
        mac_defs = [
            (BrowserType.CHROME, BrowserVariant.NATIVE, mac_support / "Google/Chrome"),
            (BrowserType.FIREFOX, BrowserVariant.NATIVE, mac_support / "Firefox/Profiles"),
            (BrowserType.EDGE, BrowserVariant.NATIVE, mac_support / "Microsoft Edge"),
            (BrowserType.BRAVE, BrowserVariant.NATIVE, mac_support / "BraveSoftware/Brave-Browser"),
            (BrowserType.SAFARI, BrowserVariant.NATIVE, home / "Library/Safari"),
        ]

        all_candidates = linux_defs + snap_defs + flatpak_defs + win_defs + mac_defs

        for b_type, b_var, path in all_candidates:
            if path.exists():
                profiles.append(
                    BrowserProfile(
                        browser_type=b_type,
                        variant=b_var,
                        profile_path=str(path),
                    )
                )

        return profiles

