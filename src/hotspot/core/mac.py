"""MAC address utilities and classification."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MACClass(Enum):
    """Classification of MAC address type."""

    ACTUAL = "actual"
    LOCAL = "local"
    UNKNOWN = "unknown"


@dataclass
class MACAddress:
    """Represents a MAC address with metadata."""

    address: str
    mac_class: MACClass = MACClass.UNKNOWN
    normalized: str = ""

    def __post_init__(self) -> None:
        if not self.normalized:
            self.normalized = normalize_mac(self.address)

    def __str__(self) -> str:
        return self.normalized

    def __repr__(self) -> str:
        return f"MACAddress({self.normalized}, class={self.mac_class.value})"


def normalize_mac(mac: str) -> str:
    """Normalize MAC address to uppercase with colons.

    Args:
        mac: MAC address in any common format.

    Returns:
        Normalized MAC in format AA:BB:CC:DD:EE:FF.
    """
    mac = re.sub(r"[-:]", ":", mac)
    return mac.upper()


def is_valid_mac(mac: str) -> bool:
    """Check if a string is a valid MAC address.

    Args:
        mac: MAC address string.

    Returns:
        True if valid, False otherwise.
    """
    pattern = r"^[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$"
    return bool(re.match(pattern, mac))


def is_randomized_mac(mac: str) -> bool:
    """Detect MAC address randomization.

    The second character of the first byte indicates local vs universal:
      Local (randomized): 2, 6, A, E
      Universal (real):    0, 1, 4, 5, 8, 9, C, D

    Args:
        mac: MAC address (format: AA:BB:CC:DD:EE:FF).

    Returns:
        True if randomized (local), False if real (actual).
    """
    if not is_valid_mac(mac):
        return False

    first_byte = mac.split(":")[0].upper()
    if len(first_byte) < 2:
        return False
    second_char = first_byte[1]
    return second_char in ("2", "6", "A", "E")


class MACClassifier:
    """Classifies MAC addresses based on their characteristics."""

    LOCAL_INDICATORS = frozenset(("2", "6", "A", "E"))

    @classmethod
    def classify(cls, mac: str) -> MACClass:
        """Classify a MAC address.

        Args:
            mac: MAC address string.

        Returns:
            MACClass indicating the type.
        """
        if not is_valid_mac(mac):
            return MACClass.UNKNOWN

        if is_randomized_mac(mac):
            return MACClass.LOCAL
        return MACClass.ACTUAL

    @classmethod
    def is_local(cls, mac: str) -> bool:
        """Check if MAC is locally administered (randomized).

        Args:
            mac: MAC address string.

        Returns:
            True if local/randomized.
        """
        return cls.classify(mac) == MACClass.LOCAL

    @classmethod
    def is_actual(cls, mac: str) -> bool:
        """Check if MAC is globally unique (real).

        Args:
            mac: MAC address string.

        Returns:
            True if actual/real.
        """
        return cls.classify(mac) == MACClass.ACTUAL
