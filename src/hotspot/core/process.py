"""Process management utilities."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from typing import Optional

from hotspot.utils.logging import get_logger

logger = get_logger("process")


class ProcessManager:
    """Manages system processes."""

    @staticmethod
    def is_running(pid: int) -> bool:
        """Check if a process with given PID is running.

        Args:
            pid: Process ID.

        Returns:
            True if running, False otherwise.
        """
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    @staticmethod
    def get_pids(pattern: str) -> list[int]:
        """Get PIDs of running processes matching a pattern.

        Args:
            pattern: Process name or pattern (passed to pgrep).

        Returns:
            List of PIDs.
        """
        try:
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True,
                text=True,
                check=False,
            )
            if not result.stdout.strip():
                return []
            return [int(p) for p in result.stdout.strip().split("\n") if p]
        except (ValueError, subprocess.SubprocessError) as err:
            logger.warning("Failed to get PIDs for pattern %s: %s", pattern, err)
            return []

    @staticmethod
    def kill(pid: int, timeout: int = 5) -> bool:
        """Kill a process by PID with optional timeout.

        Args:
            pid: Process ID.
            timeout: Seconds to wait before SIGKILL.

        Returns:
            True if process was killed gracefully.
        """
        if not ProcessManager.is_running(pid):
            return True

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return True

        count = 0
        while ProcessManager.is_running(pid) and count < timeout:
            time.sleep(1)
            count += 1

        if ProcessManager.is_running(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
            return False
        return True

    @staticmethod
    def kill_by_pattern(pattern: str, timeout: int = 5) -> int:
        """Kill all processes matching a pattern.

        Args:
            pattern: Process name or pattern.
            timeout: Seconds to wait before SIGKILL.

        Returns:
            Number of processes killed.
        """
        pids = ProcessManager.get_pids(pattern)
        killed = 0
        for pid in pids:
            if ProcessManager.kill(pid, timeout):
                killed += 1
        return killed
