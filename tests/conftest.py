"""Shared test fixtures and configuration."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_subprocess():
    """Mock subprocess module for testing system calls."""
    with patch("subprocess.run") as mock_run, \
         patch("subprocess.Popen") as mock_popen:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        mock_popen.return_value = MagicMock(
            pid=12345,
            poll=MagicMock(returncode=None)
        )
        yield {"run": mock_run, "popen": mock_popen}


@pytest.fixture
def sample_csv_content():
    """Sample airodump-ng CSV content for testing."""
    return """Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
D4:AB:CD:9E:23:11,2026-04-16 17:56:37,2026-04-16 18:16:38,-79,1668,62:0D:10:4D:E0:B9,
B8:06:0D:BF:4D:DA,2026-04-16 17:56:41,2026-04-16 18:16:28,-85,158,62:0D:10:4D:E0:B9,
E2:2B:CB:DA:42:FF,2026-04-16 17:56:42,2026-04-16 18:16:06,-47,67,62:0D:10:4D:E0:B9,
78:CA:39:BB:1B:E3,2026-04-16 17:57:02,2026-04-16 18:16:39,-75,314,62:0D:10:4D:E0:B9,CoffeeShop_Free
66:A3:92:39:49:11,2026-04-16 17:59:54,2026-04-16 18:16:24,-86,7,(not associated) ,Hotel_Guest
12:BA:8F:34:D5:07,2026-04-16 18:07:39,2026-04-16 18:07:39,-61,4,(not associated) ,RandomCafe,OnePlus_Device
"""


@pytest.fixture
def sample_lease_content():
    """Sample dnsmasq lease file content."""
    return """1713281234 aa:bb:cc:dd:ee:ff 192.168.50.10 hostname1 *
1713281567 11:22:33:44:55:66 192.168.50.11 hostname2 *
1713282000 ff:ee:dd:cc:bb:aa 192.168.50.12 hostname3 *
"""


@pytest.fixture
def mock_iwconfig_output():
    """Mock iwconfig command output."""
    return """wlp2s0    IEEE 802.11  ESSID:"TestNetwork"
          Mode:Managed  Frequency:2.437 GHz  Access Point: AA:BB:CC:DD:EE:FF
          Bit Rate=144.4 Mb/s   Tx-Power=15 dBm
          wlan1     IEEE 802.11  Mode:Master  Frequency:5.18 GHz
          ESSID:"TestAP"
"""


@pytest.fixture
def mock_iw_dev_output():
    """Mock iw dev command output."""
    return """phy#0
    Interface wlan0
        ifindex 3
        wdev 0x1
        addr aa:bb:cc:dd:ee:f0
        type managed
phy#1
    Interface wlan1
        ifindex 4
        wdev 0x2
        addr aa:bb:cc:dd:ee:f1
        type AP
"""


@pytest.fixture
def mock_iw_dev_monitor_output():
    """Mock iw dev with monitor mode interface."""
    return """phy#0
    Interface wlan0mon
        ifindex 5
        wdev 0x3
        addr aa:bb:cc:dd:ee:f2
        type monitor
"""
