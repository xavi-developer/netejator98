"""DryRunUseCase for simulating sanitisation without deleting any files."""

from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Dict, List, Optional, Tuple

from netejator98.sanitisation.application.build_plan import (
    BuildSanitisationPlanUseCase,
)
from netejator98.sanitisation.application.logger import SanitisationTracer
from netejator98.sanitisation.application.ports import FileSystemPort, PlatformPathsPort
from netejator98.sanitisation.domain.outcome import (
    SanitisationOutcome,
    TargetResult,
)
from netejator98.sanitisation.domain.policy import CleaningPolicy
from netejator98.shared.clock import ClockPort, SystemClock


class DryRunUseCase:
    """Produces a simulated sanitisation outcome without altering the filesystem."""

    def __init__(
        self,
        fs: FileSystemPort,
        paths: PlatformPathsPort,
        clock: Optional[ClockPort] = None,
    ) -> None:
        self._builder = BuildSanitisationPlanUseCase(fs, paths)
        self._clock = clock or SystemClock()

    def execute(
        self, policy: CleaningPolicy, user_email: Optional[str] = None
    ) -> SanitisationOutcome:
        start_time = time.monotonic()
        now = self._clock.now_utc()

        tracer = SanitisationTracer(enabled=getattr(policy, "thorough_logging", False))
        if tracer.enabled:
            current_os = self._builder._resolve_platform()
            tracer.log_header(mode="DRY-RUN (Simulation)", user_email=user_email, platform_name=current_os)

        plan = self._builder.execute(policy, tracer=tracer)

        # Aggregate plan items by target
        target_counts: Dict[str, int] = {}
        target_bytes: Dict[str, int] = {}
        targets_seen: List[str] = []

        for item in plan.items:
            if item.target_name not in target_counts:
                target_counts[item.target_name] = 0
                target_bytes[item.target_name] = 0
                targets_seen.append(item.target_name)

            target_counts[item.target_name] += 1
            target_bytes[item.target_name] += item.estimated_bytes

            if tracer.enabled:
                tracer.log_action(
                    action="SIMULATE",
                    path=item.path,
                    target_name=item.target_name,
                    strategy=item.strategy.value,
                    is_dir=item.is_directory,
                    size_bytes=item.estimated_bytes,
                    success=True,
                )

        target_results: List[TargetResult] = []
        for t_name in targets_seen:
            target_results.append(
                TargetResult(
                    target_name=t_name,
                    files_deleted=target_counts[t_name],
                    bytes_freed=target_bytes[t_name],
                    errors=(),
                    success=True,
                )
            )

        duration = time.monotonic() - start_time

        if tracer.enabled:
            tracer.log_summary(
                total_files=plan.total_items,
                total_bytes=plan.total_estimated_bytes,
                elapsed_seconds=duration,
                is_success=True,
                errors=[],
            )

        return SanitisationOutcome(
            timestamp=now,
            user_email=user_email,
            dry_run=True,
            targets_processed=tuple(targets_seen),
            target_results=tuple(target_results),
            files_deleted=plan.total_items,
            bytes_freed=plan.total_estimated_bytes,
            errors=(),
            duration_seconds=duration,
            log_file_path=tracer.log_file_path if tracer.enabled else None,
        )

