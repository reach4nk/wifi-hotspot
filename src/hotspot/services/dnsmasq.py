"""dnsmasq service management."""

from __future__ import annotations

import os
import time
from typing import Optional

from hotspot.core.process import ProcessManager
from hotspot.utils.logging import get_logger
from hotspot.utils.exceptions import ServiceError

logger = get_logger("dnsmasq")


class DnsmasqManager:
    """Manages dnsmasq DHCP/DNS daemon."""

    DEFAULT_CONFIG = "/tmp/dnsmasq.conf"
    LEASE_FILE = "/var/lib/misc/dnsmasq.leases"

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize dnsmasq manager.

        Args:
            config_path: Path to dnsmasq configuration file.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG
        self.pid: Optional[int] = None

    @property
    def is_running(self) -> bool:
        """Check if dnsmasq is currently running.

        Returns:
            True if running, False otherwise.
        """
        pids = ProcessManager.get_pids("dnsmasq")
        return bool(pids)

    def write_config(
        self,
        iface: str,
        dhcp_start: str,
        dhcp_end: str,
        dns_server: str = "8.8.8.8",
        lease_time: str = "12h",
    ) -> str:
        """Generate dnsmasq configuration file.

        Args:
            iface: Interface for DHCP server.
            dhcp_start: First IP in DHCP range.
            dhcp_end: Last IP in DHCP range.
            dns_server: Upstream DNS server.
            lease_time: DHCP lease duration.

        Returns:
            Path to generated configuration file.
        """
        logger.info(
            "Writing dnsmasq config: iface=%s, range=%s-%s",
            iface, dhcp_start, dhcp_end
        )

        lines = [
            f"interface={iface}",
            "bind-interfaces",
            f"dhcp-range={dhcp_start},{dhcp_end},{lease_time}",
            f"server={dns_server}",
        ]

        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        return self.config_path

    def start(self) -> bool:
        """Start the dnsmasq daemon.

        Returns:
            True on success.

        Raises:
            ServiceError: If dnsmasq fails to start.
        """
        if self.is_running:
            logger.warning("dnsmasq already running")
            return True

        if not os.path.isfile(self.config_path):
            logger.error("dnsmasq config not found: %s", self.config_path)
            raise ServiceError(
                f"dnsmasq config not found: {self.config_path}",
                service="dnsmasq"
            )

        logger.info("Starting dnsmasq...")

        import subprocess

        result = subprocess.run(
            ["dnsmasq", "-C", self.config_path],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            logger.error("Failed to start dnsmasq: %s", result.stderr.decode())
            raise ServiceError("Failed to start dnsmasq", service="dnsmasq")

        time.sleep(1)
        pids = ProcessManager.get_pids(f"dnsmasq.*{self.config_path}")
        self.pid = pids[0] if pids else None

        logger.info("dnsmasq started (PID: %s)", self.pid)
        return True

    def stop(self) -> bool:
        """Stop the dnsmasq daemon.

        Returns:
            True on success.
        """
        pids = ProcessManager.get_pids("dnsmasq")

        if not pids:
            logger.info("dnsmasq not running")
            return True

        logger.info("Stopping dnsmasq (PIDs: %s)", pids)

        for pid in pids:
            ProcessManager.kill(pid, 5)

        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        self.pid = None
        return True

    def get_leases(self) -> list[dict]:
        """Get current DHCP leases.

        Returns:
            List of lease dictionaries with timestamp, mac, ip, hostname.
        """
        leases = []

        if os.path.isfile(self.LEASE_FILE):
            with open(self.LEASE_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        leases.append({
                            "timestamp": parts[0],
                            "mac": parts[1],
                            "ip": parts[2],
                            "hostname": parts[3] if len(parts) > 3 else "",
                        })

        return leases
