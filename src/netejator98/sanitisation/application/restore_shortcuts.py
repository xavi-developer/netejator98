"""RestoreGoldenShortcutsUseCase recreating cross-platform desktop shortcuts."""

from __future__ import annotations

import os
import plistlib
import re
import sys
from typing import Any, Dict, List, Optional

from netejator98.sanitisation.application.ports import (
    FileSystemPort,
    PlatformPathsPort,
)
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Err, Ok, Result


class RestoreGoldenShortcutsUseCase:
    """Creates desktop web shortcuts matching target OS specifications."""

    def __init__(
        self,
        fs: FileSystemPort,
        paths: PlatformPathsPort,
        platform_name: Optional[str] = None,
    ) -> None:
        self._fs = fs
        self._paths = paths
        self._platform_name = self._resolve_platform(paths, platform_name)

    @staticmethod
    def _resolve_platform(paths: PlatformPathsPort, platform_name: Optional[str]) -> str:
        if platform_name:
            p = platform_name.strip().lower()
            if p in ("win32", "windows", "win"):
                return "windows"
            if p in ("darwin", "macos", "mac", "osx"):
                return "darwin"
            return "linux"

        cls_name = paths.__class__.__name__.lower()
        if "windows" in cls_name:
            return "windows"
        if "mac" in cls_name:
            return "darwin"
        if "linux" in cls_name:
            return "linux"

        sys_plat = sys.platform.lower()
        if sys_plat.startswith("win"):
            return "windows"
        if sys_plat == "darwin":
            return "darwin"
        return "linux"

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        # Replace characters illegal in Windows/Linux/macOS filenames
        cleaned = re.sub(r'[\\/*?:"<>|]', "_", name)
        # Strip trailing dots, whitespace, and leading/trailing dashes/underscores
        cleaned = cleaned.strip(". \t\r\n")
        return cleaned or "shortcut"

    @staticmethod
    def _normalize_url(url: str) -> str:
        cleaned = url.strip()
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9+-.]*://", cleaned):
            return f"https://{cleaned}"
        return cleaned

    def _generate_file_data(self, name: str, url: str) -> tuple[str, str]:
        """Returns (filename, file_content) based on the target platform."""
        safe_name = self._sanitize_filename(name)
        norm_url = self._normalize_url(url)

        if self._platform_name == "windows":
            filename = f"{safe_name}.url"
            content = f"[InternetShortcut]\r\nURL={norm_url}\r\n"
            return filename, content
        elif self._platform_name == "darwin":
            filename = f"{safe_name}.webloc"
            content = plistlib.dumps({"URL": norm_url}, fmt=plistlib.FMT_XML).decode("utf-8")
            return filename, content
        else:
            # Linux FreeDesktop specification (.desktop Link)
            filename = f"{safe_name}.desktop"
            content = (
                "[Desktop Entry]\n"
                "Version=1.0\n"
                "Type=Link\n"
                f"Name={name.strip()}\n"
                f"URL={norm_url}\n"
                "Icon=web-browser\n"
            )
            return filename, content

    def execute(self, shortcuts: List[Dict[str, Any]]) -> Result[List[str], DomainError]:
        """Creates desktop shortcuts for all valid items in shortcuts."""
        if not shortcuts:
            return Ok([])

        desktop_dir = self._paths.get_desktop_dir()
        created_paths: List[str] = []

        for item in shortcuts:
            name = str(item.get("name", "")).strip()
            url = str(item.get("url", "")).strip()
            if not name or not url:
                continue

            filename, content = self._generate_file_data(name, url)
            target_path = os.path.join(desktop_dir, filename)

            write_res = self._fs.write_text_file(target_path, content)
            if write_res.is_err():
                return Err(write_res.unwrap_err())

            created_paths.append(target_path)

        return Ok(created_paths)

