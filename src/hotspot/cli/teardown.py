"""Teardown command for the hotspot CLI."""

from __future__ import annotations

from hotspot.cli.base import CLICommand, require_root
from hotspot.utils.logging import get_logger

logger = get_logger("cli.teardown")


class TeardownCommand(CLICommand):
    """Remove hotspot software."""

    name = "teardown"
    help_text = """\
Usage: hotspot teardown

WARNING: This completely removes hostapd and dnsmasq from your system.
Use only if you want to uninstall the hotspot functionality.
"""

    def run(self, args) -> int:
        """Run the teardown command.

        Args:
            args: Parsed command line arguments.

        Returns:
            Exit code.
        """
        require_root()

        import subprocess

        logger.info("Removing hostapd, dnsmasq, and configuration files...")

        result = subprocess.run(
            ["apt", "remove", "--purge", "-y", "hostapd", "dnsmasq"],
            check=False,
        )
        if result.returncode != 0:
            logger.error("Failed to remove packages")
            return 1

        logger.info("Removing automatically installed dependencies...")
        subprocess.run(["apt", "autoremove", "-y"], check=False)

        logger.info("Removed hotspot software")
        return 0
