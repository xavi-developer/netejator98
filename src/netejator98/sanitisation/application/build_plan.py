"""BuildSanitisationPlanUseCase resolving policy targets into a concrete execution plan."""

from __future__ import annotations

from typing import Dict, List, Tuple

from netejator98.sanitisation.application.ports import FileSystemPort, PlatformPathsPort
from netejator98.sanitisation.domain.plan import SanitisationPlan
from netejator98.sanitisation.domain.planner import SanitisationPlanner
from netejator98.sanitisation.domain.policy import CleaningPolicy


class BuildSanitisationPlanUseCase:
    """Discovers paths on the filesystem matching policy targets and creates a SanitisationPlan."""

    def __init__(
        self,
        fs: FileSystemPort,
        paths: PlatformPathsPort,
        platform_name: str | None = None,
    ) -> None:
        self._fs = fs
        self._paths = paths
        self._platform_name = platform_name

    def _resolve_platform(self) -> str:
        if self._platform_name:
            return self._platform_name.strip().lower()
        cls_name = self._paths.__class__.__name__.lower()
        if "windows" in cls_name:
            return "windows"
        if "mac" in cls_name:
            return "darwin"
        if "linux" in cls_name:
            return "linux"
        import platform
        return platform.system().lower()

    def execute(self, policy: CleaningPolicy) -> SanitisationPlan:
        user_home = self._paths.get_user_home()
        current_os = self._resolve_platform()
        target_discovered: Dict[str, List[Tuple[str, bool, int]]] = {}

        for target in policy.targets:
            if not target.enabled:
                continue
            if hasattr(target, "applies_to_os") and not target.applies_to_os(current_os):
                continue

            discovered: List[Tuple[str, bool, int]] = []
            for pattern in target.patterns:
                pat_str = pattern.pattern
                # Resolve relative patterns against user home
                if pat_str.startswith("/") or (len(pat_str) > 2 and pat_str[1] == ":"):
                    base_dir = pat_str
                    search_pat = ""
                else:
                    base_dir = user_home
                    search_pat = pat_str

                if pattern.is_glob():
                    matches = self._fs.find_matching_paths(base_dir, search_pat)
                    for m in matches:
                        if self._fs.exists(m):
                            is_dir = self._fs.is_dir(m)
                            size = self._fs.get_size(m)
                            discovered.append((m, is_dir, size))
                else:
                    target_path = (
                        pat_str
                        if (pat_str.startswith("/") or (len(pat_str) > 2 and pat_str[1] == ":"))
                        else f"{user_home.rstrip('/')}/{pat_str.lstrip('/')}"
                    )
                    if self._fs.exists(target_path):
                        is_dir = self._fs.is_dir(target_path)
                        size = self._fs.get_size(target_path)
                        discovered.append((target_path, is_dir, size))

            target_discovered[target.name] = discovered
            target_discovered[f"{target.name}::{target.os}"] = discovered

        return SanitisationPlanner.plan(
            policy=policy,
            user_profile_root=user_home,
            target_discovered_paths=target_discovered,
        )

