"""hostapd service management."""

from __future__ import annotations

import os
import time
from typing import Optional

from hotspot.core.process import ProcessManager
from hotspot.utils.logging import get_logger
from hotspot.utils.exceptions import ServiceError

logger = get_logger("hostapd")


class HostapdManager:
    """Manages hostapd access point daemon."""

    DEFAULT_CONFIG = "/tmp/hostapd.conf"

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize hostapd manager.

        Args:
            config_path: Path to hostapd configuration file.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG
        self.pid: Optional[int] = None

    @property
    def is_running(self) -> bool:
        """Check if hostapd is currently running.

        Returns:
            True if running, False otherwise.
        """
        pids = ProcessManager.get_pids("hostapd")
        return bool(pids)

    def write_config(
        self,
        iface: str,
        ssid: str,
        password: str = "",
        channel: int = 6,
        wifi_mode: str = "g",
        encryption: str = "wpa2",
    ) -> str:
        """Generate hostapd configuration file.

        Args:
            iface: Wireless interface for AP.
            ssid: Network name.
            password: Security password.
            channel: WiFi channel.
            wifi_mode: Hardware mode (b, g, a, n).
            encryption: Security mode (open, wep, wpa, wpa2).

        Returns:
            Path to generated configuration file.
        """
        logger.info(
            "Writing hostapd config: iface=%s, ssid=%s, channel=%d, encryption=%s",
            iface, ssid, channel, encryption
        )

        lines = [
            f"interface={iface}",
            "driver=nl80211",
            "ctrl_interface=/var/run/hostapd",
            f"ssid={ssid}",
            f"hw_mode={wifi_mode}",
            f"channel={channel}",
            "ieee80211n=1",
            "wmm_enabled=1",
            "auth_algs=1",
        ]

        if encryption == "open":
            lines.append("wpa=0")
        elif encryption == "wep":
            lines.append("wpa=0")
            lines.append("wep_default_key=0")
            lines.append(f"wep_key0={password}")
        elif encryption == "wpa":
            lines.append("wpa=1")
            lines.append(f"wpa_passphrase={password}")
            lines.append("wpa_key_mgmt=WPA-PSK")
            lines.append("wpa_pairwise=TKIP")
        elif encryption == "wpa2":
            lines.append("wpa=2")
            lines.append(f"wpa_passphrase={password}")
            lines.append("wpa_key_mgmt=WPA-PSK")
            lines.append("rsn_pairwise=CCMP")

        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        self.config_path = self.config_path
        return self.config_path

    def start(self, background: bool = True) -> bool:
        """Start the hostapd access point daemon.

        Args:
            background: Run in background.

        Returns:
            True on success.

        Raises:
            ServiceError: If hostapd fails to start.
        """
        if self.is_running:
            logger.warning("hostapd already running")
            return True

        if not os.path.isfile(self.config_path):
            logger.error("Hostapd config not found: %s", self.config_path)
            raise ServiceError(
                f"Hostapd config not found: {self.config_path}",
                service="hostapd"
            )

        logger.info("Starting hostapd...")

        import subprocess

        if background:
            result = subprocess.run(
                ["hostapd", "-B", self.config_path],
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                logger.error("Failed to start hostapd: %s", result.stderr.decode())
                raise ServiceError("Failed to start hostapd", service="hostapd")

            time.sleep(1)
            pids = ProcessManager.get_pids(f"hostapd.*{self.config_path}")
            self.pid = pids[0] if pids else None
        else:
            subprocess.run(["hostapd", self.config_path])
            self.pid = None

        logger.info("hostapd started (PID: %s)", self.pid)
        return True

    def stop(self) -> bool:
        """Stop the hostapd daemon.

        Returns:
            True on success.
        """
        pids = ProcessManager.get_pids("hostapd")

        if not pids:
            logger.info("hostapd not running")
            return True

        logger.info("Stopping hostapd (PIDs: %s)", pids)

        for pid in pids:
            ProcessManager.kill(pid, 5)

        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        self.pid = None
        return True

    def get_stations(self, iface: Optional[str] = None) -> list[str]:
        """Get list of connected stations from hostapd.

        Args:
            iface: Hostapd interface name.

        Returns:
            List of station MAC addresses.
        """
        import subprocess

        if iface is None:
            from hotspot.core.interface import InterfaceManager
            master_ifaces = InterfaceManager.get_master_interfaces()
            iface = master_ifaces[0] if master_ifaces else None

        if not iface:
            return []

        ctrl_path = "/var/run/hostapd"
        ctrl_socket = f"{ctrl_path}/{iface}"

        if os.path.exists(ctrl_socket):
            result = subprocess.run(
                ["hostapd_cli", "-p", ctrl_path, "-i", iface, "list"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return [s for s in result.stdout.strip().split("\n") if s]
        return []
