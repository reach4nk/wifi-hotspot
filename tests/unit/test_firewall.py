"""Unit tests for firewall management."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from hotspot.core.firewall import FirewallManager


class TestFirewallManager:
    """Tests for FirewallManager class."""

    def test_enable_ip_forwarding_sysctl(self):
        """Test enabling IP forwarding via sysctl."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            FirewallManager.enable_ip_forwarding()
            mock_run.assert_called()

    def test_enable_ip_forwarding_proc(self):
        """Test enabling IP forwarding via /proc."""
        with patch("subprocess.run") as mock_run, \
             patch("builtins.open", create=True) as mock_open:
            mock_run.return_value = MagicMock(returncode=1)
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            FirewallManager.enable_ip_forwarding()
            mock_file.write.assert_called_with("1")

    def test_disable_ip_forwarding(self):
        """Test disabling IP forwarding."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            FirewallManager.disable_ip_forwarding()
            mock_run.assert_called()

    def test_is_ip_forwarding_enabled_true(self):
        """Test IP forwarding is enabled."""
        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = "1\n"
            mock_open.return_value = mock_file

            result = FirewallManager.is_ip_forwarding_enabled()
            assert result is True

    def test_is_ip_forwarding_enabled_false(self):
        """Test IP forwarding is disabled."""
        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = "0\n"
            mock_open.return_value = mock_file

            result = FirewallManager.is_ip_forwarding_enabled()
            assert result is False

    def test_is_ip_forwarding_enabled_error(self):
        """Test IP forwarding check with error."""
        with patch("builtins.open", create=True) as mock_open:
            mock_open.side_effect = OSError("Cannot open")
            result = FirewallManager.is_ip_forwarding_enabled()
            assert result is False

    def test_enable_nat(self):
        """Test enabling NAT between interfaces."""
        with patch("subprocess.run") as mock_run, \
             patch.object(FirewallManager, "enable_ip_forwarding"):
            mock_run.return_value = MagicMock(returncode=0)
            FirewallManager.enable_nat("eth0", "wlan0")
            assert mock_run.call_count >= 3

    def test_disable_nat(self):
        """Test disabling NAT between interfaces."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            FirewallManager.disable_nat("eth0", "wlan0")
            assert mock_run.call_count >= 3

    def test_setup_hotspot_firewall(self):
        """Test setting up hotspot firewall."""
        with patch.object(FirewallManager, "enable_nat") as mock_nat:
            FirewallManager.setup_hotspot_firewall("eth0", "wlan0")
            mock_nat.assert_called_once_with("eth0", "wlan0")

    def test_teardown_hotspot_firewall(self):
        """Test tearing down hotspot firewall."""
        with patch.object(FirewallManager, "disable_nat") as mock_nat:
            FirewallManager.teardown_hotspot_firewall("eth0", "wlan0")
            mock_nat.assert_called_once_with("eth0", "wlan0")

    def test_list_nat_rules(self):
        """Test listing NAT rules."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Chain POSTROUTING\ntarget     prot opt source               destination\nMASQUERADE  all  --  0.0.0.0/0            0.0.0.0/0\n",
                stderr=""
            )
            result = FirewallManager.list_nat_rules()
            assert "POSTROUTING" in result

    def test_list_nat_rules_error(self):
        """Test listing NAT rules when error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            result = FirewallManager.list_nat_rules()
            assert result == "No NAT rules"

    def test_list_forward_rules(self):
        """Test listing forward rules."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Chain FORWARD\ntarget     prot opt source               destination\nACCEPT     all  --  0.0.0.0/0            0.0.0.0/0\n",
                stderr=""
            )
            result = FirewallManager.list_forward_rules()
            assert "FORWARD" in result

    def test_list_forward_rules_error(self):
        """Test listing forward rules when error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            result = FirewallManager.list_forward_rules()
            assert result == "No forward rules"

    def test_count_rules(self):
        """Test counting firewall rules."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Chain INPUT (policy ACCEPT)\nChain FORWARD (policy ACCEPT)\nChain OUTPUT (policy ACCEPT)\n",
                stderr=""
            )
            result = FirewallManager.count_rules()
            assert result == 2  # 3 chains - 1 = 2

    def test_count_rules_empty(self):
        """Test counting rules when error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            result = FirewallManager.count_rules()
            assert result == 0

    def test_flush(self):
        """Test flushing all rules."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            FirewallManager.flush()
            assert mock_run.call_count == 4

    def test_save_rules(self):
        """Test saving firewall rules."""
        with patch("subprocess.run") as mock_run, \
             patch("builtins.open", create=True) as mock_open:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="# Generated by iptables-save\n*filter\n"
            )
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            result = FirewallManager.save("/tmp/iptables.backup")
            assert result is True

    def test_save_rules_error(self):
        """Test saving firewall rules fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            result = FirewallManager.save("/tmp/iptables.backup")
            assert result is False

    def test_restore_rules(self):
        """Test restoring firewall rules."""
        with patch("builtins.open", create=True) as mock_open, \
             patch("subprocess.run") as mock_run:
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = "# iptables rules\n"
            mock_open.return_value = mock_file
            mock_run.return_value = MagicMock(returncode=0)

            result = FirewallManager.restore("/tmp/iptables.backup")
            assert result is True

    def test_restore_rules_file_not_found(self):
        """Test restoring firewall rules when file not found."""
        with patch("builtins.open", create=True) as mock_open:
            mock_open.side_effect = OSError("File not found")
            result = FirewallManager.restore("/tmp/iptables.backup")
            assert result is False
