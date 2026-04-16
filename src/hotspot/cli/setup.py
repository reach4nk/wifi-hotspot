"""Setup command for the hotspot CLI."""

from __future__ import annotations

from hotspot.cli.base import CLICommand, require_root, SubprocessCommand
from hotspot.utils.logging import get_logger

logger = get_logger("cli.setup")


class SetupCommand(CLICommand):
    """Install dependencies for the hotspot."""

    name = "setup"
    help_text = """\
Usage: hotspot setup

Install required software for WiFi hotspot:
  - hostapd: WiFi access point daemon
  - dnsmasq: DHCP and DNS server
  - iptables: Firewall for NAT/routing
"""

    def run(self, args) -> int:
        """Run the setup command.

        Args:
            args: Parsed command line arguments.

        Returns:
            Exit code.
        """
        require_root()

        import subprocess

        logger.info("Running apt update...")
        subprocess.run(["apt", "update"], check=False)

        logger.info("Installing hostapd, dnsmasq, iptables...")
        result = subprocess.run(
            ["apt", "install", "-y", "hostapd", "dnsmasq", "iptables"],
            check=False,
        )
        if result.returncode != 0:
            logger.error("Failed to install packages")
            return 1

        logger.info("Stopping services to prevent conflicts...")
        subprocess.run(["systemctl", "stop", "hostapd"], capture_output=True, check=False)
        subprocess.run(["systemctl", "stop", "dnsmasq"], capture_output=True, check=False)
        subprocess.run(["systemctl", "disable", "hostapd"], capture_output=True, check=False)
        subprocess.run(["systemctl", "disable", "dnsmasq"], capture_output=True, check=False)

        logger.info("Setup complete")
        return 0
