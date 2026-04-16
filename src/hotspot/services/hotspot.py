"""Combined hotspot service management."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from hotspot.core.network import NetworkManager
from hotspot.core.firewall import FirewallManager
from hotspot.core.interface import InterfaceManager
from hotspot.services.hostapd import HostapdManager
from hotspot.services.dnsmasq import DnsmasqManager
from hotspot.utils.logging import get_logger
from hotspot.utils.config import HotspotConfig, get_default_config
from hotspot.utils.exceptions import ServiceError, ConfigurationError

logger = get_logger("hotspot")


class HotspotService:
    """Manages the complete hotspot service lifecycle."""

    def __init__(self, config: Optional[HotspotConfig] = None) -> None:
        """Initialize hotspot service.

        Args:
            config: Hotspot configuration. Uses defaults if not provided.
        """
        self.config = config or get_default_config()
        self.hostapd = HostapdManager(self.config.hostapd_conf)
        self.dnsmasq = DnsmasqManager(self.config.dnsmasq_conf)
        self._started = False

    @property
    def is_running(self) -> bool:
        """Check if hotspot services are running.

        Returns:
            True if all services are running.
        """
        return self.hostapd.is_running and self.dnsmasq.is_running

    def validate_config(self) -> list[str]:
        """Validate service configuration.

        Returns:
            List of validation errors (empty if valid).
        """
        return self.config.validate()

    def _detect_interfaces(self) -> None:
        """Auto-detect interfaces if not specified in config."""
        if not self.config.hotspot_iface:
            self.config.hotspot_iface = InterfaceManager.get_external_interface()
            if not self.config.hotspot_iface:
                raise ConfigurationError("No hotspot interface found")

        if not self.config.internet_iface:
            self.config.internet_iface = InterfaceManager.get_internal_interface()
            if not self.config.internet_iface:
                raise ConfigurationError("No internet interface found")

    def setup(self) -> None:
        """Set up hotspot configuration without starting services.

        Raises:
            ConfigurationError: If configuration is invalid.
            ServiceError: If setup fails.
        """
        logger.info("Setting up hotspot configuration")

        errors = self.validate_config()
        if errors:
            raise ConfigurationError(f"Invalid configuration: {', '.join(errors)}")

        self._detect_interfaces()

        logger.info(
            "Hotspot interface: %s, Internet interface: %s",
            self.config.hotspot_iface,
            self.config.internet_iface
        )

        logger.info("[1/5] Configuring interface...")
        NetworkManager.setup_hotspot_interface(
            self.config.hotspot_iface,
            self.config.gateway
        )

        logger.info("[2/5] Setting up firewall...")
        FirewallManager.setup_hotspot_firewall(
            self.config.internet_iface,
            self.config.hotspot_iface
        )

        logger.info("[3/5] Writing service configs...")
        self.dnsmasq.write_config(
            self.config.hotspot_iface,
            self.config.dhcp_start,
            self.config.dhcp_end,
            self.config.dns,
            self.config.lease_time
        )
        self.hostapd.write_config(
            self.config.hotspot_iface,
            self.config.ssid,
            self.config.password,
            self.config.channel,
            self.config.wifi_mode,
            self.config.encryption
        )

        logger.info("[4/5] Starting dnsmasq...")
        self.dnsmasq.start()

        logger.info("[5/5] Starting hostapd...")
        self.hostapd.start()

        self._started = True

    def start(self) -> None:
        """Start the hotspot service.

        Raises:
            ConfigurationError: If configuration is invalid.
            ServiceError: If services fail to start.
        """
        self.setup()
        logger.info("Hotspot started successfully")

    def stop(self) -> None:
        """Stop the hotspot service."""
        logger.info("Stopping hotspot services...")

        if self._started or self.is_running:
            logger.info("[1/4] Stopping hostapd and dnsmasq...")
            self.hostapd.stop()
            self.dnsmasq.stop()

            logger.info("[2/4] Removing firewall rules...")
            if self.config.hotspot_iface and self.config.internet_iface:
                FirewallManager.teardown_hotspot_firewall(
                    self.config.internet_iface,
                    self.config.hotspot_iface
                )

            logger.info("[3/4] Disabling IP forwarding...")
            FirewallManager.disable_ip_forwarding()

            logger.info("[4/4] Cleaning up interface...")
            if self.config.hotspot_iface:
                NetworkManager.teardown_hotspot_interface(
                    self.config.hotspot_iface
                )

            self._started = False
            logger.info("Hotspot stopped")
        else:
            logger.info("Hotspot not running")

    @contextmanager
    def managed(self) -> Generator[None, None, None]:
        """Context manager for hotspot lifecycle.

        Usage:
            with hotspot_service.managed():
                # Hotspot is running
                pass
            # Hotspot is stopped

        Yields:
            None
        """
        try:
            self.start()
            yield
        finally:
            self.stop()

    def get_status(self) -> dict:
        """Get current hotspot status.

        Returns:
            Dictionary with status information.
        """
        return {
            "running": self.is_running,
            "hostapd_running": self.hostapd.is_running,
            "dnsmasq_running": self.dnsmasq.is_running,
            "hotspot_iface": self.config.hotspot_iface,
            "internet_iface": self.config.internet_iface,
            "ssid": self.config.ssid,
            "gateway": self.config.gateway,
            "channel": self.config.channel,
            "encryption": self.config.encryption,
        }

    def get_connected_clients(self) -> dict:
        """Get information about connected clients.

        Returns:
            Dictionary with client information.
        """
        stations = self.hostapd.get_stations(self.config.hotspot_iface)
        leases = self.dnsmasq.get_leases()

        return {
            "stations": stations,
            "dhcp_leases": leases,
        }
