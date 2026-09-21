"""File-based LastUserRepository persisting hashed student email records."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Optional

from netejator98.access.domain.repositories import LastUserRepositoryPort
from netejator98.access.domain.user import LastUserRecord
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Err, Ok, Result


class FileLastUserRepository(LastUserRepositoryPort):
    """Stores the last user's salted email hash in a protected JSON file."""

    def __init__(self, storage_dir: str | Path) -> None:
        self._dir = Path(storage_dir)
        self._file = self._dir / "last_user.json"

    def get_last_user(self) -> Optional[LastUserRecord]:
        if not self._file.exists():
            return None

        try:
            with open(self._file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return LastUserRecord(
                email_hash=data["email_hash"],
                salt=data["salt"],
                recorded_at=datetime.fromisoformat(data["recorded_at"]),
            )
        except Exception:
            return None

    def save_last_user(self, record: LastUserRecord) -> Result[None, DomainError]:
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            data = {
                "email_hash": record.email_hash,
                "salt": record.salt,
                "recorded_at": record.recorded_at.astimezone(timezone.utc).isoformat(),
            }

            # Atomic write via tempfile and replace
            with tempfile.NamedTemporaryFile(
                "w", dir=self._dir, delete=False, encoding="utf-8"
            ) as tf:
                json.dump(data, tf, indent=2)
                temp_name = tf.name

            os.replace(temp_name, self._file)
            return Ok(None)
        except Exception as e:
            return Err(DomainError(f"Failed to save last user record: {e}"))

