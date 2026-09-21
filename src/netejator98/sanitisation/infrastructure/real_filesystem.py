"""RealFileSystem infrastructure adapter implementing FileSystemPort with resilient deletion."""

from __future__ import annotations

import glob
import os
from pathlib import Path
import shutil
import stat
from typing import List

from netejator98.sanitisation.application.ports import FileSystemPort
from netejator98.shared.errors import DeletionFailedError, DomainError, FileWriteError
from netejator98.shared.result import Err, Ok, Result


class RealFileSystem(FileSystemPort):
    """Production filesystem adapter with read-only clearing and secure overwrite."""

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def is_file(self, path: str) -> bool:
        return os.path.isfile(path) and not os.path.islink(path)

    def is_dir(self, path: str) -> bool:
        return os.path.isdir(path)

    def get_size(self, path: str) -> int:
        try:
            if os.path.isfile(path):
                return os.path.getsize(path)
            elif os.path.isdir(path):
                total = 0
                for root, _, files in os.walk(path):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            total += os.path.getsize(fp)
                        except OSError:
                            pass
                return total
        except OSError:
            pass
        return 0

    def list_dir(self, path: str) -> List[str]:
        try:
            return [os.path.join(path, entry) for entry in os.listdir(path)]
        except OSError:
            return []

    def _ensure_writable(self, path: str) -> None:
        """Clear read-only attributes so files can be deleted."""
        try:
            current_mode = os.stat(path).st_mode
            os.chmod(path, current_mode | stat.S_IWUSR | stat.S_IWGRP)
        except OSError:
            pass

    def _secure_overwrite(self, path: str) -> None:
        """Overwrite file with zeros before unlinking (best-effort secure delete)."""
        try:
            size = os.path.getsize(path)
            if size > 0:
                with open(path, "ba+", buffering=0) as f:
                    f.seek(0)
                    chunk_size = 65536
                    zeros = b"\x00" * min(size, chunk_size)
                    remaining = size
                    while remaining > 0:
                        write_len = min(remaining, chunk_size)
                        f.write(zeros[:write_len])
                        remaining -= write_len
                    f.flush()
                    os.fsync(f.fileno())
        except OSError:
            pass

    def remove_file(self, path: str, secure: bool = False) -> Result[None, DomainError]:
        if not os.path.exists(path) and not os.path.islink(path):
            return Ok(None)

        self._ensure_writable(path)

        if secure and os.path.isfile(path) and not os.path.islink(path):
            self._secure_overwrite(path)

        try:
            os.unlink(path)
            return Ok(None)
        except OSError as e:
            return Err(DeletionFailedError(f"Failed to unlink file '{path}': {e}"))

    def remove_dir(self, path: str) -> Result[None, DomainError]:
        if not os.path.exists(path):
            return Ok(None)

        def _on_error(func: object, p: str, exc_info: object) -> None:
            self._ensure_writable(p)
            try:
                os.unlink(p)
            except OSError:
                pass

        try:
            shutil.rmtree(path, onerror=_on_error)
            return Ok(None)
        except OSError as e:
            return Err(DeletionFailedError(f"Failed to remove directory '{path}': {e}"))

    def truncate_file(self, path: str) -> Result[None, DomainError]:
        if not os.path.exists(path) and not os.path.islink(path):
            return Ok(None)
        self._ensure_writable(path)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.truncate(0)
            return Ok(None)
        except OSError as e:
            return Err(DeletionFailedError(f"Failed to truncate file '{path}': {e}"))

    def purge_dir_contents(self, path: str) -> Result[None, DomainError]:
        if not os.path.exists(path):
            return Ok(None)
        try:
            for item in os.listdir(path):
                sub_path = os.path.join(path, item)
                if os.path.isdir(sub_path) and not os.path.islink(sub_path):
                    res = self.remove_dir(sub_path)
                else:
                    res = self.remove_file(sub_path)
                if res.is_err():
                    return res
            return Ok(None)
        except OSError as e:
            return Err(DeletionFailedError(f"Failed to purge directory contents '{path}': {e}"))


    def find_matching_paths(self, base_path: str, pattern: str) -> List[str]:
        if not os.path.exists(base_path):
            return []

        full_pattern = os.path.join(base_path, pattern)
        try:
            matches = glob.glob(full_pattern, recursive=True)
            return [os.path.normpath(m) for m in matches]
        except Exception:
            return []

    def write_text_file(self, path: str, content: str) -> Result[None, DomainError]:
        try:
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return Ok(None)
        except OSError as e:
            return Err(FileWriteError(f"Failed to write file '{path}': {e}"))

