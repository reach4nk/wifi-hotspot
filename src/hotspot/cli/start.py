"""Start command for the hotspot CLI."""

from __future__ import annotations

import sys
from typing import Optional

from hotspot.cli.base import CLICommand, require_root, require_tools
from hotspot.core.interface import InterfaceManager
from hotspot.services.hotspot import HotspotService
from hotspot.credentials.generator import CredentialGenerator
from hotspot.credentials.validator import CredentialValidator
from hotspot.utils.config import HotspotConfig, get_default_config
from hotspot.utils.logging import get_logger

logger = get_logger("cli.start")


class StartCommand(CLICommand):
    """Start a WiFi hotspot."""

    name = "start"
    help_text = """\
Usage: hotspot start [OPTIONS]

Start a WiFi hotspot with customizable settings.

OPTIONS:
    -i, --interface <name>       External WiFi interface (auto-detect if omitted)
    -n, --internet-if <name>      Internet interface (auto-detect if omitted)
        --ssid <name>             SSID name (random if omitted)
        --password <pass>        Password (auto-generate if omitted)
    -e, --encryption <mode>       Encryption: open|wep|wpa|wpa2 (default: wpa2)
    -g, --gateway <IP>            Gateway IP (default: 192.168.50.1)
        --dhcp-start <IP>         DHCP range start (default: 192.168.50.10)
        --dhcp-end <IP>           DHCP range end (default: 192.168.50.100)
        --dns <IP>                DNS server (default: 8.8.8.8)
    -c, --channel <num>           WiFi channel (default: 6)
    -m, --mode <mode>             WiFi mode: b|g|a|n (default: g)
    -h, --help                    Show this help message
"""

    def run(self, args) -> int:
        """Run the start command.

        Args:
            args: Parsed command line arguments.

        Returns:
            Exit code.
        """
        require_root()
        require_tools("hostapd", "dnsmasq", "iw", "ip", "sysctl")

        config = get_default_config()

        config.hotspot_iface = getattr(args, "interface", "") or ""
        config.internet_iface = getattr(args, "internet_if", "") or ""

        ssid = getattr(args, "ssid", "") or ""
        password = getattr(args, "password", "") or ""
        encryption = getattr(args, "encryption", "wpa2") or "wpa2"

        if ssid or password:
            valid, error = CredentialValidator.validate_credentials(
                ssid=ssid,
                password=password,
                encryption=encryption,
            )
            if not valid:
                logger.error("%s", error)
                return 1

        if not ssid or not password:
            creds = CredentialGenerator.generate(
                ssid=ssid or None,
                password=password or None,
                encryption=encryption,
            )
            ssid = creds.ssid
            password = creds.password

        config.ssid = ssid
        config.password = password
        config.encryption = encryption

        if getattr(args, "gateway", None):
            config.gateway = args.gateway
        if getattr(args, "dhcp_start", None):
            config.dhcp_start = args.dhcp_start
        if getattr(args, "dhcp_end", None):
            config.dhcp_end = args.dhcp_end
        if getattr(args, "dns", None):
            config.dns = args.dns
        if getattr(args, "channel", None):
            config.channel = args.channel
        if getattr(args, "mode", None):
            config.wifi_mode = args.mode

        if not config.hotspot_iface:
            config.hotspot_iface = InterfaceManager.get_external_interface()
        if not config.internet_iface:
            config.internet_iface = InterfaceManager.get_internal_interface()

        if not config.hotspot_iface:
            logger.error("No hotspot interface found")
            return 1
        if not config.internet_iface:
            logger.error("No internet interface found")
            return 1

        logger.info("Starting hotspot...")
        logger.info("  Hotspot interface: %s", config.hotspot_iface)
        logger.info("  Internet interface: %s", config.internet_iface)
        logger.info("  Gateway: %s", config.gateway)
        logger.info("  SSID: %s", config.ssid)
        if config.password:
            logger.info("  Password: %s", config.password)
        logger.info("  Encryption: %s", config.encryption)

        service = HotspotService(config)

        try:
            service.start()

            print()
            print("Hotspot started successfully.")
            print(f"  SSID: {config.ssid}")
            if config.password:
                print(f"  Password: {config.password}")
            print(f"  Gateway: {config.gateway}")
            print()

        except Exception as err:  # noqa: BLE001
            logger.error("%s", err)
            return 1

        return 0
