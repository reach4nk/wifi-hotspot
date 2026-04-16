"""Unit tests for configuration utilities."""

import json
from unittest.mock import patch, MagicMock

import pytest

from hotspot.utils.config import (
    HotspotConfig,
    DEFAULT_CHANNEL,
    DEFAULT_ENCRYPTION,
    DEFAULT_GATEWAY,
    DEFAULT_DHCP_START,
    DEFAULT_DHCP_END,
    DEFAULT_DNS,
    DEFAULT_WIFI_MODE,
    DEFAULT_LEASE_TIME,
    load_config,
    get_default_config,
)


class TestHotspotConfig:
    """Tests for HotspotConfig dataclass."""

    def test_defaults(self):
        """Test default configuration values."""
        config = HotspotConfig()
        assert config.hotspot_iface == ""
        assert config.internet_iface == ""
        assert config.ssid == ""
        assert config.password == ""
        assert config.encryption == DEFAULT_ENCRYPTION
        assert config.gateway == DEFAULT_GATEWAY
        assert config.channel == DEFAULT_CHANNEL

    def test_validation_valid_config(self):
        """Test validation with valid config."""
        config = HotspotConfig(
            hotspot_iface="wlan0",
            ssid="TestNet",
            password="password123",
            encryption="wpa2",
            channel=6
        )
        errors = config.validate()
        assert errors == []

    def test_validation_missing_hotspot_iface(self):
        """Test validation fails without hotspot interface."""
        config = HotspotConfig(ssid="TestNet")
        errors = config.validate()
        assert any("interface" in e.lower() for e in errors)

    def test_validation_invalid_encryption(self):
        """Test validation fails with invalid encryption."""
        config = HotspotConfig(
            hotspot_iface="wlan0",
            encryption="invalid"
        )
        errors = config.validate()
        assert any("encryption" in e.lower() for e in errors)

    def test_validation_invalid_channel(self):
        """Test validation fails with invalid channel."""
        config = HotspotConfig(
            hotspot_iface="wlan0",
            channel=0
        )
        errors = config.validate()
        assert any("channel" in e.lower() for e in errors)

    def test_validation_password_too_short(self):
        """Test validation fails with short password."""
        config = HotspotConfig(
            hotspot_iface="wlan0",
            password="short",
            encryption="wpa2"
        )
        errors = config.validate()
        assert any("short" in e.lower() for e in errors)

    def test_validation_ssid_too_long(self):
        """Test validation fails with long SSID."""
        config = HotspotConfig(
            hotspot_iface="wlan0",
            ssid="A" * 33
        )
        errors = config.validate()
        assert any("ssid" in e.lower() for e in errors)

    def test_validation_open_network_no_password(self):
        """Test validation passes for open network without password."""
        config = HotspotConfig(
            hotspot_iface="wlan0",
            ssid="TestNet",
            encryption="open"
        )
        errors = config.validate()
        assert errors == []

    def test_to_dict(self):
        """Test to_dict returns correct structure."""
        config = HotspotConfig(
            hotspot_iface="wlan0",
            internet_iface="wlan1",
            ssid="TestNet",
            password="secret123",
            encryption="wpa2"
        )
        result = config.to_dict()
        assert result["hotspot_iface"] == "wlan0"
        assert result["internet_iface"] == "wlan1"
        assert result["ssid"] == "TestNet"
        assert result["password"] == "***"
        assert result["encryption"] == "wpa2"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_nonexistent(self):
        """Test loading nonexistent config returns defaults."""
        config = load_config("/nonexistent/path.json")
        assert isinstance(config, HotspotConfig)

    def test_load_config_invalid_json(self, tmp_path):
        """Test loading invalid JSON returns defaults."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("invalid json {")
        config = load_config(str(config_file))
        assert isinstance(config, HotspotConfig)

    def test_load_config_with_valid_data(self, tmp_path):
        """Test loading valid JSON config."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"ssid": "TestNet", "channel": 11}')
        config = load_config(str(config_file))
        assert config.ssid == "TestNet"
        assert config.channel == 11

    def test_load_config_os_error(self, tmp_path):
        """Test loading config when file can't be read."""
        import os
        config = load_config("/nonexistent/path.json")
        assert isinstance(config, HotspotConfig)


class TestHotspotConfigValidation:
    """Additional validation tests."""

    def test_validation_invalid_wifi_mode(self):
        """Test validation with invalid wifi mode."""
        config = HotspotConfig(
            hotspot_iface="wlan0",
            wifi_mode="x"
        )
        errors = config.validate()
        assert any("mode" in e.lower() for e in errors)

    def test_validation_password_too_long(self):
        """Test validation with too long password."""
        config = HotspotConfig(
            hotspot_iface="wlan0",
            password="p" * 64,
            encryption="wpa2"
        )
        errors = config.validate()
        assert any("long" in e.lower() for e in errors)

    def test_to_dict_password_hidden(self):
        """Test password is hidden in to_dict."""
        config = HotspotConfig(password="secret")
        result = config.to_dict()
        assert result["password"] == "***"

    def test_to_dict_empty_password(self):
        """Test empty password in to_dict."""
        config = HotspotConfig(password="")
        result = config.to_dict()
        assert result["password"] == ""


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_get_default_config(self):
        """Test get_default_config returns correct type."""
        config = get_default_config()
        assert isinstance(config, HotspotConfig)
        assert config.encryption == DEFAULT_ENCRYPTION
        assert config.channel == DEFAULT_CHANNEL
