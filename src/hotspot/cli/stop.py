"""Stop command for the hotspot CLI."""

from __future__ import annotations

from hotspot.cli.base import CLICommand, require_root
from hotspot.services.hotspot import HotspotService
from hotspot.utils.logging import get_logger

logger = get_logger("cli.stop")


class StopCommand(CLICommand):
    """Stop the WiFi hotspot."""

    name = "stop"
    help_text = """\
Usage: hotspot stop

Stop the WiFi hotspot and clean up resources.
"""

    def run(self, args) -> int:
        """Run the stop command.

        Args:
            args: Parsed command line arguments.

        Returns:
            Exit code.
        """
        require_root()

        from hotspot.core.interface import InterfaceManager

        hotspot_iface = InterfaceManager.get_external_interface()

        logger.info("Stopping hotspot services...")

        logger.info("[1/4] Stopping hostapd and dnsmasq...")
        from hotspot.services.hostapd import HostapdManager
        from hotspot.services.dnsmasq import DnsmasqManager

        hostapd = HostapdManager()
        dnsmasq = DnsmasqManager()
        hostapd.stop()
        dnsmasq.stop()

        logger.info("[2/4] Removing firewall rules...")
        if hotspot_iface:
            internet_iface = InterfaceManager.get_internal_interface()
            if internet_iface:
                from hotspot.core.firewall import FirewallManager
                FirewallManager.teardown_hotspot_firewall(
                    internet_iface,
                    hotspot_iface
                )

        logger.info("[3/4] Disabling IP forwarding...")
        from hotspot.core.firewall import FirewallManager
        FirewallManager.disable_ip_forwarding()

        logger.info("[4/4] Cleaning up interface...")
        if hotspot_iface:
            from hotspot.core.network import NetworkManager
            NetworkManager.teardown_hotspot_interface(hotspot_iface)

        logger.info("Hotspot stopped")
        return 0
