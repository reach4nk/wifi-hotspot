"""Unit tests for credential validator."""

import pytest

from hotspot.credentials.validator import CredentialValidator


class TestCredentialValidator:
    """Tests for CredentialValidator class."""

    def test_validate_wpa_password_valid(self):
        """Test valid WPA password passes."""
        assert CredentialValidator.validate_wpa_password("password123") is True
        assert CredentialValidator.validate_wpa_password("p" * 63) is True

    def test_validate_wpa_password_too_short(self):
        """Test WPA password too short fails."""
        assert CredentialValidator.validate_wpa_password("short") is False

    def test_validate_wpa_password_too_long(self):
        """Test WPA password too long fails."""
        assert CredentialValidator.validate_wpa_password("p" * 64) is False

    def test_validate_wep_key_valid(self):
        """Test valid WEP key passes."""
        assert CredentialValidator.validate_wep_key("a" * 26) is True

    def test_validate_wep_key_invalid_length(self):
        """Test WEP key wrong length fails."""
        assert CredentialValidator.validate_wep_key("a" * 25) is False
        assert CredentialValidator.validate_wep_key("a" * 27) is False

    def test_validate_wep_key_invalid_chars(self):
        """Test WEP key with invalid chars fails."""
        assert CredentialValidator.validate_wep_key("g" * 26) is False

    def test_validate_ssid_valid(self):
        """Test valid SSID passes."""
        assert CredentialValidator.validate_ssid("TestNetwork") is True
        assert CredentialValidator.validate_ssid("A" * 32) is True

    def test_validate_ssid_empty(self):
        """Test empty SSID fails."""
        assert CredentialValidator.validate_ssid("") is False

    def test_validate_ssid_too_long(self):
        """Test SSID too long fails."""
        assert CredentialValidator.validate_ssid("A" * 33) is False

    def test_validate_encryption_mode_valid(self):
        """Test valid encryption modes pass."""
        assert CredentialValidator.validate_encryption_mode("open") is True
        assert CredentialValidator.validate_encryption_mode("wep") is True
        assert CredentialValidator.validate_encryption_mode("wpa") is True
        assert CredentialValidator.validate_encryption_mode("wpa2") is True

    def test_validate_encryption_mode_invalid(self):
        """Test invalid encryption mode fails."""
        assert CredentialValidator.validate_encryption_mode("invalid") is False

    def test_validate_wifi_mode_valid(self):
        """Test valid WiFi modes pass."""
        assert CredentialValidator.validate_wifi_mode("b") is True
        assert CredentialValidator.validate_wifi_mode("g") is True
        assert CredentialValidator.validate_wifi_mode("a") is True
        assert CredentialValidator.validate_wifi_mode("n") is True

    def test_validate_wifi_mode_invalid(self):
        """Test invalid WiFi mode fails."""
        assert CredentialValidator.validate_wifi_mode("x") is False

    def test_validate_channel_valid(self):
        """Test valid channels pass."""
        assert CredentialValidator.validate_channel(1) is True
        assert CredentialValidator.validate_channel(6) is True
        assert CredentialValidator.validate_channel(11) is True

    def test_validate_channel_invalid(self):
        """Test invalid channel fails."""
        assert CredentialValidator.validate_channel(0) is False
        assert CredentialValidator.validate_channel(166) is False

    def test_validate_credentials_open_valid(self):
        """Test valid open network credentials."""
        valid, error = CredentialValidator.validate_credentials(
            ssid="TestNet",
            encryption="open"
        )
        assert valid is True
        assert error is None

    def test_validate_credentials_wpa_valid(self):
        """Test valid WPA credentials."""
        valid, error = CredentialValidator.validate_credentials(
            ssid="TestNet",
            password="password123",
            encryption="wpa2"
        )
        assert valid is True
        assert error is None

    def test_validate_credentials_wpa_missing_password(self):
        """Test WPA credentials missing password."""
        valid, error = CredentialValidator.validate_credentials(
            ssid="TestNet",
            password="",
            encryption="wpa2"
        )
        assert valid is False
        assert "password" in error.lower()

    def test_validate_credentials_require_ssid(self):
        """Test credentials requiring SSID."""
        valid, error = CredentialValidator.validate_credentials(
            ssid="",
            password="password123",
            encryption="wpa2",
            require_ssid=True
        )
        assert valid is False
        assert "SSID" in error

    def test_validate_credentials_invalid_encryption(self):
        """Test credentials with invalid encryption."""
        valid, error = CredentialValidator.validate_credentials(
            encryption="invalid"
        )
        assert valid is False
        assert "encryption" in error.lower()

    def test_validate_credentials_wep_valid(self):
        """Test valid WEP credentials."""
        valid, error = CredentialValidator.validate_credentials(
            ssid="TestNet",
            password="a" * 26,
            encryption="wep"
        )
        assert valid is True
        assert error is None

    def test_validate_credentials_wep_missing_password(self):
        """Test WEP credentials missing password."""
        valid, error = CredentialValidator.validate_credentials(
            ssid="TestNet",
            password="",
            encryption="wep"
        )
        assert valid is False
        assert "password" in error.lower()

    def test_validate_credentials_wep_invalid_key(self):
        """Test WEP credentials with invalid key."""
        valid, error = CredentialValidator.validate_credentials(
            ssid="TestNet",
            password="invalid_key",
            encryption="wep"
        )
        assert valid is False

    def test_validate_credentials_invalid_ssid(self):
        """Test credentials with invalid SSID."""
        valid, error = CredentialValidator.validate_credentials(
            ssid="A" * 33,
            encryption="open"
        )
        assert valid is False
        assert "SSID" in error

    def test_validate_credentials_wpa_invalid_password(self):
        """Test credentials with invalid WPA password."""
        valid, error = CredentialValidator.validate_credentials(
            ssid="TestNet",
            password="short",
            encryption="wpa2"
        )
        assert valid is False
