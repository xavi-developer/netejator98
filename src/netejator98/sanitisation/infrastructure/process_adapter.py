"""ProcessPort implementation for safely closing locking processes."""

from __future__ import annotations

import os
import platform
import subprocess
from typing import List

from netejator98.sanitisation.application.ports import ProcessPort
from netejator98.sanitisation.domain.target import TargetCategory
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Ok, Result


class RealProcessPort(ProcessPort):
    """Production process controller for terminating applications locking sanitisation targets."""

    BROWSER_PROCESS_NAMES = [
        "chrome",
        "chromium",
        "firefox",
        "msedge",
        "brave",
        "opera",
        "safari",
    ]

    def terminate_processes_for_target(self, category: TargetCategory) -> Result[int, DomainError]:
        if category != TargetCategory.BROWSER_PROFILES:
            return Ok(0)

        count = 0
        current_os = platform.system().lower()

        for proc_name in self.BROWSER_PROCESS_NAMES:
            try:
                if current_os == "windows":
                    subprocess.run(
                        ["taskkill", "/F", "/IM", f"{proc_name}.exe"],
                        capture_output=True,
                        timeout=3,
                        check=False,
                    )
                else:
                    subprocess.run(
                        ["killall", "-9", proc_name],
                        capture_output=True,
                        timeout=3,
                        check=False,
                    )
                count += 1
            except Exception:
                pass

        return Ok(count)

