"""Network interface configuration utilities."""

from __future__ import annotations

import subprocess
from typing import Optional

from hotspot.core.interface import InterfaceManager
from hotspot.utils.logging import get_logger
from hotspot.utils.exceptions import InterfaceError

logger = get_logger("network")


class NetworkManager:
    """Manages network interface configuration."""

    @staticmethod
    def flush_addresses(iface: str) -> bool:
        """Flush all IP addresses from an interface.

        Args:
            iface: Interface name.

        Returns:
            True on success.
        """
        result = subprocess.run(
            ["ip", "addr", "flush", "dev", iface],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0

    @staticmethod
    def add_address(iface: str, ip: str, netmask: int = 24) -> bool:
        """Add an IP address to an interface.

        Args:
            iface: Interface name.
            ip: IP address.
            netmask: Network mask bits.

        Returns:
            True on success.
        """
        result = subprocess.run(
            ["ip", "addr", "add", f"{ip}/{netmask}", "dev", iface],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0

    @classmethod
    def setup_hotspot_interface(
        cls, iface: str, ip: str, netmask: int = 24
    ) -> bool:
        """Configure an interface for hosting a hotspot.

        Args:
            iface: Interface name.
            ip: Static IP address.
            netmask: Network mask bits.

        Returns:
            True on success.
        """
        logger.info("Setting up hotspot interface %s with IP %s", iface, ip)

        if not InterfaceManager.set_down(iface):
            logger.error("Failed to bring interface down: %s", iface)
            raise InterfaceError(f"Failed to bring interface down: {iface}", iface)

        cls.flush_addresses(iface)

        if not cls.add_address(iface, ip, netmask):
            logger.error("Failed to assign IP %s to %s", ip, iface)
            raise InterfaceError(f"Failed to assign IP: {ip}", iface)

        if not InterfaceManager.set_up(iface):
            logger.error("Failed to bring interface up: %s", iface)
            raise InterfaceError(f"Failed to bring interface up: {iface}", iface)

        return True

    @classmethod
    def teardown_hotspot_interface(cls, iface: str) -> bool:
        """Remove configuration from a hotspot interface.

        Args:
            iface: Interface name.

        Returns:
            True on success.
        """
        logger.info("Tearing down hotspot interface %s", iface)
        cls.flush_addresses(iface)
        InterfaceManager.set_down(iface)
        return True

    @classmethod
    def setup_monitor_mode(cls, iface: str) -> bool:
        """Enable monitor mode on a wireless interface.

        Args:
            iface: Interface name.

        Returns:
            True on success.
        """
        from hotspot.core.interface import InterfaceMode

        current_mode = InterfaceManager.get_mode(iface)

        if current_mode == InterfaceMode.MONITOR:
            InterfaceManager.set_up(iface)
            return True

        logger.info("Setting up monitor mode on %s", iface)

        InterfaceManager.set_down(iface)

        result = subprocess.run(
            ["iw", "dev", iface, "set", "type", "monitor"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            logger.error("Failed to set monitor mode: %s", iface)
            raise InterfaceError(f"Failed to set monitor mode: {iface}", iface)

        InterfaceManager.set_up(iface)
        return True

    @classmethod
    def teardown_monitor_mode(cls, iface: str) -> bool:
        """Restore managed mode on a wireless interface.

        Args:
            iface: Interface name.

        Returns:
            True on success.
        """
        logger.info("Restoring managed mode on %s", iface)

        InterfaceManager.set_down(iface)

        result = subprocess.run(
            ["iw", "dev", iface, "set", "type", "managed"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            logger.error("Failed to restore managed mode: %s", iface)
            raise InterfaceError(f"Failed to restore managed mode: {iface}", iface)

        InterfaceManager.set_up(iface)
        return True

    @classmethod
    def setup_ap_mode(cls, iface: str) -> bool:
        """Enable AP/Master mode on a wireless interface.

        Args:
            iface: Interface name.

        Returns:
            True on success.
        """
        from hotspot.core.interface import InterfaceMode

        current_mode = InterfaceManager.get_mode(iface)

        if current_mode == InterfaceMode.MASTER:
            return True

        logger.info("Setting up AP mode on %s", iface)

        InterfaceManager.set_down(iface)

        result = subprocess.run(
            ["iw", "dev", iface, "set", "type", "__ap"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            logger.error("Failed to set AP mode: %s", iface)
            raise InterfaceError(f"Failed to set AP mode: {iface}", iface)

        InterfaceManager.set_up(iface)
        return True

    @staticmethod
    def get_default_gateway() -> str:
        """Get the default gateway interface.

        Returns:
            Interface name of default gateway, or empty string.
        """
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.split("\n"):
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "default" and i + 1 < len(parts):
                    for next_part in parts[i + 1 :]:
                        if next_part not in ("via", "dev"):
                            return next_part
        return ""

    @staticmethod
    def has_internet(iface: Optional[str] = None) -> bool:
        """Check if an interface has internet connectivity.

        Args:
            iface: Interface name to check. Uses default gateway if None.

        Returns:
            True if connected, False otherwise.
        """
        if iface is None:
            iface = NetworkManager.get_default_gateway()

        if not iface:
            return False

        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", "-I", iface, "8.8.8.8"],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0
