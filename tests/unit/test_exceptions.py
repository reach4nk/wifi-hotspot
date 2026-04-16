"""Unit tests for exception classes."""

from __future__ import annotations

import pytest

from hotspot.utils.exceptions import (
    HotspotError,
    InterfaceError,
    ServiceError,
    ConfigurationError,
    ValidationError,
    CredentialError,
)


class TestHotspotError:
    """Tests for HotspotError exception."""

    def test_message(self):
        """Test exception message."""
        err = HotspotError("Test error")
        assert err.message == "Test error"
        assert str(err) == "Test error"


class TestInterfaceError:
    """Tests for InterfaceError exception."""

    def test_with_interface(self):
        """Test with interface name."""
        err = InterfaceError("Interface error", interface="wlan0")
        assert err.interface == "wlan0"
        assert err.message == "Interface error"

    def test_without_interface(self):
        """Test without interface name."""
        err = InterfaceError("Interface error")
        assert err.interface is None


class TestServiceError:
    """Tests for ServiceError exception."""

    def test_with_service(self):
        """Test with service name."""
        err = ServiceError("Service error", service="hostapd")
        assert err.service == "hostapd"
        assert err.message == "Service error"

    def test_without_service(self):
        """Test without service name."""
        err = ServiceError("Service error")
        assert err.service is None


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_message(self):
        """Test exception message."""
        err = ConfigurationError("Config error")
        assert err.message == "Config error"


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_message(self):
        """Test exception message."""
        err = ValidationError("Validation error")
        assert err.message == "Validation error"


class TestCredentialError:
    """Tests for CredentialError exception."""

    def test_message(self):
        """Test exception message."""
        err = CredentialError("Credential error")
        assert err.message == "Credential error"
