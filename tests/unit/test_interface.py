"""Unit tests for interface management."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from hotspot.core.interface import (
    InterfaceManager,
    InterfaceMode,
    WirelessInterface,
)


class TestInterfaceMode:
    """Tests for InterfaceMode enum."""

    def test_mode_values(self):
        """Test InterfaceMode enum values."""
        assert InterfaceMode.MANAGED.value == "Managed"
        assert InterfaceMode.MASTER.value == "Master"
        assert InterfaceMode.MONITOR.value == "Monitor"
        assert InterfaceMode.UNKNOWN.value == "Unknown"


class TestWirelessInterface:
    """Tests for WirelessInterface dataclass."""

    def test_default_values(self):
        """Test default values."""
        iface = WirelessInterface(name="wlan0")
        assert iface.name == "wlan0"
        assert iface.mode == InterfaceMode.UNKNOWN
        assert iface.mac == ""
        assert iface.is_up is False

    def test_custom_values(self):
        """Test custom values."""
        iface = WirelessInterface(
            name="wlan0",
            mode=InterfaceMode.MASTER,
            mac="aa:bb:cc:dd:ee:ff",
            is_up=True
        )
        assert iface.name == "wlan0"
        assert iface.mode == InterfaceMode.MASTER
        assert iface.mac == "aa:bb:cc:dd:ee:ff"
        assert iface.is_up is True

    def test_str_representation(self):
        """Test string representation."""
        iface = WirelessInterface(name="wlan0")
        assert str(iface) == "wlan0"


class TestInterfaceManager:
    """Tests for InterfaceManager class."""

    def test_get_all_wireless(self):
        """Test getting all wireless interfaces."""
        output = """Interface wlan0
        Interface wlan1
        """
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_all_wireless()
            assert "wlan0" in result
            assert "wlan1" in result

    def test_get_mode_master(self):
        """Test getting master mode."""
        output = """Interface wlan0
            type Master"""
        with patch("hotspot.core.interface.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_mode("wlan0")
            assert result == InterfaceMode.MASTER

    def test_get_mode_managed(self):
        """Test getting managed mode."""
        output = """Interface wlan0
            type Managed"""
        with patch("hotspot.core.interface.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_mode("wlan0")
            assert result == InterfaceMode.MANAGED

    def test_get_mode_monitor(self):
        """Test getting monitor mode."""
        output = """Interface wlan0
            type Monitor"""
        with patch("hotspot.core.interface.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_mode("wlan0")
            assert result == InterfaceMode.MONITOR

    def test_get_mode_unknown(self):
        """Test getting unknown mode."""
        output = """phy#0
        Interface wlan0
            type Unknown"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_mode("wlan0")
            assert result == InterfaceMode.UNKNOWN

    def test_get_mode_no_type(self):
        """Test getting mode when no type line."""
        output = """phy#0
        Interface wlan0"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_mode("wlan0")
            assert result == InterfaceMode.UNKNOWN

    def test_is_up_true(self):
        """Test interface is up."""
        with patch("hotspot.core.interface.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="2: wlan0: state UP")
            result = InterfaceManager.is_up("wlan0")
            assert result is True

    def test_is_up_false(self):
        """Test interface is down."""
        with patch("hotspot.core.interface.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="2: wlan0: state DOWN")
            result = InterfaceManager.is_up("wlan0")
            assert result is False

    def test_exists_true(self):
        """Test interface exists."""
        with patch("hotspot.core.interface.os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = InterfaceManager.exists("wlan0")
            assert result is True

    def test_exists_false(self):
        """Test interface does not exist."""
        with patch("hotspot.core.interface.os.path.exists") as mock_exists:
            mock_exists.return_value = False
            result = InterfaceManager.exists("wlan0")
            assert result is False

    def test_get_managed_interfaces(self):
        """Test getting managed interfaces."""
        output = """wlp88s0  IEEE 802.11  ESSID:"Test"
          Mode:Managed  Frequency:5.22 GHz"""
        with patch("hotspot.core.interface.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_managed_interfaces()
            assert "wlp88s0" in result

    def test_get_managed_interfaces_none(self):
        """Test getting managed interfaces when none."""
        output = """wlp88s0  IEEE 802.11  ESSID:"Test"
          Mode:Master"""
        with patch("hotspot.core.interface.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_managed_interfaces()
            assert result == []

    def test_get_master_interfaces(self):
        """Test getting master interfaces."""
        output = """wlxf4f26d1c2b2b  IEEE 802.11  ESSID:"Test"
          Mode:Master"""
        with patch("hotspot.core.interface.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_master_interfaces()
            assert "wlxf4f26d1c2b2b" in result

    def test_get_monitor_interfaces(self):
        """Test getting monitor interfaces."""
        output = """wlxf4f26d1c2b2b  IEEE 802.11  ESSID:"Test"
          Mode:Monitor"""
        with patch("hotspot.core.interface.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_monitor_interfaces()
            assert "wlxf4f26d1c2b2b" in result

    def test_get_internal_interface(self):
        """Test getting internal interface."""
        with patch.object(InterfaceManager, "get_managed_interfaces") as mock:
            mock.return_value = ["wlp88s0", "wlan0"]
            result = InterfaceManager.get_internal_interface()
            assert result == "wlp88s0"

    def test_get_internal_interface_none(self):
        """Test getting internal interface when none."""
        with patch.object(InterfaceManager, "get_managed_interfaces") as mock:
            mock.return_value = []
            result = InterfaceManager.get_internal_interface()
            assert result == ""

    def test_get_external_interface_master(self):
        """Test getting external interface in master mode."""
        output = """wlxf4f26d1c2b2b  IEEE 802.11  Mode:Master"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_external_interface()
            assert result == "wlxf4f26d1c2b2b"

    def test_get_external_interface_monitor(self):
        """Test getting external interface in monitor mode."""
        output = """wlxf4f26d1c2b2b  IEEE 802.11  Mode:Monitor"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_external_interface()
            assert result == "wlxf4f26d1c2b2b"

    def test_get_external_interface_none(self):
        """Test getting external interface when none."""
        output = """wlp88s0  IEEE 802.11  Mode:Managed"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = InterfaceManager.get_external_interface()
            assert result == ""

    def test_detect_interfaces(self):
        """Test detecting all interfaces."""
        with patch.object(InterfaceManager, "get_internal_interface") as mock_int:
            with patch.object(InterfaceManager, "get_external_interface") as mock_ext:
                with patch.object(InterfaceManager, "get_all_wireless") as mock_all:
                    mock_int.return_value = "wlp88s0"
                    mock_ext.return_value = "wlxf4f26d1c2b2b"
                    mock_all.return_value = ["wlp88s0", "wlxf4f26d1c2b2b"]
                    result = InterfaceManager.detect_interfaces()
                    assert result == ("wlp88s0", "wlxf4f26d1c2b2b", ["wlp88s0", "wlxf4f26d1c2b2b"])

    def test_wait_for_interface_found(self):
        """Test waiting for interface that exists."""
        with patch.object(InterfaceManager, "exists") as mock_exists:
            mock_exists.return_value = True
            result = InterfaceManager.wait_for_interface("wlan0", timeout=1)
            assert result is True

    def test_wait_for_interface_timeout(self):
        """Test waiting for interface that doesn't appear."""
        with patch.object(InterfaceManager, "exists") as mock_exists:
            mock_exists.return_value = False
            result = InterfaceManager.wait_for_interface("wlan0", timeout=1)
            assert result is False

    def test_set_up(self):
        """Test bringing interface up."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = InterfaceManager.set_up("wlan0")
            assert result is True

    def test_set_up_failure(self):
        """Test bringing interface up fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = InterfaceManager.set_up("wlan0")
            assert result is False

    def test_set_down(self):
        """Test bringing interface down."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = InterfaceManager.set_down("wlan0")
            assert result is True

    def test_set_down_failure(self):
        """Test bringing interface down fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = InterfaceManager.set_down("wlan0")
            assert result is False
