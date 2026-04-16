"""Monitor command for the hotspot CLI."""

from __future__ import annotations

from hotspot.cli.base import CLICommand
from hotspot.core.interface import InterfaceManager
from hotspot.services.hostapd import HostapdManager
from hotspot.services.dnsmasq import DnsmasqManager
from hotspot.utils.logging import get_logger

logger = get_logger("cli.monitor")


class MonitorCommand(CLICommand):
    """Monitor connected clients."""

    name = "monitor"
    help_text = """\
Usage: hotspot monitor

Monitor connected clients on the hotspot.
Shows WiFi stations, DHCP leases, and ARP table.
"""

    def run(self, args) -> int:
        """Run the monitor command.

        Args:
            args: Parsed command line arguments.

        Returns:
            Exit code.
        """
        hotspot_iface = InterfaceManager.get_external_interface()

        hostapd = HostapdManager()
        dnsmasq = DnsmasqManager()
        leases = dnsmasq.get_leases()
        stations = hostapd.get_stations(hotspot_iface)

        print("========================================")
        print(" Hotspot Monitor")
        print(f" Interface: {hotspot_iface or 'N/A'}")
        print("========================================")
        print()

        print("Connected WiFi Stations:")
        print("----------------------------------------")
        if stations:
            for mac in stations:
                print(f"  MAC: {mac}")
        else:
            print("  No stations connected")

        print()
        print("DHCP Leases:")
        print("----------------------------------------")
        if leases:
            for lease in leases:
                ip = lease.get("ip", "N/A")
                mac = lease.get("mac", "N/A")
                hostname = lease.get("hostname", "N/A")
                print(f"  IP: {ip:<15} MAC: {mac:<18} Hostname: {hostname}")
        else:
            print("  No active leases")

        print()
        print("ARP Table:")
        print("----------------------------------------")

        import subprocess

        if hotspot_iface:
            result = subprocess.run(
                ["ip", "neigh", "show", "dev", hotspot_iface],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.stdout.strip():
                print(result.stdout)
            else:
                print("  No ARP entries")
        else:
            print("  No ARP entries")

        print()
        return 0
