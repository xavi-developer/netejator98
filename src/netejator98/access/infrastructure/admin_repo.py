"""File-based AdminCredentialRepository storing admin authentication verifiers."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Optional

from netejator98.access.domain.repositories import AdminCredentialRepositoryPort
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Err, Ok, Result


class FileAdminCredentialRepository(AdminCredentialRepositoryPort):
    """Stores administrator password verifier in a protected JSON file."""

    def __init__(self, storage_dir: str | Path) -> None:
        self._dir = Path(storage_dir)
        self._file = self._dir / "admin_auth.json"

    def get_verifier(self) -> Optional[str]:
        if not self._file.exists():
            return None
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("verifier")
        except Exception:
            return None

    def save_verifier(self, verifier: str, salt: str) -> Result[None, DomainError]:
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            data = {
                "verifier": verifier,
                "salt": salt,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            with tempfile.NamedTemporaryFile(
                "w", dir=self._dir, delete=False, encoding="utf-8"
            ) as tf:
                json.dump(data, tf, indent=2)
                temp_name = tf.name

            os.replace(temp_name, self._file)
            return Ok(None)
        except Exception as e:
            return Err(DomainError(f"Failed to save admin verifier: {e}"))

    def has_password(self) -> bool:
        return self.get_verifier() is not None

