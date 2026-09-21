"""EncryptedJsonlAuditRepository for append-only sealed audit log storage."""

from __future__ import annotations

import os
from pathlib import Path
import threading
from typing import List, Optional

from netejator98.audit.domain.ports import AuditLogRepositoryPort
from netejator98.audit.domain.sealed_entry import SealedEntry
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Err, Ok, Result


class EncryptedJsonlAuditRepository(AuditLogRepositoryPort):
    """Thread-safe append-only repository storing sealed entries as JSONL."""

    def __init__(self, storage_dir: str | Path, filename: str = "audit_trail.jsonl") -> None:
        self._dir = Path(storage_dir)
        self._file = self._dir / filename
        self._lock = threading.Lock()
        self._cached_last: Optional[SealedEntry] = None
        self._initialized = False

    def _ensure_loaded(self) -> None:
        if not self._initialized:
            self._cached_last = self._read_last_from_disk()
            self._initialized = True

    def _read_last_from_disk(self) -> Optional[SealedEntry]:
        if not self._file.exists():
            return None
        last_line = ""
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        last_line = stripped
            if last_line:
                return SealedEntry.from_json_str(last_line)
        except Exception:
            return None
        return None

    def append_entry(self, entry: SealedEntry) -> Result[None, DomainError]:
        with self._lock:
            self._ensure_loaded()
            try:
                self._dir.mkdir(parents=True, exist_ok=True)
                line = entry.to_json_str() + "\n"
                with open(self._file, "a", encoding="utf-8") as f:
                    f.write(line)
                    f.flush()
                    os.fsync(f.fileno())
                self._cached_last = entry
                return Ok(None)
            except Exception as e:
                return Err(DomainError(f"Failed to append audit entry: {e}"))

    def get_last_entry(self) -> Optional[SealedEntry]:
        with self._lock:
            self._ensure_loaded()
            return self._cached_last

    def get_all_entries(self) -> List[SealedEntry]:
        with self._lock:
            if not self._file.exists():
                return []
            entries: List[SealedEntry] = []
            with open(self._file, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    stripped = line.strip()
                    if stripped:
                        try:
                            entries.append(SealedEntry.from_json_str(stripped))
                        except Exception as e:
                            raise ValueError(
                                f"Corrupted audit record on line {line_no}: {e}"
                            ) from e
            return entries

    def count(self) -> int:
        with self._lock:
            if not self._file.exists():
                return 0
            count = 0
            with open(self._file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
            return count
