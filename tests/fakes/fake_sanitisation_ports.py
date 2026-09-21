"""In-memory test doubles for Sanitisation ports."""

from __future__ import annotations

import fnmatch
from typing import Dict, List, Optional, Set, Tuple

from netejator98.sanitisation.application.ports import (
    CredentialStorePort,
    FileSystemPort,
    PlatformPathsPort,
    ProcessPort,
)
from netejator98.sanitisation.domain.protected_path import ProtectedPathRule
from netejator98.sanitisation.domain.target import TargetCategory
from netejator98.shared.errors import DeletionFailedError, DomainError
from netejator98.shared.result import Err, Ok, Result


class FakeFileSystemPort(FileSystemPort):
    """In-memory virtual filesystem for testing sanitisation without touching real disk."""

    def __init__(self) -> None:
        # path -> (is_dir: bool, size: int, is_locked: bool)
        self.files: Dict[str, Tuple[bool, int, bool]] = {}
        self.file_contents: Dict[str, str] = {}
        self.lock_attempts: Dict[str, int] = {}
        self.deleted_paths: List[str] = []

    def add_file(self, path: str, size: int = 1024, locked: bool = False) -> None:
        self.files[self._norm(path)] = (False, size, locked)

    def add_dir(self, path: str) -> None:
        self.files[self._norm(path)] = (True, 4096, False)

    @staticmethod
    def _norm(path: str) -> str:
        return path.replace("\\", "/").rstrip("/").lower()

    def exists(self, path: str) -> bool:
        return self._norm(path) in self.files

    def is_file(self, path: str) -> bool:
        entry = self.files.get(self._norm(path))
        return entry is not None and not entry[0]

    def is_dir(self, path: str) -> bool:
        entry = self.files.get(self._norm(path))
        return entry is not None and entry[0]

    def get_size(self, path: str) -> int:
        entry = self.files.get(self._norm(path))
        return entry[1] if entry else 0

    def list_dir(self, path: str) -> List[str]:
        norm_p = self._norm(path)
        prefix = norm_p + "/"
        children: Set[str] = set()
        for p in self.files:
            if p.startswith(prefix) and p != norm_p:
                sub = p[len(prefix):].split("/")[0]
                children.add(f"{norm_p}/{sub}")
        return list(children)

    def remove_file(self, path: str, secure: bool = False) -> Result[None, DomainError]:
        norm_p = self._norm(path)
        entry = self.files.get(norm_p)
        if entry is None:
            return Err(DeletionFailedError(f"File not found: {path}"))

        if entry[2]:  # locked file simulation
            attempts = self.lock_attempts.get(norm_p, 0) + 1
            self.lock_attempts[norm_p] = attempts
            # Unlock after 2 attempts to simulate successful retry
            if attempts >= 2:
                self.files[norm_p] = (entry[0], entry[1], False)
            else:
                return Err(DeletionFailedError(f"File is locked by process: {path}"))

        del self.files[norm_p]
        if norm_p in self.file_contents:
            del self.file_contents[norm_p]
        self.deleted_paths.append(path)
        return Ok(None)

    def remove_dir(self, path: str) -> Result[None, DomainError]:
        norm_p = self._norm(path)
        if norm_p not in self.files:
            return Err(DeletionFailedError(f"Directory not found: {path}"))

        prefix = norm_p + "/"
        to_delete = [p for p in self.files if p == norm_p or p.startswith(prefix)]
        for p in to_delete:
            del self.files[p]
            if p in self.file_contents:
                del self.file_contents[p]
            self.deleted_paths.append(p)
        return Ok(None)

    def truncate_file(self, path: str) -> Result[None, DomainError]:
        norm_p = self._norm(path)
        entry = self.files.get(norm_p)
        if entry is None:
            return Err(DeletionFailedError(f"File not found: {path}"))
        self.files[norm_p] = (entry[0], 0, entry[2])
        if norm_p in self.file_contents:
            self.file_contents[norm_p] = ""
        self.deleted_paths.append(path)
        return Ok(None)

    def purge_dir_contents(self, path: str) -> Result[None, DomainError]:
        norm_p = self._norm(path)
        if norm_p not in self.files:
            return Err(DeletionFailedError(f"Directory not found: {path}"))
        prefix = norm_p + "/"
        to_delete = [p for p in self.files if p.startswith(prefix) and p != norm_p]
        for p in to_delete:
            del self.files[p]
            if p in self.file_contents:
                del self.file_contents[p]
            self.deleted_paths.append(p)
        return Ok(None)


    def find_matching_paths(self, base_path: str, pattern: str) -> List[str]:
        norm_base = self._norm(base_path)
        matched: List[str] = []
        for p in self.files:
            if p.startswith(norm_base):
                rel = p[len(norm_base):].lstrip("/")
                if fnmatch.fnmatch(rel, pattern.lower()) or fnmatch.fnmatch(p, pattern.lower()):
                    matched.append(p)
        return matched

    def write_text_file(self, path: str, content: str) -> Result[None, DomainError]:
        norm_p = self._norm(path)
        self.files[norm_p] = (False, len(content.encode("utf-8")), False)
        self.file_contents[norm_p] = content
        return Ok(None)

    def read_text_file(self, path: str) -> Optional[str]:
        return self.file_contents.get(self._norm(path))


class FakePlatformPathsPort(PlatformPathsPort):
    """Simulated platform paths for Linux/UNIX workstation profile."""

    def __init__(self, user_home: str = "/home/student") -> None:
        self.user_home = user_home

    def get_user_home(self) -> str:
        return self.user_home

    def get_documents_dir(self) -> str:
        return f"{self.user_home}/Documents"

    def get_downloads_dir(self) -> str:
        return f"{self.user_home}/Downloads"

    def get_desktop_dir(self) -> str:
        return f"{self.user_home}/Desktop"

    def get_pictures_dir(self) -> str:
        return f"{self.user_home}/Pictures"

    def get_videos_dir(self) -> str:
        return f"{self.user_home}/Videos"

    def get_music_dir(self) -> str:
        return f"{self.user_home}/Music"

    def get_temp_dirs(self) -> List[str]:
        return [f"{self.user_home}/.cache", "/tmp"]

    def get_recent_files_paths(self) -> List[str]:
        return [f"{self.user_home}/.local/share/recently-used.xbel"]

    def get_trash_paths(self) -> List[str]:
        return [f"{self.user_home}/.local/share/Trash"]

    def get_browser_paths(self) -> List[Tuple[str, str, str]]:
        return [
            ("chrome", "NATIVE", f"{self.user_home}/.config/google-chrome"),
            ("firefox", "NATIVE", f"{self.user_home}/.mozilla/firefox"),
        ]

    def get_credential_paths(self) -> List[str]:
        return [f"{self.user_home}/.ssh", f"{self.user_home}/.aws"]

    def get_shell_history_paths(self) -> List[str]:
        return [f"{self.user_home}/.bash_history", f"{self.user_home}/.zsh_history"]

    def get_cloud_sync_paths(self) -> List[str]:
        return [f"{self.user_home}/Dropbox", f"{self.user_home}/Google Drive"]

    def get_system_protected_rules(self) -> List[ProtectedPathRule]:
        return ProtectedPathRule.get_default_system_rules()


class FakeProcessPort(ProcessPort):
    """In-memory test double for closing locking processes."""

    def __init__(self) -> None:
        self.terminated_targets: List[TargetCategory] = []

    def terminate_processes_for_target(self, category: TargetCategory) -> Result[int, DomainError]:
        self.terminated_targets.append(category)
        return Ok(1)


class FakeCredentialStorePort(CredentialStorePort):
    """In-memory test double for clearing user credentials."""

    def __init__(self) -> None:
        self.cleared = False

    def clear_user_credentials(self) -> Result[None, DomainError]:
        self.cleared = True
        return Ok(None)

