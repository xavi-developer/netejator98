"""Ports (interfaces) for the Sanitisation application layer."""

from __future__ import annotations

from typing import List, Protocol, Tuple

from netejator98.sanitisation.domain.protected_path import ProtectedPathRule
from netejator98.sanitisation.domain.target import TargetCategory
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Result


class FileSystemPort(Protocol):
    """Port for interacting with the workstation filesystem."""

    def exists(self, path: str) -> bool:
        ...

    def is_file(self, path: str) -> bool:
        ...

    def is_dir(self, path: str) -> bool:
        ...

    def get_size(self, path: str) -> int:
        ...

    def list_dir(self, path: str) -> List[str]:
        ...

    def remove_file(self, path: str, secure: bool = False) -> Result[None, DomainError]:
        ...

    def remove_dir(self, path: str) -> Result[None, DomainError]:
        ...

    def truncate_file(self, path: str) -> Result[None, DomainError]:
        ...

    def purge_dir_contents(self, path: str) -> Result[None, DomainError]:
        ...

    def find_matching_paths(self, base_path: str, pattern: str) -> List[str]:
        ...

    def write_text_file(self, path: str, content: str) -> Result[None, DomainError]:
        ...


class PlatformPathsPort(Protocol):
    """Port resolving OS-specific user directory surfaces."""

    def get_user_home(self) -> str:
        ...

    def get_documents_dir(self) -> str:
        ...

    def get_downloads_dir(self) -> str:
        ...

    def get_desktop_dir(self) -> str:
        ...

    def get_pictures_dir(self) -> str:
        ...

    def get_videos_dir(self) -> str:
        ...

    def get_music_dir(self) -> str:
        ...

    def get_temp_dirs(self) -> List[str]:
        ...

    def get_recent_files_paths(self) -> List[str]:
        ...

    def get_trash_paths(self) -> List[str]:
        ...

    def get_browser_paths(self) -> List[Tuple[str, str, str]]:
        """Return list of (browser_name, variant, profile_path)."""
        ...

    def get_credential_paths(self) -> List[str]:
        ...

    def get_shell_history_paths(self) -> List[str]:
        ...

    def get_cloud_sync_paths(self) -> List[str]:
        ...

    def get_system_protected_rules(self) -> List[ProtectedPathRule]:
        ...


class ProcessPort(Protocol):
    """Port for checking and closing running applications blocking file removal."""

    def terminate_processes_for_target(self, category: TargetCategory) -> Result[int, DomainError]:
        ...


class CredentialStorePort(Protocol):
    """Port for purging system keyring / Credential Manager entries."""

    def clear_user_credentials(self) -> Result[None, DomainError]:
        ...

