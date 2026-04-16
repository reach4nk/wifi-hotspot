"""Base CLI command classes."""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import Optional

from hotspot.utils.logging import get_logger, setup_logging

logger = get_logger("cli")


def require_root() -> None:
    """Ensure script is run as root."""
    if os.geteuid() != 0:
        logger.error("This script must be run as root")
        sys.exit(1)


def require_tool(tool: str) -> None:
    """Ensure a tool is available.

    Args:
        tool: Tool name.

    Raises:
        SystemExit: If tool is not found.
    """
    if shutil.which(tool) is None:
        logger.error("Required tool not found: %s", tool)
        logger.error("Run ./setup.py to install dependencies")
        sys.exit(1)


def require_tools(*tools: str) -> None:
    """Ensure all tools are available.

    Args:
        tools: Tool names.
    """
    for tool in tools:
        require_tool(tool)


class CLICommand(ABC):
    """Base class for CLI commands."""

    name: str = ""
    help_text: str = ""

    def __init__(self) -> None:
        """Initialize CLI command."""
        setup_logging()

    @abstractmethod
    def run(self, args: list[str]) -> int:
        """Run the command.

        Args:
            args: Command line arguments.

        Returns:
            Exit code.
        """

    def print_help(self) -> None:
        """Print command help."""
        print(self.help_text)


class SubprocessCommand(CLICommand):
    """Command that runs a subprocess."""

    command: list[str] = []
    description: str = ""

    def run(self, args: list[str]) -> int:
        """Run the subprocess.

        Args:
            args: Command line arguments.

        Returns:
            Exit code.
        """
        try:
            result = subprocess.run(
                self.command,
                check=True,
            )
            return result.returncode
        except subprocess.CalledProcessError as err:
            return err.returncode
        except Exception as err:  # noqa: BLE001
            logger.error("%s", err)
            return 1


def create_parser() -> "argparse.ArgumentParser":
    """Create argument parser for hotspot CLI.

    Returns:
        Configured argument parser.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="hotspot",
        description="WiFi Hotspot Management Tool",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    start_parser = subparsers.add_parser(
        "start", help="Start a WiFi hotspot"
    )
    start_parser.add_argument("-i", "--interface", help="Hotspot interface")
    start_parser.add_argument("-n", "--internet-if", help="Internet interface")
    start_parser.add_argument("--ssid", help="SSID name")
    start_parser.add_argument("--password", help="Password")
    start_parser.add_argument(
        "-e", "--encryption",
        choices=["open", "wep", "wpa", "wpa2"],
        default="wpa2",
        help="Encryption mode"
    )
    start_parser.add_argument("-g", "--gateway", help="Gateway IP")
    start_parser.add_argument("--dhcp-start", help="DHCP range start")
    start_parser.add_argument("--dhcp-end", help="DHCP range end")
    start_parser.add_argument("--dns", help="DNS server")
    start_parser.add_argument("-c", "--channel", type=int, help="WiFi channel")
    start_parser.add_argument("-m", "--mode", choices=["b", "g", "a", "n"], help="WiFi mode")

    subparsers.add_parser("stop", help="Stop the WiFi hotspot")
    subparsers.add_parser("monitor", help="Monitor connected clients")

    scan_parser = subparsers.add_parser("scan", help="Scan for probe requests")
    scan_parser.add_argument("-i", "--interface", help="WiFi interface")
    scan_parser.add_argument("-d", "--duration", type=int, help="Scan duration in seconds")
    scan_parser.add_argument("-o", "--output", help="Output JSON file")
    scan_parser.add_argument("--cleanup", action="store_true", help="Restore managed mode")

    subparsers.add_parser("setup", help="Install dependencies")
    subparsers.add_parser("teardown", help="Remove software")
    subparsers.add_parser("find-interfaces", help="Show detected interfaces")

    return parser


def main() -> int:
    """Main entry point for hotspot CLI.

    Returns:
        Exit code.
    """
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "start":
        from hotspot.cli.start import StartCommand
        cmd = StartCommand()
        return cmd.run(args)

    if args.command == "stop":
        from hotspot.cli.stop import StopCommand
        cmd = StopCommand()
        return cmd.run(args)

    if args.command == "monitor":
        from hotspot.cli.monitor import MonitorCommand
        cmd = MonitorCommand()
        return cmd.run(args)

    if args.command == "scan":
        from hotspot.cli.scan import ScanCommand
        cmd = ScanCommand()
        return cmd.run(args)

    if args.command == "setup":
        from hotspot.cli.setup import SetupCommand
        cmd = SetupCommand()
        return cmd.run(args)

    if args.command == "teardown":
        from hotspot.cli.teardown import TeardownCommand
        cmd = TeardownCommand()
        return cmd.run(args)

    if args.command == "find-interfaces":
        from hotspot.cli.find_interfaces import FindInterfacesCommand
        cmd = FindInterfacesCommand()
        return cmd.run(args)

    return 0
