"""Unit tests for hostapd service management."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from hotspot.services.hostapd import HostapdManager


class TestHostapdManager:
    """Tests for HostapdManager class."""

    def test_init(self):
        """Test initialization."""
        manager = HostapdManager()
        assert manager.config_path == "/tmp/hostapd.conf"

    def test_is_running_true(self):
        """Test hostapd is running."""
        with patch("hotspot.services.hostapd.ProcessManager.get_pids") as mock:
            mock.return_value = [12345]
            manager = HostapdManager()
            assert manager.is_running is True

    def test_is_running_false(self):
        """Test hostapd is not running."""
        with patch("hotspot.services.hostapd.ProcessManager.get_pids") as mock:
            mock.return_value = []
            manager = HostapdManager()
            assert manager.is_running is False

    def test_write_config_wpa2(self, tmp_path):
        """Test writing WPA2 config."""
        manager = HostapdManager(str(tmp_path / "hostapd.conf"))
        manager.write_config(
            iface="wlan0",
            ssid="TestNetwork",
            password="TestPass123",
            channel=6,
            wifi_mode="g",
            encryption="wpa2"
        )
        content = (tmp_path / "hostapd.conf").read_text()
        assert "interface=wlan0" in content
        assert "ssid=TestNetwork" in content
        assert "wpa=2" in content
        assert "wpa_passphrase=TestPass123" in content

    def test_write_config_open(self, tmp_path):
        """Test writing open network config."""
        manager = HostapdManager(str(tmp_path / "hostapd.conf"))
        manager.write_config(
            iface="wlan0",
            ssid="TestNetwork",
            password="",
            channel=6,
            wifi_mode="g",
            encryption="open"
        )
        content = (tmp_path / "hostapd.conf").read_text()
        assert "wpa=0" in content

    def test_write_config_wep(self, tmp_path):
        """Test writing WEP config."""
        manager = HostapdManager(str(tmp_path / "hostapd.conf"))
        manager.write_config(
            iface="wlan0",
            ssid="TestNetwork",
            password="abc123def45678901234567890ab",
            channel=6,
            wifi_mode="g",
            encryption="wep"
        )
        content = (tmp_path / "hostapd.conf").read_text()
        assert "wep_key0=" in content

    def test_write_config_wpa(self, tmp_path):
        """Test writing WPA config."""
        manager = HostapdManager(str(tmp_path / "hostapd.conf"))
        manager.write_config(
            iface="wlan0",
            ssid="TestNetwork",
            password="TestPass123",
            channel=6,
            wifi_mode="g",
            encryption="wpa"
        )
        content = (tmp_path / "hostapd.conf").read_text()
        assert "wpa=1" in content
        assert "wpa_pairwise=TKIP" in content

    def test_start_already_running(self, tmp_path):
        """Test starting hostapd when already running."""
        with patch.object(HostapdManager, "is_running", new_callable=lambda: property(lambda self: True)):
            manager = HostapdManager(str(tmp_path / "hostapd.conf"))
            manager.write_config("wlan0", "Test", "Pass123")
            result = manager.start()
            assert result is True

    def test_start_no_config(self, tmp_path):
        """Test starting hostapd without config."""
        manager = HostapdManager(str(tmp_path / "nonexistent.conf"))
        with pytest.raises(Exception):
            manager.start()

    def test_start_background(self, tmp_path):
        """Test starting hostapd in background."""
        with patch("subprocess.run") as mock_run, \
             patch.object(HostapdManager, "is_running", new_callable=lambda: property(lambda self: False)):
            mock_run.return_value = MagicMock(returncode=0)
            manager = HostapdManager(str(tmp_path / "hostapd.conf"))
            manager.write_config("wlan0", "Test", "Pass123")
            with patch("hotspot.services.hostapd.ProcessManager.get_pids") as mock_pids:
                mock_pids.return_value = [12345]
                result = manager.start()
                assert result is True

    def test_stop_running(self):
        """Test stopping running hostapd."""
        with patch("hotspot.services.hostapd.ProcessManager.get_pids") as mock_pids, \
             patch("hotspot.services.hostapd.ProcessManager.kill") as mock_kill, \
             patch("os.path.exists") as mock_exists, \
             patch("os.remove") as mock_remove:
            mock_pids.return_value = [12345]
            mock_kill.return_value = True
            mock_exists.return_value = True

            manager = HostapdManager()
            result = manager.stop()
            assert result is True

    def test_stop_not_running(self):
        """Test stopping hostapd when not running."""
        with patch("hotspot.services.hostapd.ProcessManager.get_pids") as mock_pids:
            mock_pids.return_value = []
            manager = HostapdManager()
            result = manager.stop()
            assert result is True

    def test_get_stations(self):
        """Test getting connected stations."""
        with patch("os.path.exists") as mock_exists, \
             patch("subprocess.run") as mock_run:
            mock_exists.return_value = True
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="AA:BB:CC:DD:EE:FF\n12:34:56:78:9A:BC\n",
                stderr=""
            )
            manager = HostapdManager()
            result = manager.get_stations("wlan0")
            assert len(result) == 2

    def test_get_stations_no_socket(self):
        """Test getting stations when no socket exists."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            manager = HostapdManager()
            result = manager.get_stations("wlan0")
            assert result == []
