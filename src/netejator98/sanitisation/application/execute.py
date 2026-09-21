"""ExecuteSanitisationUseCase implementing resilient deletion with retry and safety checks."""

from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Dict, List, Optional, Tuple

from netejator98.sanitisation.application.build_plan import (
    BuildSanitisationPlanUseCase,
)
from netejator98.sanitisation.application.logger import SanitisationTracer
from netejator98.sanitisation.application.ports import (
    CredentialStorePort,
    FileSystemPort,
    PlatformPathsPort,
    ProcessPort,
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
from netejator98.sanitisation.domain.policy import CleaningPolicy
from netejator98.sanitisation.domain.strategy import DeletionStrategy
from netejator98.sanitisation.domain.target import TargetCategory
from netejator98.shared.clock import ClockPort, SystemClock
from netejator98.shared.event_bus import EventBus


class ExecuteSanitisationUseCase:
    """Executes resilient workstation profile sanitisation with safety invariants."""

    def __init__(
        self,
        fs: FileSystemPort,
        paths: PlatformPathsPort,
        event_bus: EventBus,
        process_port: Optional[ProcessPort] = None,
        credential_port: Optional[CredentialStorePort] = None,
        clock: Optional[ClockPort] = None,
        max_retries: int = 3,
        retry_delay_seconds: float = 0.05,
    ) -> None:
        self._fs = fs
        self._paths = paths
        self._event_bus = event_bus
        self._process = process_port
        self._credential = credential_port
        self._clock = clock or SystemClock()
        self._max_retries = max_retries
        self._retry_delay = retry_delay_seconds
        self._builder = BuildSanitisationPlanUseCase(fs, paths)

    def execute(
        self, policy: CleaningPolicy, user_email: Optional[str] = None
    ) -> SanitisationOutcome:
        start_time = time.monotonic()
        now = self._clock.now_utc()

        tracer = SanitisationTracer(enabled=getattr(policy, "thorough_logging", False))
        if tracer.enabled:
            current_os = self._builder._resolve_platform()
            tracer.log_header(mode="REAL EXECUTION (Deletion)", user_email=user_email, platform_name=current_os)

        self._event_bus.publish(
            SanitisationRequested(user_email=user_email, dry_run=False, timestamp=now)
        )

        # 1. Close active locking applications if process port is provided
        if self._process is not None:
            if tracer.enabled:
                tracer.log("Terminating active locking applications (browsers)...")
            self._process.terminate_processes_for_target(TargetCategory.BROWSER_PROFILES)

        # 2. Clear credentials if credential port is provided
        if self._credential is not None:
            if tracer.enabled:
                tracer.log("Clearing saved user credentials...")
            self._credential.clear_user_credentials()

        # 3. Build deletion plan
        plan = self._builder.execute(policy, tracer=tracer)

        target_deleted_counts: Dict[str, int] = {}
        target_bytes_freed: Dict[str, int] = {}
        target_errors: Dict[str, List[str]] = {}
        targets_seen: List[str] = []
        all_errors: List[str] = []

        total_files_deleted = 0
        total_bytes_freed = 0

        # 4. Execute deletion items
        for item in plan.items:
            t_name = item.target_name
            if t_name not in targets_seen:
                targets_seen.append(t_name)
                target_deleted_counts[t_name] = 0
                target_bytes_freed[t_name] = 0
                target_errors[t_name] = []

            # Invariant check: verify that path doesn't violate any protected rules
            is_prohibited = False
            for rule in policy.protected_rules:
                if rule.is_violating(item.path):
                    is_prohibited = True
                    err_msg = f"Runtime safety invariant violation: {item.path} overlaps protected path {rule.path}"
                    target_errors[t_name].append(err_msg)
                    all_errors.append(err_msg)
                    if tracer.enabled:
                        tracer.log(f"[BLOCKED] {err_msg}", level="WARN")
                    break

            if is_prohibited:
                continue

            # Execute deletion with retry for locked files
            success = False
            last_err = ""
            for attempt in range(self._max_retries):
                if item.is_directory:
                    if item.strategy == DeletionStrategy.PURGE_CHILDREN and hasattr(self._fs, "purge_dir_contents"):
                        del_res = self._fs.purge_dir_contents(item.path)
                    else:
                        del_res = self._fs.remove_dir(item.path)
                else:
                    if item.strategy == DeletionStrategy.TRUNCATE and hasattr(self._fs, "truncate_file"):
                        del_res = self._fs.truncate_file(item.path)
                    else:
                        secure = (item.strategy in (DeletionStrategy.SECURE, DeletionStrategy.SHRED_NIST))
                        del_res = self._fs.remove_file(item.path, secure=secure)

                if del_res.is_ok():
                    success = True
                    break
                else:
                    last_err = del_res.unwrap_err().message
                    time.sleep(self._retry_delay)

            if success:
                target_deleted_counts[t_name] += 1
                target_bytes_freed[t_name] += item.estimated_bytes
                total_files_deleted += 1
                total_bytes_freed += item.estimated_bytes
                if tracer.enabled:
                    tracer.log_action(
                        action="DELETE",
                        path=item.path,
                        target_name=item.target_name,
                        strategy=item.strategy.value,
                        is_dir=item.is_directory,
                        size_bytes=item.estimated_bytes,
                        success=True,
                    )
            else:
                err_msg = f"Failed to delete {item.path}: {last_err}"
                target_errors[t_name].append(err_msg)
                all_errors.append(err_msg)
                if tracer.enabled:
                    tracer.log_action(
                        action="DELETE",
                        path=item.path,
                        target_name=item.target_name,
                        strategy=item.strategy.value,
                        is_dir=item.is_directory,
                        size_bytes=item.estimated_bytes,
                        success=False,
                        error=last_err,
                    )

        # 5. Compile outcome
        target_results: List[TargetResult] = []
        for t_name in targets_seen:
            errs = tuple(target_errors[t_name])
            target_results.append(
                TargetResult(
                    target_name=t_name,
                    files_deleted=target_deleted_counts[t_name],
                    bytes_freed=target_bytes_freed[t_name],
                    errors=errs,
                    success=(len(errs) == 0),
                )
            )

        duration = time.monotonic() - start_time

        if tracer.enabled:
            tracer.log_summary(
                total_files=total_files_deleted,
                total_bytes=total_bytes_freed,
                elapsed_seconds=duration,
                is_success=(len(all_errors) == 0),
                errors=all_errors,
            )

        outcome = SanitisationOutcome(
            timestamp=now,
            user_email=user_email,
            dry_run=False,
            targets_processed=tuple(targets_seen),
            target_results=tuple(target_results),
            files_deleted=total_files_deleted,
            bytes_freed=total_bytes_freed,
            errors=tuple(all_errors),
            duration_seconds=duration,
            log_file_path=tracer.log_file_path if tracer.enabled else None,
        )

        if outcome.is_success:
            self._event_bus.publish(
                SanitisationCompleted(outcome=outcome, timestamp=self._clock.now_utc())
            )
        else:
            self._event_bus.publish(
                SanitisationFailed(
                    reason=f"{len(all_errors)} errors encountered during sanitisation",
                    errors=tuple(all_errors),
                    timestamp=self._clock.now_utc(),
                )
            )

        return outcome

