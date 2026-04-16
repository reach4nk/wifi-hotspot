"""Configuration management for the hotspot package."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_GATEWAY = "192.168.50.1"
DEFAULT_DHCP_START = "192.168.50.10"
DEFAULT_DHCP_END = "192.168.50.100"
DEFAULT_DNS = "8.8.8.8"
DEFAULT_CHANNEL = 6
DEFAULT_WIFI_MODE = "g"
DEFAULT_ENCRYPTION = "wpa2"
DEFAULT_LEASE_TIME = "12h"


@dataclass
class HotspotConfig:
    """Configuration for a WiFi hotspot."""

    hotspot_iface: str = ""
    internet_iface: str = ""
    ssid: str = ""
    password: str = ""
    encryption: str = DEFAULT_ENCRYPTION
    gateway: str = DEFAULT_GATEWAY
    dhcp_start: str = DEFAULT_DHCP_START
    dhcp_end: str = DEFAULT_DHCP_END
    dns: str = DEFAULT_DNS
    channel: int = DEFAULT_CHANNEL
    wifi_mode: str = DEFAULT_WIFI_MODE
    lease_time: str = DEFAULT_LEASE_TIME
    hostapd_conf: str = "/tmp/hostapd.conf"
    dnsmasq_conf: str = "/tmp/dnsmasq.conf"
    cleanup_on_exit: bool = True

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        if not self.hotspot_iface:
            errors.append("Hotspot interface not specified")

        if self.encryption not in ("open", "wep", "wpa", "wpa2"):
            errors.append(f"Invalid encryption mode: {self.encryption}")

        if self.channel < 1 or self.channel > 165:
            errors.append(f"Invalid channel: {self.channel}")

        if self.wifi_mode not in ("b", "g", "a", "n"):
            errors.append(f"Invalid WiFi mode: {self.wifi_mode}")

        if self.encryption != "open":
            if len(self.password) < 8:
                errors.append("Password too short (min 8 chars)")
            if len(self.password) > 63:
                errors.append("Password too long (max 63 chars)")

        if self.ssid and len(self.ssid) > 32:
            errors.append("SSID too long (max 32 chars)")

        return errors

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration.
        """
        return {
            "hotspot_iface": self.hotspot_iface,
            "internet_iface": self.internet_iface,
            "ssid": self.ssid,
            "password": "***" if self.password else "",
            "encryption": self.encryption,
            "gateway": self.gateway,
            "dhcp_start": self.dhcp_start,
            "dhcp_end": self.dhcp_end,
            "dns": self.dns,
            "channel": self.channel,
            "wifi_mode": self.wifi_mode,
            "lease_time": self.lease_time,
        }


def load_config(config_file: str | Path | None = None) -> HotspotConfig:
    """Load configuration from file or return default.

    Args:
        config_file: Optional path to configuration file.

    Returns:
        Loaded or default configuration.
    """
    import json

    config = HotspotConfig()

    if config_file and Path(config_file).exists():
        try:
            with open(config_file) as f:
                data = json.load(f)

            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        except (json.JSONDecodeError, OSError):
            pass

    return config


def get_default_config() -> HotspotConfig:
    """Get default hotspot configuration.

    Returns:
        Default configuration with standard settings.
    """
    return HotspotConfig()
