"""ProtectedPathRule value object defining non-negotiable system safety boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ProtectedPathRule:
    """An invariant safety rule prohibiting deletion of system or critical directories."""

    path: str
    description: str

    def __post_init__(self) -> None:
        cleaned = self._normalize(self.path)
        if not cleaned:
            raise ValueError("Protected path cannot be empty")
        object.__setattr__(self, "path", cleaned)

    @staticmethod
    def _normalize(p: str) -> str:
        raw = p.strip().replace("\\", "/")
        if raw == "/":
            return "/"
        norm = raw.rstrip("/")
        if norm.endswith(":") and len(norm) == 2:  # Windows drive letter C:
            norm = norm + "/"
        if not norm:
            return "/"
        return norm.lower()

    def is_violating(self, candidate_path: str) -> bool:
        """Return True if candidate_path overlaps, contains, or resides within this protected path."""
        cand_norm = self._normalize(candidate_path)
        prot_norm = self.path

        # Exact match: deleting the protected path itself is always a violation
        if cand_norm == prot_norm:
            return True

        # If protected path is the root filesystem itself, only deleting root itself is prohibited
        if prot_norm in ("/", "c:/"):
            return False

        # For sub-roots (e.g. /etc, /usr, C:/Windows):
        # 1. Candidate is inside protected directory (e.g. cand = /etc/passwd, prot = /etc)
        prot_prefix = prot_norm if prot_norm.endswith("/") else (prot_norm + "/")
        if cand_norm.startswith(prot_prefix):
            return True

        # 2. Candidate is ancestor of protected directory (e.g. cand = /, prot = /etc)
        cand_prefix = cand_norm if cand_norm.endswith("/") else (cand_norm + "/")
        if prot_norm.startswith(cand_prefix):
            return True

        return False

    @classmethod
    def get_default_system_rules(cls) -> List[ProtectedPathRule]:
        """Core non-negotiable system protection rules across POSIX and Windows."""
        return [
            # Linux / POSIX system roots
            cls("/", "Filesystem root"),
            cls("/bin", "System binaries"),
            cls("/sbin", "System admin binaries"),
            cls("/usr", "User system hierarchy"),
            cls("/etc", "System configuration"),
            cls("/lib", "System shared libraries"),
            cls("/lib64", "64-bit system libraries"),
            cls("/boot", "Kernel boot loader files"),
            cls("/dev", "Device nodes"),
            cls("/proc", "Process virtual filesystem"),
            cls("/sys", "Kernel sysfs"),
            cls("/root", "Root user home profile"),
            cls("/var/lib/netejator98", "Netejator98 data and audit directory (Linux)"),
            # Windows system roots
            cls("c:/", "Windows system drive root"),
            cls("c:/windows", "Windows operating system files"),
            cls("c:/program files", "64-bit program installation directory"),
            cls("c:/program files (x86)", "32-bit program installation directory"),
            cls("c:/programdata/netejator98", "Netejator98 data and audit directory (Windows)"),
            # macOS system roots
            cls("/system", "macOS system directory"),
            cls("/library", "macOS root system library"),
            cls(
                "/library/application support/netejator98",
                "Netejator98 data and audit directory (macOS)",
            ),
        ]
