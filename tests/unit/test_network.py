"""Unit tests for network configuration."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from hotspot.core.network import NetworkManager
from hotspot.core.interface import InterfaceMode, InterfaceManager


class TestNetworkManager:
    """Tests for NetworkManager class."""

    def test_flush_addresses(self):
        """Test flushing addresses from interface."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = NetworkManager.flush_addresses("wlan0")
            assert result is True

    def test_add_address(self):
        """Test adding IP address to interface."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = NetworkManager.add_address("wlan0", "192.168.50.1", 24)
            assert result is True

    def test_add_address_failure(self):
        """Test adding IP address fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = NetworkManager.add_address("wlan0", "192.168.50.1", 24)
            assert result is False

    def test_setup_hotspot_interface(self):
        """Test setting up hotspot interface."""
        with patch.object(InterfaceManager, "set_down") as mock_down, \
             patch.object(InterfaceManager, "set_up") as mock_up:
            mock_down.return_value = True
            mock_up.return_value = True

            with patch.object(NetworkManager, "flush_addresses") as mock_flush, \
                 patch.object(NetworkManager, "add_address") as mock_add:
                mock_flush.return_value = True
                mock_add.return_value = True

                result = NetworkManager.setup_hotspot_interface("wlan0", "192.168.50.1", 24)
                assert result is True

    def test_setup_hotspot_interface_fail_down(self):
        """Test setting up hotspot interface fails when bringing down."""
        with patch.object(InterfaceManager, "set_down") as mock_down:
            mock_down.return_value = False

            with pytest.raises(Exception):
                NetworkManager.setup_hotspot_interface("wlan0", "192.168.50.1", 24)

    def test_teardown_hotspot_interface(self):
        """Test tearing down hotspot interface."""
        with patch.object(InterfaceManager, "set_down") as mock_down:
            mock_down.return_value = True

            with patch.object(NetworkManager, "flush_addresses") as mock_flush:
                mock_flush.return_value = True

                result = NetworkManager.teardown_hotspot_interface("wlan0")
                assert result is True

    def test_setup_monitor_mode_already(self):
        """Test setup monitor mode when already in monitor mode."""
        with patch.object(InterfaceManager, "get_mode") as mock_mode, \
             patch.object(InterfaceManager, "set_up") as mock_up:
            mock_mode.return_value = InterfaceMode.MONITOR
            mock_up.return_value = True

            result = NetworkManager.setup_monitor_mode("wlan0")
            assert result is True

    def test_setup_monitor_mode_success(self):
        """Test setting up monitor mode successfully."""
        with patch.object(InterfaceManager, "get_mode") as mock_mode, \
             patch.object(InterfaceManager, "set_down") as mock_down, \
             patch.object(InterfaceManager, "set_up") as mock_up, \
             patch("subprocess.run") as mock_run:
            mock_mode.return_value = InterfaceMode.MANAGED
            mock_down.return_value = True
            mock_up.return_value = True
            mock_run.return_value = MagicMock(returncode=0)

            result = NetworkManager.setup_monitor_mode("wlan0")
            assert result is True

    def test_setup_monitor_mode_failure(self):
        """Test setting up monitor mode fails."""
        with patch.object(InterfaceManager, "get_mode") as mock_mode, \
             patch.object(InterfaceManager, "set_down") as mock_down, \
             patch("subprocess.run") as mock_run:
            mock_mode.return_value = InterfaceMode.MANAGED
            mock_down.return_value = True
            mock_run.return_value = MagicMock(returncode=1)

            with pytest.raises(Exception):
                NetworkManager.setup_monitor_mode("wlan0")

    def test_teardown_monitor_mode(self):
        """Test restoring managed mode."""
        with patch.object(InterfaceManager, "set_down") as mock_down, \
             patch.object(InterfaceManager, "set_up") as mock_up, \
             patch("subprocess.run") as mock_run:
            mock_down.return_value = True
            mock_up.return_value = True
            mock_run.return_value = MagicMock(returncode=0)

            result = NetworkManager.teardown_monitor_mode("wlan0")
            assert result is True

    def test_teardown_monitor_mode_failure(self):
        """Test restoring managed mode fails."""
        with patch.object(InterfaceManager, "set_down") as mock_down, \
             patch("subprocess.run") as mock_run:
            mock_down.return_value = True
            mock_run.return_value = MagicMock(returncode=1)

            with pytest.raises(Exception):
                NetworkManager.teardown_monitor_mode("wlan0")

    def test_setup_ap_mode_already(self):
        """Test setup AP mode when already in AP mode."""
        with patch.object(InterfaceManager, "get_mode") as mock_mode:
            mock_mode.return_value = InterfaceMode.MASTER

            result = NetworkManager.setup_ap_mode("wlan0")
            assert result is True

    def test_setup_ap_mode_success(self):
        """Test setting up AP mode successfully."""
        with patch.object(InterfaceManager, "get_mode") as mock_mode, \
             patch.object(InterfaceManager, "set_down") as mock_down, \
             patch.object(InterfaceManager, "set_up") as mock_up, \
             patch("subprocess.run") as mock_run:
            mock_mode.return_value = InterfaceMode.MANAGED
            mock_down.return_value = True
            mock_up.return_value = True
            mock_run.return_value = MagicMock(returncode=0)

            result = NetworkManager.setup_ap_mode("wlan0")
            assert result is True

    def test_get_default_gateway(self):
        """Test getting default gateway."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="default via 192.168.1.1 dev wlan0 proto dhcp\n",
                stderr=""
            )
            result = NetworkManager.get_default_gateway()
            assert result == "192.168.1.1"

    def test_get_default_gateway_empty(self):
        """Test getting default gateway when none exists."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = NetworkManager.get_default_gateway()
            assert result == ""

    def test_has_internet(self):
        """Test checking internet connectivity."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = NetworkManager.has_internet("wlan0")
            assert result is True

    def test_has_internet_no_interface(self):
        """Test checking internet connectivity with no interface."""
        with patch.object(NetworkManager, "get_default_gateway") as mock_gw:
            mock_gw.return_value = ""
            result = NetworkManager.has_internet()
            assert result is False

    def test_has_internet_ping_fails(self):
        """Test checking internet when ping fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = NetworkManager.has_internet("wlan0")
            assert result is False
