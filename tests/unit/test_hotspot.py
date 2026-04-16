"""Unit tests for hotspot service management."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from hotspot.services.hotspot import HotspotService
from hotspot.services.hostapd import HostapdManager
from hotspot.services.dnsmasq import DnsmasqManager
from hotspot.utils.config import HotspotConfig


class TestHotspotService:
    """Tests for HotspotService class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        service = HotspotService()
        assert isinstance(service.config, HotspotConfig)
        assert service.hostapd is not None
        assert service.dnsmasq is not None

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = HotspotConfig(ssid="TestNet")
        service = HotspotService(config)
        assert service.config.ssid == "TestNet"

    def test_is_running_both(self):
        """Test is_running when both services running."""
        with patch.object(HostapdManager, "is_running", new_callable=lambda: property(lambda self: True)), \
             patch.object(DnsmasqManager, "is_running", new_callable=lambda: property(lambda self: True)):
            service = HotspotService()
            assert service.is_running is True

    def test_is_running_one(self):
        """Test is_running when one service down."""
        with patch.object(HostapdManager, "is_running", new_callable=lambda: property(lambda self: True)), \
             patch.object(DnsmasqManager, "is_running", new_callable=lambda: property(lambda self: False)):
            service = HotspotService()
            assert service.is_running is False

    def test_validate_config_valid(self):
        """Test validating valid config."""
        config = HotspotConfig(
            hotspot_iface="wlan0",
            ssid="TestNet",
            password="TestPass123"
        )
        service = HotspotService(config)
        errors = service.validate_config()
        assert errors == []

    def test_validate_config_invalid(self):
        """Test validating invalid config."""
        config = HotspotConfig()
        service = HotspotService(config)
        errors = service.validate_config()
        assert len(errors) > 0

    def test_detect_interfaces(self):
        """Test auto-detecting interfaces."""
        with patch("hotspot.core.interface.InterfaceManager.get_external_interface") as mock_ext, \
             patch("hotspot.core.interface.InterfaceManager.get_internal_interface") as mock_int:
            mock_ext.return_value = "wlan1"
            mock_int.return_value = "wlan0"

            config = HotspotConfig()
            service = HotspotService(config)
            service._detect_interfaces()

            assert service.config.hotspot_iface == "wlan1"
            assert service.config.internet_iface == "wlan0"

    def test_detect_interfaces_missing_external(self):
        """Test detecting interfaces when external missing."""
        with patch("hotspot.core.interface.InterfaceManager.get_external_interface") as mock_ext, \
             patch("hotspot.core.interface.InterfaceManager.get_internal_interface") as mock_int:
            mock_ext.return_value = ""
            mock_int.return_value = "wlan0"

            config = HotspotConfig()
            service = HotspotService(config)

            with pytest.raises(Exception) as exc_info:
                service._detect_interfaces()
            assert "No hotspot interface" in str(exc_info.value)

    def test_stop_not_started(self):
        """Test stopping when not started."""
        service = HotspotService()
        service._started = False
        service.stop()  # Should not raise

    def test_stop(self):
        """Test stopping hotspot."""
        with patch.object(HostapdManager, "stop") as mock_hostapd_stop, \
             patch.object(DnsmasqManager, "stop") as mock_dnsmasq_stop, \
             patch("hotspot.core.firewall.FirewallManager.teardown_hotspot_firewall") as mock_fw, \
             patch("hotspot.core.firewall.FirewallManager.disable_ip_forwarding") as mock_ip, \
             patch("hotspot.core.network.NetworkManager.teardown_hotspot_interface") as mock_net:
            service = HotspotService()
            service._started = True
            service.config.hotspot_iface = "wlan0"
            service.config.internet_iface = "wlan1"

            service.stop()

            mock_hostapd_stop.assert_called_once()
            mock_dnsmasq_stop.assert_called_once()
            mock_fw.assert_called_once()
            mock_ip.assert_called_once()
            mock_net.assert_called_once()

    def test_get_status(self):
        """Test getting status."""
        with patch.object(HostapdManager, "is_running", new_callable=lambda: property(lambda self: True)), \
             patch.object(DnsmasqManager, "is_running", new_callable=lambda: property(lambda self: True)):
            config = HotspotConfig(
                hotspot_iface="wlan0",
                internet_iface="wlan1",
                ssid="TestNet",
                gateway="192.168.50.1"
            )
            service = HotspotService(config)
            status = service.get_status()

            assert status["running"] is True
            assert status["ssid"] == "TestNet"
            assert status["gateway"] == "192.168.50.1"

    def test_get_connected_clients(self):
        """Test getting connected clients."""
        with patch.object(HostapdManager, "get_stations") as mock_stations, \
             patch.object(DnsmasqManager, "get_leases") as mock_leases:
            mock_stations.return_value = ["AA:BB:CC:DD:EE:FF"]
            mock_leases.return_value = [{"ip": "192.168.50.10"}]

            service = HotspotService()
            service.config.hotspot_iface = "wlan0"
            clients = service.get_connected_clients()

            assert len(clients["stations"]) == 1
            assert len(clients["dhcp_leases"]) == 1

    def test_detect_interfaces_missing_internal(self):
        """Test detecting interfaces when internal missing."""
        with patch("hotspot.core.interface.InterfaceManager.get_external_interface") as mock_ext, \
             patch("hotspot.core.interface.InterfaceManager.get_internal_interface") as mock_int:
            mock_ext.return_value = "wlan1"
            mock_int.return_value = ""

            config = HotspotConfig()
            service = HotspotService(config)

            with pytest.raises(Exception) as exc_info:
                service._detect_interfaces()
            assert "No internet interface" in str(exc_info.value)

    def test_setup_config_error(self):
        """Test setup with config error."""
        config = HotspotConfig()
        service = HotspotService(config)

        with pytest.raises(Exception) as exc_info:
            service.setup()
        assert "Invalid configuration" in str(exc_info.value)

    def test_stop_is_running(self):
        """Test stopping when services are running."""
        with patch.object(HostapdManager, "is_running", new_callable=lambda: property(lambda self: True)), \
             patch.object(DnsmasqManager, "is_running", new_callable=lambda: property(lambda self: True)), \
             patch.object(HostapdManager, "stop") as mock_hostapd_stop, \
             patch.object(DnsmasqManager, "stop") as mock_dnsmasq_stop, \
             patch("hotspot.core.firewall.FirewallManager.teardown_hotspot_firewall") as mock_fw, \
             patch("hotspot.core.firewall.FirewallManager.disable_ip_forwarding") as mock_ip, \
             patch("hotspot.core.network.NetworkManager.teardown_hotspot_interface") as mock_net:
            service = HotspotService()
            service.config.hotspot_iface = "wlan0"
            service.config.internet_iface = "wlan1"

            service.stop()

            mock_hostapd_stop.assert_called()
            mock_dnsmasq_stop.assert_called()

    def test_managed_context_manager(self):
        """Test managed context manager."""
        service = HotspotService()
        service.config.hotspot_iface = "wlan0"
        service.config.internet_iface = "wlan1"

        with patch.object(service, "start") as mock_start, \
             patch.object(service, "stop") as mock_stop:
            mock_start.side_effect = Exception("Test")
            try:
                with service.managed():
                    pass
            except Exception:
                pass
            mock_stop.assert_called()
