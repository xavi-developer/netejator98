"""SanitisationOutcome and TargetResult value objects summarizing sanitisation runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class TargetResult:
    """Outcome for an individual cleaning target."""

    target_name: str
    files_deleted: int
    bytes_freed: int
    errors: Tuple[str, ...]
    success: bool


@dataclass(frozen=True)
class SanitisationOutcome:
    """Comprehensive summary of a sanitisation execution run."""

    timestamp: datetime
    user_email: Optional[str]
    dry_run: bool
    targets_processed: Tuple[str, ...]
    target_results: Tuple[TargetResult, ...]
    files_deleted: int
    bytes_freed: int
    errors: Tuple[str, ...]
    duration_seconds: float
    log_file_path: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """True if all targets completed without critical errors."""
        return len(self.errors) == 0

    @classmethod
    def empty(cls, dry_run: bool = False, user_email: Optional[str] = None) -> SanitisationOutcome:
        return cls(
            timestamp=datetime.now(timezone.utc),
            user_email=user_email,
            dry_run=dry_run,
            targets_processed=(),
            target_results=(),
            files_deleted=0,
            bytes_freed=0,
            errors=(),
            duration_seconds=0.0,
        )

