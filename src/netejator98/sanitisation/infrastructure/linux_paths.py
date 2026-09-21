"""LinuxPathsAdapter implementing PlatformPathsPort for Linux workstations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple

from netejator98.sanitisation.application.ports import PlatformPathsPort
from netejator98.sanitisation.domain.protected_path import ProtectedPathRule
from netejator98.sanitisation.infrastructure.browser_locator import (
    BrowserProfileLocator,
)


class LinuxPathsAdapter(PlatformPathsPort):
    """Platform paths resolver for Linux systems respecting XDG specifications."""

    def __init__(self, user_home: str | None = None) -> None:
        self._home = Path(user_home or os.path.expanduser("~")).resolve()

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
        return [
            str(self._home / ".cache"),
            "/tmp",
            "/var/tmp",
        ]

    def get_recent_files_paths(self) -> List[str]:
        return [
            str(self._home / ".local/share/recently-used.xbel"),
        ]

    def get_trash_paths(self) -> List[str]:
        return [
            str(self._home / ".local/share/Trash"),
        ]

    def get_browser_paths(self) -> List[Tuple[str, str, str]]:
        profiles = BrowserProfileLocator.locate_all(str(self._home))
        return [(p.browser_type.value, p.variant.value, p.profile_path) for p in profiles]

    def get_credential_paths(self) -> List[str]:
        return [
            str(self._home / ".ssh"),
            str(self._home / ".aws"),
            str(self._home / ".config/gh"),
            str(self._home / ".git-credentials"),
            str(self._home / ".config/git/credentials"),
        ]

    def get_shell_history_paths(self) -> List[str]:
        return [
            str(self._home / ".bash_history"),
            str(self._home / ".zsh_history"),
            str(self._home / ".python_history"),
        ]

    def get_cloud_sync_paths(self) -> List[str]:
        return [
            str(self._home / "Dropbox"),
            str(self._home / "Google Drive"),
            str(self._home / "OneDrive"),
        ]

    def get_system_protected_rules(self) -> List[ProtectedPathRule]:
        return ProtectedPathRule.get_default_system_rules()

