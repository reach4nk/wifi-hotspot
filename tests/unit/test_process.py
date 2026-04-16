"""Unit tests for process management."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from hotspot.core.process import ProcessManager


class TestProcessManager:
    """Tests for ProcessManager class."""

    def test_is_running_true(self):
        """Test is_running when process exists."""
        with patch("os.kill") as mock_kill:
            mock_kill.return_value = None
            result = ProcessManager.is_running(12345)
            assert result is True

    def test_is_running_false(self):
        """Test is_running when process doesn't exist."""
        with patch("os.kill") as mock_kill:
            mock_kill.side_effect = OSError("No such process")
            result = ProcessManager.is_running(99999)
            assert result is False

    def test_get_pids_found(self):
        """Test get_pids when processes found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="12345\n67890\n",
                returncode=0
            )
            result = ProcessManager.get_pids("hostapd")
            assert result == [12345, 67890]

    def test_get_pids_empty(self):
        """Test get_pids when no processes found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            result = ProcessManager.get_pids("nonexistent")
            assert result == []

    def test_get_pids_value_error(self):
        """Test get_pids with invalid PID in output."""
        with patch("hotspot.core.process.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="12345\ninvalid\n",
                returncode=0
            )
            result = ProcessManager.get_pids("hostapd")
            assert result == []

    def test_get_pids_subprocess_error(self):
        """Test get_pids when subprocess fails."""
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.SubprocessError("Failed")
            result = ProcessManager.get_pids("hostapd")
            assert result == []

    def test_kill_not_running(self):
        """Test kill when process not running."""
        with patch.object(ProcessManager, "is_running", return_value=False):
            result = ProcessManager.kill(99999)
            assert result is True

    def test_kill_success(self):
        """Test successful kill with SIGTERM."""
        with patch("hotspot.core.process.ProcessManager.is_running") as mock_running:
            mock_running.side_effect = [True, True, False, False]
            with patch("os.kill") as mock_kill:
                mock_kill.return_value = None
                result = ProcessManager.kill(12345, timeout=2)
                assert result is True
                mock_kill.assert_called()

    def test_kill_uses_sigkill_on_timeout(self):
        """Test kill uses SIGKILL when SIGTERM times out."""
        with patch("hotspot.core.process.ProcessManager.is_running", return_value=True):
            with patch("os.kill") as mock_kill:
                mock_kill.return_value = None
                result = ProcessManager.kill(12345, timeout=1)
                assert result is False
                assert mock_kill.call_count == 2

    def test_kill_oserror_on_sigterm(self):
        """Test kill handles OSError on SIGTERM."""
        with patch("hotspot.core.process.ProcessManager.is_running", return_value=False):
            with patch("os.kill") as mock_kill:
                mock_kill.side_effect = OSError("Already dead")
                result = ProcessManager.kill(12345)
                assert result is True

    def test_kill_oserror_on_sigkill(self):
        """Test kill handles OSError on SIGKILL."""
        with patch("hotspot.core.process.ProcessManager.is_running", return_value=True):
            with patch("os.kill") as mock_kill:
                mock_kill.side_effect = [None, OSError("Already dead")]
                result = ProcessManager.kill(12345, timeout=1)
                assert result is False

    def test_kill_by_pattern(self):
        """Test kill_by_pattern."""
        with patch.object(ProcessManager, "get_pids", return_value=[12345, 67890]):
            with patch.object(ProcessManager, "kill", return_value=True):
                result = ProcessManager.kill_by_pattern("hostapd")
                assert result == 2

    def test_kill_by_pattern_partial(self):
        """Test kill_by_pattern when some processes fail to kill."""
        with patch.object(ProcessManager, "get_pids", return_value=[12345, 67890]):
            with patch.object(ProcessManager, "kill") as mock_kill:
                mock_kill.side_effect = [True, False]
                result = ProcessManager.kill_by_pattern("hostapd")
                assert result == 1

    def test_kill_by_pattern_none_found(self):
        """Test kill_by_pattern when no processes found."""
        with patch.object(ProcessManager, "get_pids", return_value=[]):
            result = ProcessManager.kill_by_pattern("nonexistent")
            assert result == 0
