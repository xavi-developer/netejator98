"""Sanitisation domain models, aggregate root, and services."""

from netejator98.sanitisation.domain.browser import (
    BrowserProfile,
    BrowserType,
    BrowserVariant,
)
from netejator98.sanitisation.domain.events import (
    SanitisationCompleted,
    SanitisationFailed,
    SanitisationRequested,
)
from netejator98.sanitisation.domain.outcome import (
    SanitisationOutcome,
    TargetResult,
)
from netejator98.sanitisation.domain.path_pattern import PathPattern
from netejator98.sanitisation.domain.plan import PlannedDeletion, SanitisationPlan
from netejator98.sanitisation.domain.planner import SanitisationPlanner
from netejator98.sanitisation.domain.policy import CleaningPolicy
from netejator98.sanitisation.domain.protected_path import ProtectedPathRule
from netejator98.sanitisation.domain.strategy import DeletionStrategy
from netejator98.sanitisation.domain.target import CleaningTarget, TargetCategory

__all__ = [
    "PathPattern",
    "ProtectedPathRule",
    "DeletionStrategy",
    "BrowserType",
    "BrowserVariant",
    "BrowserProfile",
    "TargetCategory",
    "CleaningTarget",
    "CleaningPolicy",
    "PlannedDeletion",
    "SanitisationPlan",
    "TargetResult",
    "SanitisationOutcome",
    "SanitisationPlanner",
    "SanitisationRequested",
    "SanitisationCompleted",
    "SanitisationFailed",
]

