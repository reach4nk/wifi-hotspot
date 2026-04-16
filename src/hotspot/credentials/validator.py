"""Credential validation utilities."""

from __future__ import annotations

import re
from typing import Optional

from hotspot.utils.logging import get_logger
from hotspot.utils.exceptions import CredentialError

logger = get_logger("validator")


class CredentialValidator:
    """Validates WiFi credentials."""

    WPA_MIN_LENGTH = 8
    WPA_MAX_LENGTH = 63
    WEP_KEY_LENGTH = 26
    SSID_MAX_LENGTH = 32
    VALID_ENCRYPTIONS = ("open", "wep", "wpa", "wpa2")
    VALID_WIFI_MODES = ("b", "g", "a", "n")
    VALID_CHANNELS = range(1, 166)

    @classmethod
    def validate_wpa_password(cls, password: str) -> bool:
        """Check if a password meets WPA requirements.

        Args:
            password: Password to validate.

        Returns:
            True if valid, False otherwise.
        """
        length = len(password)

        if length < cls.WPA_MIN_LENGTH:
            logger.error("Password too short (min %d chars): %d", cls.WPA_MIN_LENGTH, length)
            return False

        if length > cls.WPA_MAX_LENGTH:
            logger.error("Password too long (max %d chars): %d", cls.WPA_MAX_LENGTH, length)
            return False

        return True

    @classmethod
    def validate_wep_key(cls, key: str) -> bool:
        """Check if a key is valid WEP format.

        Args:
            key: Key to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not re.match(r"^[0-9a-fA-F]{26}$", key):
            logger.error("Invalid WEP key (must be 26 hex characters)")
            return False
        return True

    @classmethod
    def validate_ssid(cls, ssid: str) -> bool:
        """Check if an SSID is valid.

        Args:
            ssid: SSID to validate.

        Returns:
            True if valid, False otherwise.
        """
        length = len(ssid)

        if length < 1:
            logger.error("SSID cannot be empty")
            return False

        if length > cls.SSID_MAX_LENGTH:
            logger.error("SSID too long (max %d chars): %d", cls.SSID_MAX_LENGTH, length)
            return False

        return True

    @classmethod
    def validate_encryption_mode(cls, mode: str) -> bool:
        """Validate encryption mode string.

        Args:
            mode: Encryption mode.

        Returns:
            True if valid, False otherwise.
        """
        if mode not in cls.VALID_ENCRYPTIONS:
            logger.error("Invalid encryption mode: %s", mode)
            return False
        return True

    @classmethod
    def validate_wifi_mode(cls, mode: str) -> bool:
        """Validate WiFi mode string.

        Args:
            mode: WiFi mode (b, g, a, n).

        Returns:
            True if valid, False otherwise.
        """
        if mode not in cls.VALID_WIFI_MODES:
            logger.error("Invalid WiFi mode: %s (must be one of %s)", mode, cls.VALID_WIFI_MODES)
            return False
        return True

    @classmethod
    def validate_channel(cls, channel: int) -> bool:
        """Validate WiFi channel.

        Args:
            channel: Channel number.

        Returns:
            True if valid, False otherwise.
        """
        if channel not in cls.VALID_CHANNELS:
            logger.error("Invalid channel: %d (must be 1-165)", channel)
            return False
        return True

    @classmethod
    def validate_credentials(
        cls,
        ssid: str = "",
        password: str = "",
        encryption: str = "wpa2",
        require_ssid: bool = False
    ) -> tuple[bool, Optional[str]]:
        """Validate credentials for a hotspot.

        Args:
            ssid: SSID to validate.
            password: Password to validate.
            encryption: Encryption mode.
            require_ssid: Whether SSID is required.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not cls.validate_encryption_mode(encryption):
            return False, f"Invalid encryption mode: {encryption}"

        if require_ssid and not ssid:
            return False, "SSID is required"

        if ssid and not cls.validate_ssid(ssid):
            return False, f"Invalid SSID: {ssid}"

        if encryption == "open":
            return True, None

        if encryption == "wep":
            if not password:
                return False, "Password required for WEP encryption"
            if not cls.validate_wep_key(password):
                return False, "Invalid WEP key"
            return True, None

        if encryption in ("wpa", "wpa2"):
            if not password:
                return False, "Password required for WPA/WPA2 encryption"
            if not cls.validate_wpa_password(password):
                return False, "Invalid WPA password"
            return True, None

        return False, "Unknown encryption mode"
