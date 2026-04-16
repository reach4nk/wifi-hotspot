"""Unit tests for dnsmasq service management."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from hotspot.services.dnsmasq import DnsmasqManager


class TestDnsmasqManager:
    """Tests for DnsmasqManager class."""

    def test_init(self):
        """Test initialization."""
        manager = DnsmasqManager()
        assert manager.config_path == "/tmp/dnsmasq.conf"
        assert manager.LEASE_FILE == "/var/lib/misc/dnsmasq.leases"

    def test_is_running_true(self):
        """Test dnsmasq is running."""
        with patch("hotspot.services.dnsmasq.ProcessManager.get_pids") as mock:
            mock.return_value = [12345]
            manager = DnsmasqManager()
            assert manager.is_running is True

    def test_is_running_false(self):
        """Test dnsmasq is not running."""
        with patch("hotspot.services.dnsmasq.ProcessManager.get_pids") as mock:
            mock.return_value = []
            manager = DnsmasqManager()
            assert manager.is_running is False

    def test_write_config(self, tmp_path):
        """Test writing dnsmasq config."""
        manager = DnsmasqManager(str(tmp_path / "dnsmasq.conf"))
        manager.write_config(
            iface="wlan0",
            dhcp_start="192.168.50.10",
            dhcp_end="192.168.50.100",
            dns_server="8.8.8.8",
            lease_time="12h"
        )
        content = (tmp_path / "dnsmasq.conf").read_text()
        assert "interface=wlan0" in content
        assert "192.168.50.10,192.168.50.100,12h" in content
        assert "server=8.8.8.8" in content

    def test_start_already_running(self, tmp_path):
        """Test starting dnsmasq when already running."""
        with patch.object(DnsmasqManager, "is_running", new_callable=lambda: property(lambda self: True)):
            manager = DnsmasqManager(str(tmp_path / "dnsmasq.conf"))
            manager.write_config("wlan0", "192.168.50.10", "192.168.50.100")
            result = manager.start()
            assert result is True

    def test_start_no_config(self, tmp_path):
        """Test starting dnsmasq without config."""
        manager = DnsmasqManager(str(tmp_path / "nonexistent.conf"))
        with pytest.raises(Exception):
            manager.start()

    def test_start_success(self, tmp_path):
        """Test starting dnsmasq successfully."""
        with patch("subprocess.run") as mock_run, \
             patch.object(DnsmasqManager, "is_running", new_callable=lambda: property(lambda self: False)):
            mock_run.return_value = MagicMock(returncode=0)
            manager = DnsmasqManager(str(tmp_path / "dnsmasq.conf"))
            manager.write_config("wlan0", "192.168.50.10", "192.168.50.100")
            with patch("hotspot.services.dnsmasq.ProcessManager.get_pids") as mock_pids:
                mock_pids.return_value = [12345]
                result = manager.start()
                assert result is True

    def test_stop_running(self):
        """Test stopping running dnsmasq."""
        with patch("hotspot.services.dnsmasq.ProcessManager.get_pids") as mock_pids, \
             patch("hotspot.services.dnsmasq.ProcessManager.kill") as mock_kill, \
             patch("os.path.exists") as mock_exists, \
             patch("os.remove") as mock_remove:
            mock_pids.return_value = [12345]
            mock_kill.return_value = True
            mock_exists.return_value = True

            manager = DnsmasqManager()
            result = manager.stop()
            assert result is True

    def test_stop_not_running(self):
        """Test stopping dnsmasq when not running."""
        with patch("hotspot.services.dnsmasq.ProcessManager.get_pids") as mock_pids:
            mock_pids.return_value = []
            manager = DnsmasqManager()
            result = manager.stop()
            assert result is True

    def test_get_leases(self, tmp_path):
        """Test getting DHCP leases."""
        lease_file = tmp_path / "dnsmasq.leases"
        lease_file.write_text(
            "1713281234 aa:bb:cc:dd:ee:ff 192.168.50.10 hostname1 *\n"
            "1713281567 11:22:33:44:55:66 192.168.50.11 hostname2 *\n"
        )

        with patch.object(DnsmasqManager, "LEASE_FILE", str(lease_file)):
            manager = DnsmasqManager()
            leases = manager.get_leases()
            assert len(leases) == 2
            assert leases[0]["ip"] == "192.168.50.10"
            assert leases[0]["mac"] == "aa:bb:cc:dd:ee:ff"

    def test_get_leases_no_file(self):
        """Test getting leases when file doesn't exist."""
        with patch("os.path.isfile") as mock_isfile:
            mock_isfile.return_value = False
            manager = DnsmasqManager()
            leases = manager.get_leases()
            assert leases == []
