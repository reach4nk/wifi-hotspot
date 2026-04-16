"""Firewall and NAT management utilities."""

from __future__ import annotations

import subprocess
from typing import Optional

from hotspot.utils.logging import get_logger

logger = get_logger("firewall")


class FirewallManager:
    """Manages iptables rules and IP forwarding."""

    @staticmethod
    def enable_ip_forwarding() -> None:
        """Enable IPv4 packet forwarding in the kernel."""
        result = subprocess.run(
            ["sysctl", "-w", "net.ipv4.ip_forward=1"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            with open("/proc/sys/net/ipv4/ip_forward", "w", encoding="utf-8") as f:
                f.write("1")

    @staticmethod
    def disable_ip_forwarding() -> None:
        """Disable IPv4 packet forwarding."""
        result = subprocess.run(
            ["sysctl", "-w", "net.ipv4.ip_forward=0"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            with open("/proc/sys/net/ipv4/ip_forward", "w", encoding="utf-8") as f:
                f.write("0")

    @staticmethod
    def is_ip_forwarding_enabled() -> bool:
        """Check if IP forwarding is currently enabled.

        Returns:
            True if enabled, False otherwise.
        """
        try:
            with open("/proc/sys/net/ipv4/ip_forward", "r", encoding="utf-8") as f:
                return f.read().strip() == "1"
        except OSError:
            return False

    @classmethod
    def enable_nat(cls, external_if: str, internal_if: str) -> None:
        """Enable NAT between two interfaces.

        Args:
            external_if: Interface connected to internet.
            internal_if: Interface connected to clients.
        """
        logger.info("Enabling NAT: %s -> %s", external_if, internal_if)
        cls.enable_ip_forwarding()

        subprocess.run(
            [
                "iptables",
                "-t",
                "nat",
                "-A",
                "POSTROUTING",
                "-o",
                external_if,
                "-j",
                "MASQUERADE",
            ],
            capture_output=True,
            check=False,
        )

        subprocess.run(
            [
                "iptables",
                "-A",
                "FORWARD",
                "-i",
                external_if,
                "-o",
                internal_if,
                "-m",
                "state",
                "--state",
                "RELATED,ESTABLISHED",
                "-j",
                "ACCEPT",
            ],
            capture_output=True,
            check=False,
        )

        subprocess.run(
            [
                "iptables",
                "-A",
                "FORWARD",
                "-i",
                internal_if,
                "-o",
                external_if,
                "-j",
                "ACCEPT",
            ],
            capture_output=True,
            check=False,
        )

    @classmethod
    def disable_nat(cls, external_if: str, internal_if: str) -> None:
        """Remove NAT configuration between two interfaces.

        Args:
            external_if: External interface.
            internal_if: Internal interface.
        """
        logger.info("Disabling NAT: %s -> %s", external_if, internal_if)

        subprocess.run(
            [
                "iptables",
                "-t",
                "nat",
                "-D",
                "POSTROUTING",
                "-o",
                external_if,
                "-j",
                "MASQUERADE",
            ],
            capture_output=True,
            check=False,
        )

        subprocess.run(
            [
                "iptables",
                "-D",
                "FORWARD",
                "-i",
                external_if,
                "-o",
                internal_if,
                "-m",
                "state",
                "--state",
                "RELATED,ESTABLISHED",
                "-j",
                "ACCEPT",
            ],
            capture_output=True,
            check=False,
        )

        subprocess.run(
            [
                "iptables",
                "-D",
                "FORWARD",
                "-i",
                internal_if,
                "-o",
                external_if,
                "-j",
                "ACCEPT",
            ],
            capture_output=True,
            check=False,
        )

    @classmethod
    def setup_hotspot_firewall(
        cls, internet_if: str, hotspot_if: str
    ) -> None:
        """Configure firewall rules for a hotspot.

        Args:
            internet_if: Interface with internet (upstream).
            hotspot_if: Interface hosting the hotspot.
        """
        cls.enable_nat(internet_if, hotspot_if)

    @classmethod
    def teardown_hotspot_firewall(
        cls, internet_if: str, hotspot_if: str
    ) -> None:
        """Remove firewall rules for a hotspot.

        Args:
            internet_if: Internet interface.
            hotspot_if: Hotspot interface.
        """
        cls.disable_nat(internet_if, hotspot_if)

    @staticmethod
    def list_nat_rules() -> str:
        """Get current NAT rules.

        Returns:
            NAT rules as string.
        """
        result = subprocess.run(
            ["iptables", "-t", "nat", "-L", "-n", "-v"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout if result.returncode == 0 else "No NAT rules"

    @staticmethod
    def list_forward_rules() -> str:
        """Get current forwarding rules.

        Returns:
            Forward rules as string.
        """
        result = subprocess.run(
            ["iptables", "-L", "FORWARD", "-n", "-v"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout if result.returncode == 0 else "No forward rules"

    @staticmethod
    def count_rules() -> int:
        """Count total number of active firewall rules.

        Returns:
            Number of rules.
        """
        result = subprocess.run(
            ["iptables", "-L", "-n"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            count = result.stdout.count("Chain")
            return max(0, count - 1)
        return 0

    @staticmethod
    def flush() -> None:
        """Flush all rules in the filter table."""
        logger.warning("Flushing all iptables rules")
        subprocess.run(["iptables", "-F"], capture_output=True, check=False)
        subprocess.run(["iptables", "-X"], capture_output=True, check=False)
        subprocess.run(
            ["iptables", "-t", "nat", "-F"], capture_output=True, check=False
        )
        subprocess.run(
            ["iptables", "-t", "nat", "-X"], capture_output=True, check=False
        )

    @staticmethod
    def save(path: str = "/tmp/iptables.backup") -> bool:
        """Save current iptables rules to a file.

        Args:
            path: File path to save rules.

        Returns:
            True on success.
        """
        result = subprocess.run(
            ["iptables-save"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            with open(path, "w", encoding="utf-8") as f:
                f.write(result.stdout)
            logger.info("Rules saved to: %s", path)
            return True
        return False

    @staticmethod
    def restore(path: str = "/tmp/iptables.backup") -> bool:
        """Restore iptables rules from a file.

        Args:
            path: File path to restore from.

        Returns:
            True on success.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            result = subprocess.run(
                ["iptables-restore"],
                input=content,
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                logger.info("Rules restored from: %s", path)
                return True
        except OSError:
            pass
        return False
