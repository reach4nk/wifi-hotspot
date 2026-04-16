"""Unit tests for CLI base module."""

from __future__ import annotations

import argparse
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

from hotspot.cli.base import (
    CLICommand,
    SubprocessCommand,
    create_parser,
    main,
    require_root,
    require_tool,
    require_tools,
)


class TestRequireFunctions:
    """Tests for require_* functions."""

    def test_require_tool_found(self):
        """Test require_tool when tool exists."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/python3"
            require_tool("python3")

    def test_require_tool_not_found(self):
        """Test require_tool when tool does not exist."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with pytest.raises(SystemExit):
                require_tool("nonexistent_tool")

    def test_require_tools_all_found(self):
        """Test require_tools when all tools exist."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/python3"
            require_tools("python3", "ls")

    def test_require_tools_one_missing(self):
        """Test require_tools when one tool is missing."""
        def which_side_effect(tool):
            return "/usr/bin/python3" if tool == "python3" else None

        with patch("shutil.which", side_effect=which_side_effect):
            with pytest.raises(SystemExit):
                require_tools("python3", "nonexistent")

    def test_require_root_not_root(self):
        """Test require_root exits when not root."""
        with patch.object(os, "geteuid", return_value=1):
            with pytest.raises(SystemExit):
                require_root()

    def test_require_root_is_root(self):
        """Test require_root passes when root."""
        with patch.object(os, "geteuid", return_value=0):
            require_root()


class TestCLICommand:
    """Tests for CLICommand base class."""

    def test_print_help(self):
        """Test print_help method."""
        class TestCommand(CLICommand):
            name = "test"
            help_text = "Test help text"

            def run(self, args) -> int:
                return 0

        cmd = TestCommand()
        cmd.print_help()


class TestSubprocessCommand:
    """Tests for SubprocessCommand class."""

    def test_run_success(self):
        """Test successful subprocess run."""
        class TestCommand(SubprocessCommand):
            name = "test"
            command = ["echo", "hello"]

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            cmd = TestCommand()
            result = cmd.run([])
            assert result == 0

    def test_run_called_process_error(self):
        """Test subprocess run with CalledProcessError."""
        import subprocess

        class TestCommand(SubprocessCommand):
            name = "test"
            command = ["false"]

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "false")
            cmd = TestCommand()
            result = cmd.run([])
            assert result == 1

    def test_run_other_error(self):
        """Test subprocess run with other error."""
        class TestCommand(SubprocessCommand):
            name = "test"
            command = ["echo", "hello"]

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = OSError("Test error")
            cmd = TestCommand()
            result = cmd.run([])
            assert result == 1


class TestCreateParser:
    """Tests for create_parser function."""

    def test_parser_creation(self):
        """Test parser is created correctly."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_no_command(self):
        """Test parser with no command shows help."""
        parser = create_parser()
        with patch("sys.stdout", MagicMock()) as mock_stdout:
            args = parser.parse_args([])
            assert args.command is None

    def test_parser_start_command(self):
        """Test parser with start command."""
        parser = create_parser()
        args = parser.parse_args(["start", "--ssid", "TestNet", "--password", "pass123"])
        assert args.command == "start"
        assert args.ssid == "TestNet"
        assert args.password == "pass123"
        assert args.encryption == "wpa2"

    def test_parser_stop_command(self):
        """Test parser with stop command."""
        parser = create_parser()
        args = parser.parse_args(["stop"])
        assert args.command == "stop"

    def test_parser_monitor_command(self):
        """Test parser with monitor command."""
        parser = create_parser()
        args = parser.parse_args(["monitor"])
        assert args.command == "monitor"

    def test_parser_scan_command(self):
        """Test parser with scan command."""
        parser = create_parser()
        args = parser.parse_args(["scan", "-d", "60", "-o", "out.json"])
        assert args.command == "scan"
        assert args.duration == 60
        assert args.output == "out.json"

    def test_parser_setup_command(self):
        """Test parser with setup command."""
        parser = create_parser()
        args = parser.parse_args(["setup"])
        assert args.command == "setup"

    def test_parser_teardown_command(self):
        """Test parser with teardown command."""
        parser = create_parser()
        args = parser.parse_args(["teardown"])
        assert args.command == "teardown"

    def test_parser_find_interfaces_command(self):
        """Test parser with find-interfaces command."""
        parser = create_parser()
        args = parser.parse_args(["find-interfaces"])
        assert args.command == "find-interfaces"

    def test_parser_encryption_choices(self):
        """Test parser encryption choices."""
        parser = create_parser()
        args = parser.parse_args(["start", "-e", "wpa"])
        assert args.encryption == "wpa"

    def test_parser_channel_type(self):
        """Test parser channel type."""
        parser = create_parser()
        args = parser.parse_args(["start", "-c", "11"])
        assert args.channel == 11

    def test_parser_wifi_mode_choices(self):
        """Test parser wifi mode choices."""
        parser = create_parser()
        args = parser.parse_args(["start", "-m", "n"])
        assert args.mode == "n"


class TestMain:
    """Tests for main function."""

    def test_main_no_command(self):
        """Test main with no command."""
        with patch("sys.argv", ["hotspot"]):
            with patch.object(argparse.ArgumentParser, "parse_args") as mock_parse:
                mock_parse.return_value = MagicMock(command=None)
                with patch.object(argparse.ArgumentParser, "print_help"):
                    result = main()
                    assert result == 0

    def test_main_unknown_command(self):
        """Test main with unknown command."""
        with patch("sys.argv", ["hotspot", "unknown"]):
            with patch.object(argparse.ArgumentParser, "parse_args") as mock_parse:
                mock_parse.return_value = MagicMock(command="unknown")
                result = main()
                assert result == 0

    def test_main_find_interfaces(self):
        """Test main with find-interfaces command."""
        with patch("sys.argv", ["hotspot", "find-interfaces"]):
            with patch("hotspot.cli.find_interfaces.FindInterfacesCommand") as mock_cmd:
                mock_instance = MagicMock()
                mock_instance.run.return_value = 0
                mock_cmd.return_value = mock_instance
                result = main()
                assert result == 0
                mock_instance.run.assert_called_once()

    def test_main_setup(self):
        """Test main with setup command."""
        with patch("sys.argv", ["hotspot", "setup"]):
            with patch("hotspot.cli.setup.SetupCommand") as mock_cmd:
                mock_instance = MagicMock()
                mock_instance.run.return_value = 0
                mock_cmd.return_value = mock_instance
                result = main()
                assert result == 0

    def test_main_teardown(self):
        """Test main with teardown command."""
        with patch("sys.argv", ["hotspot", "teardown"]):
            with patch("hotspot.cli.teardown.TeardownCommand") as mock_cmd:
                mock_instance = MagicMock()
                mock_instance.run.return_value = 0
                mock_cmd.return_value = mock_instance
                result = main()
                assert result == 0

    def test_main_start(self):
        """Test main with start command."""
        with patch("sys.argv", ["hotspot", "start"]):
            with patch("hotspot.cli.start.StartCommand") as mock_cmd:
                mock_instance = MagicMock()
                mock_instance.run.return_value = 0
                mock_cmd.return_value = mock_instance
                result = main()
                assert result == 0
                mock_instance.run.assert_called_once()

    def test_main_stop(self):
        """Test main with stop command."""
        with patch("sys.argv", ["hotspot", "stop"]):
            with patch("hotspot.cli.stop.StopCommand") as mock_cmd:
                mock_instance = MagicMock()
                mock_instance.run.return_value = 0
                mock_cmd.return_value = mock_instance
                result = main()
                assert result == 0

    def test_main_monitor(self):
        """Test main with monitor command."""
        with patch("sys.argv", ["hotspot", "monitor"]):
            with patch("hotspot.cli.monitor.MonitorCommand") as mock_cmd:
                mock_instance = MagicMock()
                mock_instance.run.return_value = 0
                mock_cmd.return_value = mock_instance
                result = main()
                assert result == 0

    def test_main_scan(self):
        """Test main with scan command."""
        with patch("sys.argv", ["hotspot", "scan", "-d", "60"]):
            with patch("hotspot.cli.scan.ScanCommand") as mock_cmd:
                mock_instance = MagicMock()
                mock_instance.run.return_value = 0
                mock_cmd.return_value = mock_instance
                result = main()
                assert result == 0
