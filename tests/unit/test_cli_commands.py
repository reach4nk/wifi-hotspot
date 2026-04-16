"""Unit tests for CLI commands."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from hotspot.cli.find_interfaces import FindInterfacesCommand
from hotspot.cli.monitor import MonitorCommand
from hotspot.cli.scan import ScanCommand
from hotspot.cli.setup import SetupCommand
from hotspot.cli.stop import StopCommand
from hotspot.cli.teardown import TeardownCommand
from hotspot.cli.start import StartCommand


class TestFindInterfacesCommand:
    """Tests for FindInterfacesCommand."""

    def test_run_with_interfaces(self):
        """Test run with detected interfaces."""
        cmd = FindInterfacesCommand()
        with patch("hotspot.cli.find_interfaces.InterfaceManager.get_internal_interface") as mock_int:
            with patch("hotspot.cli.find_interfaces.InterfaceManager.get_external_interface") as mock_ext:
                with patch("hotspot.cli.find_interfaces.InterfaceManager.get_all_wireless") as mock_all:
                    mock_int.return_value = "wlan0"
                    mock_ext.return_value = "wlan1"
                    mock_all.return_value = ["wlan0", "wlan1"]
                    result = cmd.run(None)
                    assert result == 0

    def test_run_no_interfaces(self):
        """Test run with no interfaces found."""
        cmd = FindInterfacesCommand()
        with patch("hotspot.cli.find_interfaces.InterfaceManager.get_internal_interface") as mock_int:
            with patch("hotspot.cli.find_interfaces.InterfaceManager.get_external_interface") as mock_ext:
                with patch("hotspot.cli.find_interfaces.InterfaceManager.get_all_wireless") as mock_all:
                    mock_int.return_value = ""
                    mock_ext.return_value = ""
                    mock_all.return_value = []
                    result = cmd.run(None)
                    assert result == 0


class TestMonitorCommand:
    """Tests for MonitorCommand."""

    def test_run_with_no_interface(self):
        """Test monitor with no hotspot interface."""
        cmd = MonitorCommand()
        with patch("hotspot.cli.monitor.InterfaceManager.get_external_interface") as mock_ext:
            with patch("hotspot.cli.monitor.HostapdManager") as mock_hapd_cls:
                with patch("hotspot.cli.monitor.DnsmasqManager") as mock_dns_cls:
                    mock_ext.return_value = ""
                    mock_hapd = MagicMock()
                    mock_hapd.get_stations.return_value = []
                    mock_hapd_cls.return_value = mock_hapd
                    mock_dns = MagicMock()
                    mock_dns.get_leases.return_value = []
                    mock_dns_cls.return_value = mock_dns
                    result = cmd.run(None)
                    assert result == 0

    def test_run_with_interface_and_stations(self):
        """Test monitor with active hotspot and connected stations."""
        cmd = MonitorCommand()
        with patch("hotspot.cli.monitor.InterfaceManager.get_external_interface") as mock_ext:
            with patch("hotspot.cli.monitor.HostapdManager") as mock_hapd_cls:
                with patch("hotspot.cli.monitor.DnsmasqManager") as mock_dns_cls:
                    mock_ext.return_value = "wlan1"
                    mock_hapd = MagicMock()
                    mock_hapd.get_stations.return_value = ["aa:bb:cc:dd:ee:ff"]
                    mock_hapd_cls.return_value = mock_hapd
                    mock_dns = MagicMock()
                    mock_dns.get_leases.return_value = [
                        {"ip": "192.168.50.10", "mac": "aa:bb:cc:dd:ee:ff", "hostname": "device"}
                    ]
                    mock_dns_cls.return_value = mock_dns
                    with patch("subprocess.run") as mock_run:
                        mock_run.return_value = MagicMock(stdout="192.168.50.10 dev wlan1")
                        result = cmd.run(None)
                        assert result == 0

    def test_run_with_interface_no_stations(self):
        """Test monitor with active hotspot but no connected stations."""
        cmd = MonitorCommand()
        with patch("hotspot.cli.monitor.InterfaceManager.get_external_interface") as mock_ext:
            with patch("hotspot.cli.monitor.HostapdManager") as mock_hapd_cls:
                with patch("hotspot.cli.monitor.DnsmasqManager") as mock_dns_cls:
                    mock_ext.return_value = "wlan1"
                    mock_hapd = MagicMock()
                    mock_hapd.get_stations.return_value = []
                    mock_hapd_cls.return_value = mock_hapd
                    mock_dns = MagicMock()
                    mock_dns.get_leases.return_value = []
                    mock_dns_cls.return_value = mock_dns
                    with patch("subprocess.run") as mock_run:
                        mock_run.return_value = MagicMock(stdout="")
                        result = cmd.run(None)
                        assert result == 0


class TestSetupCommand:
    """Tests for SetupCommand."""

    def test_run_success(self):
        """Test successful setup."""
        cmd = SetupCommand()
        with patch("hotspot.cli.setup.require_root"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = cmd.run(None)
                assert result == 0

    def test_run_install_failure(self):
        """Test setup with install failure."""
        cmd = SetupCommand()
        with patch("hotspot.cli.setup.require_root"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1)
                result = cmd.run(None)
                assert result == 1


class TestTeardownCommand:
    """Tests for TeardownCommand."""

    def test_run_success(self):
        """Test successful teardown."""
        cmd = TeardownCommand()
        with patch("hotspot.cli.teardown.require_root"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = cmd.run(None)
                assert result == 0

    def test_run_remove_failure(self):
        """Test teardown with remove failure."""
        cmd = TeardownCommand()
        with patch("hotspot.cli.teardown.require_root"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1)
                result = cmd.run(None)
                assert result == 1


class TestStopCommand:
    """Tests for StopCommand."""

    def test_run_no_interface(self):
        """Test stop with no hotspot interface."""
        cmd = StopCommand()
        with patch("hotspot.cli.stop.require_root"):
            with patch("hotspot.core.interface.InterfaceManager.get_external_interface") as mock_ext:
                with patch("hotspot.core.interface.InterfaceManager.get_internal_interface") as mock_int:
                    with patch("hotspot.services.hostapd.HostapdManager") as mock_hapd_cls:
                        with patch("hotspot.services.dnsmasq.DnsmasqManager") as mock_dns_cls:
                            mock_ext.return_value = ""
                            mock_int.return_value = ""
                            mock_hapd = MagicMock()
                            mock_hapd.stop.return_value = True
                            mock_hapd_cls.return_value = mock_hapd
                            mock_dns = MagicMock()
                            mock_dns.stop.return_value = True
                            mock_dns_cls.return_value = mock_dns
                            result = cmd.run(None)
                            assert result == 0

    def test_run_with_interface(self):
        """Test stop with active hotspot."""
        cmd = StopCommand()
        with patch("hotspot.cli.stop.require_root"):
            with patch("hotspot.core.interface.InterfaceManager.get_external_interface") as mock_ext:
                with patch("hotspot.core.interface.InterfaceManager.get_internal_interface") as mock_int:
                    with patch("hotspot.services.hostapd.HostapdManager") as mock_hapd_cls:
                        with patch("hotspot.services.dnsmasq.DnsmasqManager") as mock_dns_cls:
                            with patch("hotspot.core.firewall.FirewallManager") as mock_fw_cls:
                                with patch("hotspot.core.network.NetworkManager") as mock_net_cls:
                                    mock_ext.return_value = "wlan1"
                                    mock_int.return_value = "wlan0"
                                    mock_hapd = MagicMock()
                                    mock_hapd.stop.return_value = True
                                    mock_hapd_cls.return_value = mock_hapd
                                    mock_dns = MagicMock()
                                    mock_dns.stop.return_value = True
                                    mock_dns_cls.return_value = mock_dns
                                    result = cmd.run(None)
                                    assert result == 0

    def test_run_with_no_internal_interface(self):
        """Test stop when only external interface is present."""
        cmd = StopCommand()
        with patch("hotspot.cli.stop.require_root"):
            with patch("hotspot.core.interface.InterfaceManager.get_external_interface") as mock_ext:
                with patch("hotspot.core.interface.InterfaceManager.get_internal_interface") as mock_int:
                    with patch("hotspot.services.hostapd.HostapdManager") as mock_hapd_cls:
                        with patch("hotspot.services.dnsmasq.DnsmasqManager") as mock_dns_cls:
                            with patch("hotspot.core.firewall.FirewallManager") as mock_fw_cls:
                                with patch("hotspot.core.network.NetworkManager") as mock_net_cls:
                                    mock_ext.return_value = "wlan1"
                                    mock_int.return_value = ""  # No internal interface
                                    mock_hapd = MagicMock()
                                    mock_hapd.stop.return_value = True
                                    mock_hapd_cls.return_value = mock_hapd
                                    mock_dns = MagicMock()
                                    mock_dns.stop.return_value = True
                                    mock_dns_cls.return_value = mock_dns
                                    result = cmd.run(None)
                                    assert result == 0


class TestStartCommand:
    """Tests for StartCommand."""

    def test_run_no_hotspot_iface(self):
        """Test start with no hotspot interface."""
        cmd = StartCommand()
        with patch("hotspot.cli.start.require_root"):
            with patch("hotspot.cli.start.require_tools"):
                with patch("hotspot.cli.start.InterfaceManager.get_external_interface") as mock_ext:
                    with patch("hotspot.cli.start.InterfaceManager.get_internal_interface") as mock_int:
                        mock_ext.return_value = ""
                        mock_int.return_value = "wlan0"
                        result = cmd.run(MagicMock())
                        assert result == 1

    def test_run_no_internet_iface(self):
        """Test start with no internet interface."""
        cmd = StartCommand()
        with patch("hotspot.cli.start.require_root"):
            with patch("hotspot.cli.start.require_tools"):
                with patch("hotspot.cli.start.InterfaceManager.get_external_interface") as mock_ext:
                    with patch("hotspot.cli.start.InterfaceManager.get_internal_interface") as mock_int:
                        mock_ext.return_value = "wlan1"
                        mock_int.return_value = ""
                        result = cmd.run(MagicMock())
                        assert result == 1

    def test_run_with_custom_args(self):
        """Test start with custom arguments."""
        args = MagicMock()
        args.interface = "wlan1"
        args.internet_if = "wlan0"
        args.ssid = "TestNet"
        args.password = "TestPass123"
        args.encryption = "wpa2"
        args.gateway = None
        args.dhcp_start = None
        args.dhcp_end = None
        args.dns = None
        args.channel = None
        args.mode = None

        cmd = StartCommand()
        with patch("hotspot.cli.start.require_root"):
            with patch("hotspot.cli.start.require_tools"):
                with patch("hotspot.cli.start.InterfaceManager.get_external_interface") as mock_ext:
                    with patch("hotspot.cli.start.InterfaceManager.get_internal_interface") as mock_int:
                        with patch("hotspot.cli.start.HotspotService") as mock_svc_cls:
                            mock_ext.return_value = "wlan1"
                            mock_int.return_value = "wlan0"
                            mock_svc = MagicMock()
                            mock_svc.start.return_value = None
                            mock_svc_cls.return_value = mock_svc
                            result = cmd.run(args)
                            assert result == 0

    def test_run_with_invalid_credentials(self):
        """Test start with invalid credentials."""
        args = MagicMock()
        args.interface = ""
        args.internet_if = ""
        args.ssid = "A" * 33
        args.password = ""
        args.encryption = "wpa2"
        args.gateway = None
        args.dhcp_start = None
        args.dhcp_end = None
        args.dns = None
        args.channel = None
        args.mode = None

        cmd = StartCommand()
        with patch("hotspot.cli.start.require_root"):
            with patch("hotspot.cli.start.require_tools"):
                with patch("hotspot.cli.start.InterfaceManager.get_external_interface") as mock_ext:
                    with patch("hotspot.cli.start.InterfaceManager.get_internal_interface") as mock_int:
                        with patch("hotspot.cli.start.CredentialValidator.validate_credentials") as mock_val:
                            mock_ext.return_value = "wlan1"
                            mock_int.return_value = "wlan0"
                            mock_val.return_value = (False, "SSID too long")
                            result = cmd.run(args)
                            assert result == 1

    def test_run_with_generated_credentials(self):
        """Test start with auto-generated credentials."""
        args = MagicMock()
        args.interface = ""
        args.internet_if = ""
        args.ssid = ""
        args.password = ""
        args.encryption = "wpa2"
        args.gateway = None
        args.dhcp_start = None
        args.dhcp_end = None
        args.dns = None
        args.channel = None
        args.mode = None

        cmd = StartCommand()
        with patch("hotspot.cli.start.require_root"):
            with patch("hotspot.cli.start.require_tools"):
                with patch("hotspot.cli.start.InterfaceManager.get_external_interface") as mock_ext:
                    with patch("hotspot.cli.start.InterfaceManager.get_internal_interface") as mock_int:
                        with patch("hotspot.cli.start.HotspotService") as mock_svc_cls:
                            mock_ext.return_value = "wlan1"
                            mock_int.return_value = "wlan0"
                            mock_svc = MagicMock()
                            mock_svc.start.return_value = None
                            mock_svc_cls.return_value = mock_svc
                            result = cmd.run(args)
                            assert result == 0

    def test_run_with_open_network(self):
        """Test start with open network encryption."""
        args = MagicMock()
        args.interface = "wlan1"
        args.internet_if = "wlan0"
        args.ssid = "FreeWiFi"
        args.password = ""
        args.encryption = "open"
        args.gateway = None
        args.dhcp_start = None
        args.dhcp_end = None
        args.dns = None
        args.channel = None
        args.mode = None

        cmd = StartCommand()
        with patch("hotspot.cli.start.require_root"):
            with patch("hotspot.cli.start.require_tools"):
                with patch("hotspot.cli.start.HotspotService") as mock_svc_cls:
                    mock_svc = MagicMock()
                    mock_svc.start.return_value = None
                    mock_svc_cls.return_value = mock_svc
                    result = cmd.run(args)
                    assert result == 0

    def test_run_with_wep_encryption(self):
        """Test start with WEP encryption."""
        args = MagicMock()
        args.interface = "wlan1"
        args.internet_if = "wlan0"
        args.ssid = "OldDevice"
        args.password = "12345678901234567890123456"
        args.encryption = "wep"
        args.gateway = None
        args.dhcp_start = None
        args.dhcp_end = None
        args.dns = None
        args.channel = None
        args.mode = None

        cmd = StartCommand()
        with patch("hotspot.cli.start.require_root"):
            with patch("hotspot.cli.start.require_tools"):
                with patch("hotspot.cli.start.HotspotService") as mock_svc_cls:
                    mock_svc = MagicMock()
                    mock_svc.start.return_value = None
                    mock_svc_cls.return_value = mock_svc
                    result = cmd.run(args)
                    assert result == 0

    def test_run_service_exception(self):
        """Test start with service exception."""
        args = MagicMock()
        args.interface = "wlan1"
        args.internet_if = "wlan0"
        args.ssid = "TestNet"
        args.password = "TestPass123"
        args.encryption = "wpa2"
        args.gateway = None
        args.dhcp_start = None
        args.dhcp_end = None
        args.dns = None
        args.channel = None
        args.mode = None

        cmd = StartCommand()
        with patch("hotspot.cli.start.require_root"):
            with patch("hotspot.cli.start.require_tools"):
                with patch("hotspot.cli.start.InterfaceManager.get_external_interface") as mock_ext:
                    with patch("hotspot.cli.start.InterfaceManager.get_internal_interface") as mock_int:
                        with patch("hotspot.cli.start.HotspotService") as mock_svc_cls:
                            mock_ext.return_value = "wlan1"
                            mock_int.return_value = "wlan0"
                            mock_svc = MagicMock()
                            mock_svc.start.side_effect = Exception("Test error")
                            mock_svc_cls.return_value = mock_svc
                            result = cmd.run(args)
                            assert result == 1


class TestScanCommand:
    """Tests for ScanCommand."""

    def test_run_missing_tool(self):
        """Test scan with missing required tool."""
        args = MagicMock()
        args.interface = None
        args.duration = None
        args.output = None
        args.cleanup = False

        cmd = ScanCommand()
        with patch("hotspot.cli.scan.require_root"):
            with patch("hotspot.cli.scan.ProbeScanner.check_requirements") as mock_req:
                mock_req.return_value = ["airodump-ng"]
                result = cmd.run(args)
                assert result == 1

    def test_run_no_interface_detected(self):
        """Test scan when no interface can be detected."""
        args = MagicMock()
        args.interface = None
        args.duration = None
        args.output = None
        args.cleanup = False

        cmd = ScanCommand()
        with patch("hotspot.cli.scan.require_root"):
            with patch("hotspot.cli.scan.ProbeScanner.check_requirements") as mock_req:
                with patch("hotspot.cli.scan.ProbeScanner.detect_interface") as mock_detect:
                    mock_req.return_value = []
                    mock_detect.return_value = None
                    result = cmd.run(args)
                    assert result == 1

    def test_run_success(self):
        """Test successful scan."""
        from hotspot.cli.scan import ScanCommand

        args = MagicMock()
        args.interface = "wlan1"
        args.duration = 60
        args.output = "/tmp/probes.json"
        args.cleanup = True

        mock_scanner = MagicMock()
        mock_scanner.run.return_value = 0

        cmd = ScanCommand()
        with patch.object(cmd, '_check_requirements', return_value=[]):
            with patch.object(cmd, '_create_scanner', return_value=mock_scanner):
                with patch('hotspot.cli.scan.require_root'):
                    result = cmd.run(args)
                    assert result == 0
                    mock_scanner.cleanup.assert_called_once()
