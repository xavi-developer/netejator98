"""CleaningPolicy aggregate root enforcing protected-path invariants and managing targets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from netejator98.sanitisation.domain.path_pattern import PathPattern
from netejator98.sanitisation.domain.protected_path import ProtectedPathRule
from netejator98.sanitisation.domain.strategy import DeletionStrategy
from netejator98.sanitisation.domain.target import CleaningTarget, TargetCategory
from netejator98.shared.errors import PolicyValidationError, ProtectedPathViolationError


@dataclass
class CleaningPolicy:
    """Aggregate root governing all cleaning targets and invariant safety rules."""

    targets: List[CleaningTarget] = field(default_factory=list)
    protected_rules: List[ProtectedPathRule] = field(default_factory=list)
    dry_run: bool = True
    secure_delete: bool = False
    always_clean_on_boot: bool = False
    thorough_logging: bool = False
    retention_days: int = 365
    reset_to_golden_profile: bool = False
    golden_profile_path: str = "/etc/skel"
    golden_profile_shortcuts: List[Dict[str, str]] = field(
        default_factory=lambda: [{"name": "insestatut.cat", "url": "https://insestatut.cat"}]
    )

    def __post_init__(self) -> None:
        if not self.protected_rules:
            self.protected_rules = ProtectedPathRule.get_default_system_rules()
        self.validate()

    def validate(self) -> None:
        """Validate invariant: no cleaning target may violate any protected path rule."""
        for target in self.targets:
            for pattern in target.patterns:
                # Check absolute patterns against protected rules
                raw_pat = pattern.pattern
                for rule in self.protected_rules:
                    if rule.is_violating(raw_pat):
                        raise ProtectedPathViolationError(
                            f"Target '{target.name}' pattern '{raw_pat}' violates protected path '{rule.path}' ({rule.description})",
                            details=raw_pat,
                        )

    def add_target(self, target: CleaningTarget) -> None:
        """Add a target and enforce safety invariants."""
        for pattern in target.patterns:
            raw_pat = pattern.pattern
            for rule in self.protected_rules:
                if rule.is_violating(raw_pat):
                    raise ProtectedPathViolationError(
                        f"Cannot add target '{target.name}': pattern '{raw_pat}' violates protected path '{rule.path}'",
                        details=raw_pat,
                    )
        self.targets.append(target)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize policy to a dictionary for YAML persistence."""
        return {
            "dry_run": self.dry_run,
            "secure_delete": self.secure_delete,
            "always_clean_on_boot": self.always_clean_on_boot,
            "thorough_logging": self.thorough_logging,
            "retention_days": self.retention_days,
            "reset_to_golden_profile": self.reset_to_golden_profile,
            "golden_profile_path": self.golden_profile_path,
            "golden_profile_shortcuts": self.golden_profile_shortcuts,
            "targets": [
                {
                    "name": t.name,
                    "os": getattr(t, "os", "ALL"),
                    "category": t.category.value,
                    "patterns": [p.pattern for p in t.patterns],
                    "strategy": t.strategy.value,
                    "description": t.description,
                    "enabled": t.enabled,
                }
                for t in self.targets
            ],
            "protected_paths": [
                {"path": r.path, "description": r.description} for r in self.protected_rules
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CleaningPolicy:
        """Construct CleaningPolicy from dictionary."""
        targets: List[CleaningTarget] = []
        for t_dict in data.get("targets", []):
            patterns = tuple(PathPattern(p) for p in t_dict.get("patterns", []))
            target = CleaningTarget(
                name=t_dict["name"],
                category=TargetCategory(t_dict.get("category", TargetCategory.CUSTOM.value)),
                patterns=patterns,
                strategy=DeletionStrategy(
                    t_dict.get("strategy", DeletionStrategy.STANDARD.value)
                ),
                description=t_dict.get("description", ""),
                enabled=t_dict.get("enabled", False),
                os=t_dict.get("os", "ALL"),
            )
            targets.append(target)

        rules: List[ProtectedPathRule] = []
        for r_dict in data.get("protected_paths", []):
            rules.append(ProtectedPathRule(r_dict["path"], r_dict.get("description", "")))
        if not rules:
            rules = ProtectedPathRule.get_default_system_rules()

        default_shortcuts = [{"name": "insestatut.cat", "url": "https://insestatut.cat"}]
        shortcuts = data.get("golden_profile_shortcuts")
        if shortcuts is None:
            shortcuts = default_shortcuts

        return cls(
            targets=targets,
            protected_rules=rules,
            dry_run=data.get("dry_run", True),
            secure_delete=data.get("secure_delete", False),
            always_clean_on_boot=data.get("always_clean_on_boot", False),
            thorough_logging=data.get("thorough_logging", False),
            retention_days=data.get("retention_days", 365),
            reset_to_golden_profile=data.get("reset_to_golden_profile", False),
            golden_profile_path=data.get("golden_profile_path") or "/etc/skel",
            golden_profile_shortcuts=shortcuts,
        )

