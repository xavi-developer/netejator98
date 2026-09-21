"""SanitisationPlan and PlannedDeletion value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from netejator98.sanitisation.domain.strategy import DeletionStrategy


@dataclass(frozen=True)
class PlannedDeletion:
    """A concrete file or directory resolved and scheduled for erasure."""

    path: str
    target_name: str
    strategy: DeletionStrategy
    is_directory: bool
    estimated_bytes: int


@dataclass(frozen=True)
class SanitisationPlan:
    """The fully planned and ordered list of paths to be deleted."""

    user_profile_root: str
    items: Tuple[PlannedDeletion, ...]

    @property
    def total_items(self) -> int:
        return len(self.items)

    @property
    def total_estimated_bytes(self) -> int:
        return sum(item.estimated_bytes for item in self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0

