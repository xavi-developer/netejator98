"""WindowsPathsAdapter implementing PlatformPathsPort for Windows 10+ workstations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple

from netejator98.sanitisation.application.ports import PlatformPathsPort
from netejator98.sanitisation.domain.protected_path import ProtectedPathRule
from netejator98.sanitisation.infrastructure.browser_locator import (
    BrowserProfileLocator,
)


class WindowsPathsAdapter(PlatformPathsPort):
    """Platform paths resolver for Windows systems."""

    def __init__(self, user_home: str | None = None) -> None:
        home_str = user_home or os.environ.get("USERPROFILE", os.path.expanduser("~"))
        self._home = Path(home_str).resolve()
        self._appdata = Path(os.environ.get("APPDATA", str(self._home / "AppData/Roaming")))
        self._localappdata = Path(
            os.environ.get("LOCALAPPDATA", str(self._home / "AppData/Local"))
        )

    def get_user_home(self) -> str:
        return str(self._home)

    def get_documents_dir(self) -> str:
        return str(self._home / "Documents")

    def get_downloads_dir(self) -> str:
        return str(self._home / "Downloads")

    def get_desktop_dir(self) -> str:
        return str(self._home / "Desktop")

    def get_pictures_dir(self) -> str:
        return str(self._home / "Pictures")

    def get_videos_dir(self) -> str:
        return str(self._home / "Videos")

    def get_music_dir(self) -> str:
        return str(self._home / "Music")

    def get_temp_dirs(self) -> List[str]:
        temp_env = os.environ.get("TEMP", str(self._localappdata / "Temp"))
        return [
            temp_env,
            str(self._localappdata / "Temp"),
            str(self._localappdata / "CrashDumps"),
        ]

    def get_recent_files_paths(self) -> List[str]:
        recent = self._appdata / "Microsoft/Windows/Recent"
        return [
            str(recent),
            str(recent / "AutomaticDestinations"),
            str(recent / "CustomDestinations"),
        ]

    def get_trash_paths(self) -> List[str]:
        return ["C:/$Recycle.Bin"]

    def get_browser_paths(self) -> List[Tuple[str, str, str]]:
        profiles = BrowserProfileLocator.locate_all(str(self._home))
        return [(p.browser_type.value, p.variant.value, p.profile_path) for p in profiles]

    def get_credential_paths(self) -> List[str]:
        return [
            str(self._home / ".ssh"),
            str(self._home / ".aws"),
            str(self._home / ".config/gh"),
            str(self._home / ".git-credentials"),
        ]

    def get_shell_history_paths(self) -> List[str]:
        return [
            str(
                self._appdata
                / "Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt"
            ),
        ]

    def get_cloud_sync_paths(self) -> List[str]:
        return [
            str(self._home / "OneDrive"),
            str(self._home / "Dropbox"),
            str(self._home / "Google Drive"),
        ]

    def get_system_protected_rules(self) -> List[ProtectedPathRule]:
        return ProtectedPathRule.get_default_system_rules()

