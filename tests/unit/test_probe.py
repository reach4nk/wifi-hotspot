"""Unit tests for probe scanner."""

from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from hotspot.scanner.probe import ProbeClient, ProbeScanner
from hotspot.core.mac import MACClass


class TestProbeClient:
    """Tests for ProbeClient dataclass."""

    def test_to_dict_actual(self):
        """Test to_dict with actual MAC."""
        client = ProbeClient(
            mac="aa:bb:cc:dd:ee:ff",
            mac_class=MACClass.ACTUAL,
            ssids=["Network1", "Network2"]
        )
        result = client.to_dict()
        assert result["class"] == "actual"
        assert result["mac"] == "aa:bb:cc:dd:ee:ff"
        assert result["ssids"] == ["Network1", "Network2"]

    def test_to_dict_local(self):
        """Test to_dict with local (randomized) MAC."""
        client = ProbeClient(
            mac="2a:bb:cc:dd:ee:ff",
            mac_class=MACClass.LOCAL,
            ssids=["Network1"]
        )
        result = client.to_dict()
        assert result["class"] == "local"
        assert result["mac"] == "2a:bb:cc:dd:ee:ff"

    def test_default_ssids(self):
        """Test default empty ssids list."""
        client = ProbeClient(
            mac="aa:bb:cc:dd:ee:ff",
            mac_class=MACClass.ACTUAL
        )
        assert client.ssids == []


class TestProbeScanner:
    """Tests for ProbeScanner class."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        scanner = ProbeScanner("wlan0")
        assert scanner.interface == "wlan0"
        assert scanner.duration is None
        assert scanner.output == "./probes.json"
        assert scanner.restore_managed is False

    def test_init_custom(self):
        """Test initialization with custom values."""
        scanner = ProbeScanner(
            interface="wlan0",
            duration=60,
            output="/tmp/probes.json",
            restore_managed=True
        )
        assert scanner.interface == "wlan0"
        assert scanner.duration == 60
        assert scanner.output == "/tmp/probes.json"
        assert scanner.restore_managed is True

    def test_handle_interrupt(self):
        """Test interrupt signal handler."""
        scanner = ProbeScanner("wlan0")
        scanner._handle_interrupt(15, None)
        assert scanner.interrupted is True

    def test_setup_monitor_mode_already(self):
        """Test setup when already in monitor mode."""
        scanner = ProbeScanner("wlan0")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="type Monitor\nsome info",
                returncode=0
            )
            result = scanner._setup_monitor_mode()
            assert result is True

    def test_setup_monitor_mode_failure(self):
        """Test setup when setting monitor mode fails."""
        scanner = ProbeScanner("wlan0")
        with patch("hotspot.scanner.probe.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout="type Managed", returncode=0),
                MagicMock(returncode=0),
                MagicMock(returncode=1, stderr=b"Failed"),
            ]
            result = scanner._setup_monitor_mode()
            assert result is False

    def test_setup_monitor_mode_success(self):
        """Test successful monitor mode setup."""
        scanner = ProbeScanner("wlan0")
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout="type Managed", returncode=0),
                MagicMock(returncode=0),
                MagicMock(returncode=0),
                MagicMock(returncode=0),
            ]
            result = scanner._setup_monitor_mode()
            assert result is True

    def test_restore_managed_mode(self):
        """Test restoring managed mode."""
        scanner = ProbeScanner("wlan0")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            scanner._restore_managed_mode()
            assert mock_run.call_count == 3

    def test_load_existing_no_file(self):
        """Test loading when no existing file."""
        scanner = ProbeScanner("wlan0")
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            scanner._load_existing()
            assert scanner._clients == {}

    def test_load_existing_with_data(self):
        """Test loading existing file with data."""
        scanner = ProbeScanner("wlan0", output="/tmp/probes.json")
        data = {
            "clients": [
                {"mac": "AA:BB:CC:DD:EE:FF", "ssids": ["Network1"]},
                {"mac": "22:33:44:55:66:77", "ssids": ["Network2"]}
            ]
        }
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("builtins.open", MagicMock()):
                with patch("json.load") as mock_json:
                    mock_json.return_value = data
                    scanner._load_existing()
                    assert len(scanner._clients) == 2

    def test_load_existing_invalid_json(self):
        """Test loading with invalid JSON."""
        scanner = ProbeScanner("wlan0")
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("builtins.open", MagicMock()):
                with patch("json.load") as mock_json:
                    mock_json.side_effect = json.JSONDecodeError("err", "", 0)
                    scanner._load_existing()
                    assert scanner._clients == {}

    def test_save_results(self):
        """Test saving results to file."""
        scanner = ProbeScanner("wlan0", output="/tmp/probes.json")
        scanner._clients["aa:bb:cc:dd:ee:ff"] = ProbeClient(
            mac="aa:bb:cc:dd:ee:ff",
            mac_class=MACClass.ACTUAL,
            ssids=["Network1"]
        )
        with patch("builtins.open", MagicMock()) as mock_file:
            with patch("json.dump") as mock_json:
                scanner._save_results()
                mock_file.assert_called_once()
                mock_json.assert_called_once()

    def test_parse_csv_entries_no_file(self):
        """Test parsing when CSV file doesn't exist."""
        scanner = ProbeScanner("wlan0")
        scanner.csv_file = "/nonexistent/file.csv"
        result = scanner._parse_csv_entries()
        assert result == 0

    def test_parse_csv_entries_with_data(self):
        """Test parsing CSV with station data."""
        scanner = ProbeScanner("wlan0")
        scanner._clients = {}
        scanner._seen_macs = set()
        scanner.csv_file = "/tmp/test.csv"

        with patch("hotspot.scanner.probe.os.path.exists", return_value=True):
            with patch("hotspot.scanner.parser.CSVParser.parse_file") as mock_parse:
                mock_station = MagicMock()
                mock_station.mac = "aa:bb:cc:dd:ee:ff"
                mock_station.ssids = ["Network1", "Network2"]
                mock_parse.return_value = [mock_station]
                result = scanner._parse_csv_entries()
                assert result == 1
                assert "aa:bb:cc:dd:ee:ff" in scanner._clients

    def test_parse_csv_entries_existing_mac(self):
        """Test parsing with already seen MAC."""
        scanner = ProbeScanner("wlan0")
        scanner._clients["aa:bb:cc:dd:ee:ff"] = ProbeClient(
            mac="aa:bb:cc:dd:ee:ff",
            mac_class=MACClass.ACTUAL,
            ssids=["Network1"]
        )
        scanner._seen_macs = {"aa:bb:cc:dd:ee:ff"}
        scanner.csv_file = "/tmp/test.csv"

        with patch("hotspot.scanner.probe.os.path.exists", return_value=True):
            with patch("hotspot.scanner.parser.CSVParser.parse_file") as mock_parse:
                mock_station = MagicMock()
                mock_station.mac = "aa:bb:cc:dd:ee:ff"
                mock_station.ssids = ["Network1", "Network2"]
                mock_parse.return_value = [mock_station]
                result = scanner._parse_csv_entries()
                assert result == 1
                assert len(scanner._clients["aa:bb:cc:dd:ee:ff"].ssids) == 2

    def test_parse_csv_entries_no_ssids(self):
        """Test parsing with no SSIDs (skip)."""
        scanner = ProbeScanner("wlan0")
        scanner.csv_file = "/tmp/test.csv"

        with patch("hotspot.scanner.probe.os.path.exists", return_value=True):
            with patch("hotspot.scanner.parser.CSVParser.parse_file") as mock_parse:
                mock_station = MagicMock()
                mock_station.mac = "aa:bb:cc:dd:ee:ff"
                mock_station.ssids = []
                mock_parse.return_value = [mock_station]
                result = scanner._parse_csv_entries()
                assert result == 0

    def test_start_airodump_success(self):
        """Test successful airodump start."""
        scanner = ProbeScanner("wlan0")
        with patch("hotspot.scanner.probe.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.poll.return_value = None
            mock_popen.return_value = mock_proc
            with patch("hotspot.scanner.probe.time.sleep"):
                with patch("hotspot.scanner.probe.Path.glob"):
                    result = scanner._start_airodump()
                    assert result is True
                    assert scanner.airodump_proc is not None

    def test_start_airodump_process_died(self):
        """Test when airodump dies immediately."""
        scanner = ProbeScanner("wlan0")
        with patch("hotspot.scanner.probe.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.poll.return_value = 1
            mock_popen.return_value = mock_proc
            with patch("hotspot.scanner.probe.time.sleep"):
                with patch("hotspot.scanner.probe.Path.glob"):
                    result = scanner._start_airodump()
                    assert result is False

    def test_start_airodump_oserror(self):
        """Test when airodump fails to start."""
        scanner = ProbeScanner("wlan0")
        with patch("hotspot.scanner.probe.subprocess.Popen") as mock_popen:
            mock_popen.side_effect = OSError("Failed to start")
            with patch("hotspot.scanner.probe.Path.glob"):
                result = scanner._start_airodump()
                assert result is False

    def test_monitor_loop_duration(self):
        """Test monitor loop with duration."""
        scanner = ProbeScanner("wlan0", duration=2)
        scanner.airodump_proc = MagicMock()
        scanner.airodump_proc.poll.return_value = None

        with patch.object(scanner, "_parse_csv_entries", return_value=0):
            with patch("time.sleep"):
                scanner._monitor_loop()

    def test_monitor_loop_interrupted(self):
        """Test monitor loop interrupted."""
        scanner = ProbeScanner("wlan0")
        scanner.airodump_proc = MagicMock()
        scanner.airodump_proc.poll.return_value = None
        scanner.interrupted = True

        with patch.object(scanner, "_parse_csv_entries", return_value=0):
            with patch("time.sleep"):
                scanner._monitor_loop()

    def test_monitor_loop_process_dead(self):
        """Test monitor loop when process dies."""
        scanner = ProbeScanner("wlan0")
        scanner.airodump_proc = MagicMock()
        scanner.airodump_proc.poll.return_value = 1

        scanner._monitor_loop()

    def test_cleanup_with_airodump(self):
        """Test cleanup with running airodump."""
        scanner = ProbeScanner("wlan0")
        scanner.airodump_proc = MagicMock()
        scanner.airodump_proc.poll.return_value = None
        scanner._clients["aa:bb:cc:dd:ee:ff"] = ProbeClient(
            mac="aa:bb:cc:dd:ee:ff",
            mac_class=MACClass.ACTUAL,
            ssids=["Network1"]
        )

        with patch.object(scanner, "_parse_csv_entries", return_value=0):
            with patch.object(scanner, "_save_results"):
                with patch("hotspot.scanner.probe.Path.glob"):
                    scanner.cleanup()
                    scanner.airodump_proc.terminate.assert_called_once()

    def test_cleanup_kill_on_timeout(self):
        """Test cleanup kills on timeout."""
        import subprocess

        scanner = ProbeScanner("wlan0")
        scanner.airodump_proc = MagicMock()
        scanner.airodump_proc.poll.return_value = None
        scanner.airodump_proc.wait.side_effect = subprocess.TimeoutExpired("cmd", 5)

        with patch.object(scanner, "_parse_csv_entries", return_value=0):
            with patch.object(scanner, "_save_results"):
                with patch("hotspot.scanner.probe.Path.glob"):
                    scanner.cleanup()
                    scanner.airodump_proc.kill.assert_called_once()

    def test_cleanup_with_restore(self):
        """Test cleanup with restore managed mode."""
        scanner = ProbeScanner("wlan0", restore_managed=True)
        scanner._clients = {}

        with patch.object(scanner, "_restore_managed_mode") as mock_restore:
            scanner.cleanup()
            mock_restore.assert_called_once()

    def test_cleanup_no_restore(self):
        """Test cleanup without restore managed mode."""
        scanner = ProbeScanner("wlan0", restore_managed=False)
        scanner._clients = {}

        with patch.object(scanner, "_restore_managed_mode") as mock_restore:
            scanner.cleanup()
            mock_restore.assert_not_called()

    def test_detect_interface_master(self):
        """Test detecting interface in master mode."""
        output = """wlxf4f26d1c2b2b  IEEE 802.11  Mode:Master"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = ProbeScanner.detect_interface()
            assert result == "wlxf4f26d1c2b2b"

    def test_detect_interface_monitor(self):
        """Test detecting interface in monitor mode."""
        output = """wlxf4f26d1c2b2b  IEEE 802.11  Mode:Monitor"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = ProbeScanner.detect_interface()
            assert result == "wlxf4f26d1c2b2b"

    def test_detect_interface_none(self):
        """Test detecting when no suitable interface."""
        output = """wlp88s0  IEEE 802.11  Mode:Managed"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = ProbeScanner.detect_interface()
            assert result is None

    def test_check_requirements_all_present(self):
        """Test check requirements when all tools present."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = ProbeScanner.check_requirements()
            assert result == []

    def test_check_requirements_missing(self):
        """Test check requirements with missing tools."""
        def which_side_effect(cmd, *args, **kwargs):
            returncode = 0 if cmd[1] == "iw" else 1
            return MagicMock(returncode=returncode)

        with patch("hotspot.scanner.probe.subprocess.run", side_effect=which_side_effect):
            result = ProbeScanner.check_requirements()
            assert "airodump-ng" in result

    def test_run_success(self):
        """Test successful run."""
        scanner = ProbeScanner("wlan0")

        with patch.object(scanner, "_load_existing"):
            with patch.object(scanner, "_setup_monitor_mode", return_value=True):
                with patch.object(scanner, "_start_airodump", return_value=True):
                    with patch.object(scanner, "_monitor_loop"):
                        result = scanner.run()
                        assert result == 0

    def test_run_setup_failure(self):
        """Test run when setup fails."""
        scanner = ProbeScanner("wlan0")

        with patch.object(scanner, "_load_existing"):
            with patch.object(scanner, "_setup_monitor_mode", return_value=False):
                result = scanner.run()
                assert result == 1

    def test_run_airodump_failure(self):
        """Test run when airodump fails."""
        scanner = ProbeScanner("wlan0")

        with patch.object(scanner, "_load_existing"):
            with patch.object(scanner, "_setup_monitor_mode", return_value=True):
                with patch.object(scanner, "_start_airodump", return_value=False):
                    result = scanner.run()
                    assert result == 1
