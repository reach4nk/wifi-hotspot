"""Scan command for the hotspot CLI."""

from __future__ import annotations

import sys

from hotspot.cli.base import CLICommand, require_root
from hotspot.scanner.probe import ProbeScanner
from hotspot.utils.logging import get_logger

logger = get_logger("cli.scan")


class ScanCommand(CLICommand):
    """Scan for WiFi probe requests."""

    name = "scan"
    help_text = """\
Usage: hotspot scan [OPTIONS]

Scan for WiFi probe requests and merge results in real-time.

OPTIONS:
    -i, --interface <name>    WiFi interface (auto-detect if omitted)
    -d, --duration <seconds>  Scan duration in seconds
    -o, --output <file>       Output JSON file (default: ./probes.json)
        --cleanup             Restore managed mode after scan
    -h, --help                Show this help message

Examples:
  hotspot scan -d 60              Scan for 60 seconds
  hotspot scan -i wlan1 -d 30    Scan on specific interface
  hotspot scan -o probes.json    Custom output file
"""

    def run(self, args) -> int:
        """Run the scan command.

        Args:
            args: Parsed command line arguments.

        Returns:
            Exit code.
        """
        require_root()

        missing = ProbeScanner.check_requirements()
        if missing:
            for tool in missing:
                logger.error("Required tool not found: %s", tool)
            logger.error("Run 'hotspot setup' to install dependencies")
            return 1

        interface = getattr(args, "interface", None)
        if not interface:
            logger.info("Auto-detecting interface...")
            interface = ProbeScanner.detect_interface()
            if not interface:
                logger.error("No monitor or master interface found")
                return 1

        logger.info("Using interface: %s", interface)

        duration = getattr(args, "duration", None)
        output = getattr(args, "output", None)
        restore_managed = getattr(args, "cleanup", False)

        scanner = ProbeScanner(
            interface=interface,
            duration=duration,
            output=output,
            restore_managed=restore_managed,
        )

        try:
            return scanner.run()
        finally:
            scanner.cleanup()
