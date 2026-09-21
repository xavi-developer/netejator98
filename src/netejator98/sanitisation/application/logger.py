"""SanitisationTracer providing thorough logging of the sanitisation process."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import sys
from typing import List, Optional


class SanitisationTracer:
    """Records detailed step-by-step traces of target evaluations, pattern expansions,

    safety checks, and deletion attempts when thorough logging is activated in the policy.
    """

    def __init__(
        self,
        enabled: bool = False,
        log_file_path: Optional[str | Path] = None,
    ) -> None:
        self.enabled = enabled
        self.log_file_path = str(log_file_path) if log_file_path else self._resolve_default_log_path()
        self._entries: List[str] = []

        if self.enabled:
            self._ensure_log_file_ready()

    @staticmethod
    def _resolve_default_log_path() -> str:
        """Resolve a suitable default path for clean_trace.log."""
        # Try /var/lib/netejator98 or user data directory
        env_storage = os.environ.get("NETEJATOR98_STORAGE_DIR")
        if env_storage:
            candidate_dir = Path(env_storage)
        else:
            system = sys.platform.lower()
            if system.startswith("win"):
                prog_data = os.environ.get("ProgramData", "C:/ProgramData")
                candidate_dir = Path(prog_data) / "Netejator98"
            elif system.startswith("darwin"):
                candidate_dir = Path("/Library/Application Support/Netejator98")
            else:
                candidate_dir = Path("/var/lib/netejator98")

        try:
            candidate_dir.mkdir(parents=True, exist_ok=True)
            test_file = candidate_dir / ".perm_check"
            test_file.touch()
            test_file.unlink()
            return str(candidate_dir / "clean_trace.log")
        except OSError:
            # Fallback to user home .local/share/netejator98/clean_trace.log
            fallback = Path.home() / ".local" / "share" / "netejator98"
            try:
                fallback.mkdir(parents=True, exist_ok=True)
                return str(fallback / "clean_trace.log")
            except OSError:
                import tempfile
                return os.path.join(tempfile.gettempdir(), "netejator98_clean_trace.log")

    def _ensure_log_file_ready(self) -> None:
        try:
            parent = os.path.dirname(self.log_file_path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
        except OSError:
            pass

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a formatted trace message to memory, disk and stdout."""
        if not self.enabled:
            return

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        formatted = f"[{now_str}] [{level:<5}] {message}"
        self._entries.append(formatted)

        # Output to console with safe ascii
        try:
            print(f"[*] [CLEAN-TRACE] {formatted}")
        except Exception:
            pass

        # Append to log file
        try:
            with open(self.log_file_path, "a", encoding="utf-8", errors="replace") as f:
                f.write(formatted + "\n")
                f.flush()
        except OSError:
            pass

    def log_header(self, mode: str, user_email: Optional[str], platform_name: str) -> None:
        """Log the start of a sanitisation session."""
        sep = "=" * 70
        self.log(sep)
        self.log(f"STARTING CLEANING PROCESS — Mode: {mode.upper()}")
        self.log(f"Platform: {platform_name} | Session user: {user_email or 'N/A'}")
        self.log(f"Trace log file: {self.log_file_path}")
        self.log(sep)

    def log_target_eval(
        self,
        target_name: str,
        category: str,
        os_filter: str,
        enabled: bool,
        applies_to_current_os: bool,
    ) -> None:
        """Log evaluation of a target declared in the policy."""
        status = "ENABLED" if enabled else "DISABLED (Skipped)"
        os_match = "MATCHES" if applies_to_current_os else "MISMATCH (Skipped)"
        self.log(
            f"Evaluating Target '{target_name}' [{category}] (OS filter: {os_filter} -> {os_match}) -> {status}"
        )

    def log_pattern_resolution(
        self,
        target_name: str,
        pattern: str,
        resolved_base: str,
        matches: List[str],
    ) -> None:
        """Log pattern expansion and matching results."""
        self.log(
            f"  Pattern: '{pattern}' (Base: '{resolved_base}') -> Found {len(matches)} matching path(s)"
        )
        for idx, m in enumerate(matches, 1):
            self.log(f"    [{idx}/{len(matches)}] Matched candidate: {m}")

    def log_safety_check(
        self,
        candidate_path: str,
        is_safe: bool,
        violated_rule: Optional[str] = None,
    ) -> None:
        """Log invariant boundary check against protected system rules."""
        if is_safe:
            self.log(f"    [OK] Safety check passed: '{candidate_path}' is outside all protected boundaries")
        else:
            self.log(
                f"    [BLOCKED] Safety violation: '{candidate_path}' overlaps protected path '{violated_rule}'",
                level="WARN",
            )

    def log_action(
        self,
        action: str,  # 'DELETE', 'SIMULATE', 'TRUNCATE', 'PURGE'
        path: str,
        target_name: str,
        strategy: str,
        is_dir: bool,
        size_bytes: int,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log action taken on an individual path."""
        obj_type = "DIR" if is_dir else "FILE"
        result_str = "[OK] Success" if success else f"[FAIL] Error: {error}"
        self.log(
            f"  [{action.upper()}] [{obj_type}] Target: '{target_name}' (Strategy: {strategy}, Size: {size_bytes}B) -> '{path}' -> {result_str}",
            level="INFO" if success else "ERROR",
        )

    def log_summary(
        self,
        total_files: int,
        total_bytes: int,
        elapsed_seconds: float,
        is_success: bool,
        errors: List[str],
    ) -> None:
        """Log execution summary and footer."""
        sep = "=" * 70
        self.log(sep)
        status_str = "SUCCESS" if is_success else f"FAILED ({len(errors)} errors)"
        self.log(
            f"CLEANING PROCESS FINISHED — Result: {status_str} | Files: {total_files} | Bytes: {total_bytes} ({total_bytes / (1024 * 1024):.2f} MB)"
        )
        self.log(f"Duration: {elapsed_seconds:.3f} seconds")
        if errors:
            self.log("Summary of errors encountered:", level="WARN")
            for e in errors:
                self.log(f"  * {e}", level="WARN")
        self.log(sep + "\n")

