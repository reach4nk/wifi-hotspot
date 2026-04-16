"""Interface detection and management utilities."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from hotspot.core.mac import MACClassifier, MACClass
from hotspot.utils.exceptions import InterfaceError
from hotspot.utils.logging import get_logger

logger = get_logger("interface")


class InterfaceMode(Enum):
    """Wireless interface modes."""

    MANAGED = "Managed"
    MASTER = "Master"
    MONITOR = "Monitor"
    UNKNOWN = "Unknown"


@dataclass
class WirelessInterface:
    """Represents a wireless interface."""

    name: str
    mode: InterfaceMode = InterfaceMode.UNKNOWN
    mac: str = ""
    is_up: bool = False

    def __str__(self) -> str:
        return self.name


class InterfaceManager:
    """Manages network interface detection and configuration."""

    @staticmethod
    def get_all_wireless() -> list[str]:
        """List all wireless interfaces on the system.

        Returns:
            List of wireless interface names.
        """
        result = subprocess.run(
            ["iw", "dev"],
            capture_output=True,
            text=True,
            check=False,
        )
        interfaces = []
        for line in result.stdout.split("\n"):
            if line.strip().startswith("Interface"):
                parts = line.split()
                if len(parts) >= 2:
                    interfaces.append(parts[1])
        return interfaces

    @staticmethod
    def get_mode(iface: str) -> InterfaceMode:
        """Get the current mode of a wireless interface.

        Args:
            iface: Interface name.

        Returns:
            InterfaceMode value.
        """
        result = subprocess.run(
            ["iw", "dev", iface, "info"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.split("\n"):
            if "type" in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    mode_str = parts[1].capitalize()
                    try:
                        return InterfaceMode(mode_str)
                    except ValueError:
                        return InterfaceMode.UNKNOWN
        return InterfaceMode.UNKNOWN

    @staticmethod
    def is_up(iface: str) -> bool:
        """Check if an interface is up and running.

        Args:
            iface: Interface name.

        Returns:
            True if up, False otherwise.
        """
        result = subprocess.run(
            ["ip", "link", "show", iface],
            capture_output=True,
            text=True,
            check=False,
        )
        return "state UP" in result.stdout

    @staticmethod
    def exists(iface: str) -> bool:
        """Check if an interface exists.

        Args:
            iface: Interface name.

        Returns:
            True if exists, False otherwise.
        """
        return os.path.exists(f"/sys/class/net/{iface}")

    @staticmethod
    def get_managed_interfaces() -> list[str]:
        """List all interfaces in managed (client) mode.

        Returns:
            List of managed interface names.
        """
        result = subprocess.run(
            ["iwconfig"],
            capture_output=True,
            text=True,
            check=False,
        )
        interfaces = []
        lines = result.stdout.split("\n")
        for i, line in enumerate(lines):
            if "Mode:Managed" in line and i > 0:
                match = lines[i - 1].split()[0] if lines[i - 1].split() else None
                if match:
                    interfaces.append(match)
        return interfaces

    @staticmethod
    def get_master_interfaces() -> list[str]:
        """List all interfaces in master (AP) mode.

        Returns:
            List of master interface names.
        """
        result = subprocess.run(
            ["iwconfig"],
            capture_output=True,
            text=True,
            check=False,
        )
        interfaces = []
        lines = result.stdout.split("\n")
        for i, line in enumerate(lines):
            if "Mode:Master" in line and i > 0:
                match = lines[i - 1].split()[0] if lines[i - 1].split() else None
                if match:
                    interfaces.append(match)
        return interfaces

    @staticmethod
    def get_monitor_interfaces() -> list[str]:
        """List all interfaces in monitor mode.

        Returns:
            List of monitor interface names.
        """
        result = subprocess.run(
            ["iwconfig"],
            capture_output=True,
            text=True,
            check=False,
        )
        interfaces = []
        lines = result.stdout.split("\n")
        for i, line in enumerate(lines):
            if "Mode:Monitor" in line and i > 0:
                match = lines[i - 1].split()[0] if lines[i - 1].split() else None
                if match:
                    interfaces.append(match)
        return interfaces

    @classmethod
    def get_internal_interface(cls) -> str:
        """Get the WiFi interface connected to the internet (managed mode).

        Returns:
            Interface name in Managed mode, or empty string.
        """
        interfaces = cls.get_managed_interfaces()
        return interfaces[0] if interfaces else ""

    @classmethod
    def get_external_interface(cls) -> str:
        """Get the WiFi interface available for hosting (master/monitor mode).

        Returns:
            Interface name in Master or Monitor mode, or empty string.
        """
        result = subprocess.run(
            ["iwconfig"],
            capture_output=True,
            text=True,
            check=False,
        )
        lines = result.stdout.split("\n")
        current_iface = ""
        for line in lines:
            match = re.match(r"^(\S+)\s+IEEE", line)
            if match:
                current_iface = match.group(1)
            if "Mode:Master" in line or "Mode:Monitor" in line:
                if current_iface:
                    return current_iface
        return ""

    @classmethod
    def detect_interfaces(cls) -> tuple[str, str, list[str]]:
        """Detect all relevant interfaces.

        Returns:
            Tuple of (internal, external, all_wireless).
        """
        internal = cls.get_internal_interface()
        external = cls.get_external_interface()
        all_wireless = cls.get_all_wireless()
        return internal, external, all_wireless

    @classmethod
    def wait_for_interface(
        cls, iface: str, timeout: int = 10
    ) -> bool:
        """Wait for an interface to appear.

        Args:
            iface: Interface name.
            timeout: Max seconds to wait.

        Returns:
            True if interface found, False if timeout.
        """
        import time

        for _ in range(timeout):
            if cls.exists(iface):
                return True
            time.sleep(1)
        return False

    @classmethod
    def set_up(cls, iface: str) -> bool:
        """Bring an interface up.

        Args:
            iface: Interface name.

        Returns:
            True on success.
        """
        result = subprocess.run(
            ["ip", "link", "set", iface, "up"],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0

    @classmethod
    def set_down(cls, iface: str) -> bool:
        """Bring an interface down.

        Args:
            iface: Interface name.

        Returns:
            True on success.
        """
        result = subprocess.run(
            ["ip", "link", "set", iface, "down"],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0
