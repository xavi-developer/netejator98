"""SanitisationPlanner domain service building safe, validated execution plans."""

from __future__ import annotations

from typing import Dict, List, Tuple

from netejator98.sanitisation.domain.plan import PlannedDeletion, SanitisationPlan
from netejator98.sanitisation.domain.policy import CleaningPolicy
from netejator98.sanitisation.domain.strategy import DeletionStrategy


class SanitisationPlanner:
    """Domain service converting CleaningPolicy and discovered paths into a SanitisationPlan."""

    @classmethod
    def plan(
        cls,
        policy: CleaningPolicy,
        user_profile_root: str,
        target_discovered_paths: Dict[str, List[Tuple[str, bool, int]]],  # (path, is_dir, bytes)
    ) -> SanitisationPlan:
        """Create a sanitisation plan, strictly rejecting any path violating protected path rules."""
        planned_items: List[PlannedDeletion] = []

        for target in policy.targets:
            if not target.enabled:
                continue

            discovered = target_discovered_paths.get(
                f"{target.name}::{getattr(target, 'os', 'ALL')}",
                target_discovered_paths.get(target.name, []),
            )
            for path, is_dir, size_bytes in discovered:
                # 1. Enforce safety invariants against all protected path rules
                violates = False
                for rule in policy.protected_rules:
                    if rule.is_violating(path):
                        violates = True
                        break

                if violates:
                    # Invariant violation: skip dangerous path
                    continue

                # 2. Determine deletion strategy (policy global secure_delete overrides if True)
                strat = (
                    DeletionStrategy.SECURE
                    if policy.secure_delete
                    else target.strategy
                )

                planned_items.append(
                    PlannedDeletion(
                        path=path,
                        target_name=target.name,
                        strategy=strat,
                        is_directory=is_dir,
                        estimated_bytes=size_bytes,
                    )
                )

        return SanitisationPlan(
            user_profile_root=user_profile_root,
            items=tuple(planned_items),
        )

