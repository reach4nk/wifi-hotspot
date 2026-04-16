"""Unit tests for CSV parser."""

import json
import os
import pytest

from hotspot.scanner.parser import CSVParser, CSVStation


class TestCSVParser:
    """Tests for CSVParser class."""

    def test_is_valid_mac_valid(self):
        """Test valid MAC returns True."""
        assert CSVParser.is_valid_mac("AA:BB:CC:DD:EE:FF") is True

    def test_is_valid_mac_invalid(self):
        """Test invalid MAC returns False."""
        assert CSVParser.is_valid_mac("invalid") is False
        assert CSVParser.is_valid_mac("") is False

    def test_parse_content_empty(self):
        """Test parsing empty content."""
        result = CSVParser.parse_content("")
        assert result == []

    def test_parse_content_no_stations(self):
        """Test parsing content without stations header."""
        content = "BSSID, First time seen, Last time seen, channel\n"
        result = CSVParser.parse_content(content)
        assert result == []

    def test_parse_content_with_station_and_single_ssid(self):
        """Test parsing station with a single probed SSID."""
        content = """Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
D4:AB:CD:9E:23:11,2026-04-16 17:56:37,2026-04-16 18:16:38,-79,1668,62:0D:10:4D:E0:B9,CoffeeShop_Free
"""
        result = CSVParser.parse_content(content)
        assert len(result) == 1
        assert result[0].mac == "D4:AB:CD:9E:23:11"
        assert "CoffeeShop_Free" in result[0].ssids

    def test_parse_content_with_multiple_ssids(self):
        """Test parsing station with multiple probed SSIDs."""
        content = """Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
AA:50:F3:21:AC:30,2026-04-16 18:05:06,2026-04-16 18:05:44,-82,92,50:0F:F5:47:C2:69,BT-Device42,HomeRouter
"""
        result = CSVParser.parse_content(content)
        assert len(result) == 1
        assert result[0].mac == "AA:50:F3:21:AC:30"
        assert "BT-Device42" in result[0].ssids
        assert "HomeRouter" in result[0].ssids

    def test_parse_content_with_not_associated(self):
        """Test parsing station with (not associated) BSSID."""
        content = """Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
12:BA:8F:34:D5:07,2026-04-16 18:07:39,2026-04-16 18:07:39,-61,4,(not associated) ,RandomCafe,OnePlus_Device
"""
        result = CSVParser.parse_content(content)
        assert len(result) == 1
        assert result[0].mac == "12:BA:8F:34:D5:07"
        assert "RandomCafe" in result[0].ssids
        assert "OnePlus_Device" in result[0].ssids

    def test_parse_content_skips_invalid_mac(self):
        """Test parsing skips lines with invalid MAC."""
        content = """Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
invalid_mac,2026-04-16 17:56:37,2026-04-16 18:16:38,-79,1668,62:0D:10:4D:E0:B9,CoffeeShop_Free
"""
        result = CSVParser.parse_content(content)
        assert len(result) == 0

    def test_parse_content_skips_empty_ssids(self):
        """Test parsing skips stations with no SSIDs (empty probed ESSIDs)."""
        content = """Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
D4:AB:CD:9E:23:11,2026-04-16 17:56:37,2026-04-16 18:16:38,-79,1668,62:0D:10:4D:E0:B9,
"""
        result = CSVParser.parse_content(content)
        assert len(result) == 0

    def test_parse_content_multiple_stations(self):
        """Test parsing multiple stations from CSV."""
        content = """Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
D4:AB:CD:9E:23:11,2026-04-16 17:56:37,2026-04-16 18:16:38,-79,1668,62:0D:10:4D:E0:B9,
B8:06:0D:BF:4D:DA,2026-04-16 17:56:41,2026-04-16 18:16:28,-85,158,62:0D:10:4D:E0:B9,
78:CA:39:BB:1B:E3,2026-04-16 17:57:02,2026-04-16 18:16:39,-75,314,62:0D:10:4D:E0:B9,CoffeeShop_Free
"""
        result = CSVParser.parse_content(content)
        assert len(result) == 1  # Only one has SSIDs
        assert result[0].mac == "78:CA:39:BB:1B:E3"

    def test_parse_file_not_found(self, tmp_path):
        """Test parsing non-existent file returns empty."""
        result = CSVParser.parse_file(str(tmp_path / "nonexistent.csv"))
        assert result == []

    def test_parse_station_line_empty(self):
        """Test parsing empty line."""
        result = CSVParser._parse_station_line("")
        assert result is None

    def test_parse_station_line_invalid_mac(self):
        """Test parsing line with invalid MAC."""
        result = CSVParser._parse_station_line("invalid,data,here")
        assert result is None

    def test_parse_station_line_no_ssids(self):
        """Test parsing line with valid MAC but no SSIDs."""
        result = CSVParser._parse_station_line("AA:BB:CC:DD:EE:FF")
        assert result is None

    def test_parse_station_line_with_empty_ssid(self):
        """Test parsing line with empty SSID after MAC."""
        result = CSVParser._parse_station_line("AA:BB:CC:DD:EE:FF,,,,,,,,")
        assert result is None

    def test_parse_file_with_realistic_content(self, tmp_path):
        """Test parsing with realistic airodump-ng CSV format."""
        csv_content = """Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
D4:AB:CD:9E:23:11,2026-04-16 17:56:37,2026-04-16 18:16:38,-79,1668,62:0D:10:4D:E0:B9,
78:CA:39:BB:1B:E3,2026-04-16 17:57:02,2026-04-16 18:16:39,-75,314,62:0D:10:4D:E0:B9,CoffeeShop_Free
66:A3:92:39:49:11,2026-04-16 17:59:54,2026-04-16 18:16:24,-86,7,(not associated) ,Hotel_Guest
12:BA:8F:34:D5:07,2026-04-16 18:07:39,2026-04-16 18:07:39,-61,4,(not associated) ,RandomCafe,OnePlus_Device
"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)

        result = CSVParser.parse_file(str(csv_file))
        assert len(result) == 3

        macs = [station.mac for station in result]
        assert "78:CA:39:BB:1B:E3" in macs
        assert "66:A3:92:39:49:11" in macs
        assert "12:BA:8F:34:D5:07" in macs

        # Verify SSIDs
        for station in result:
            if station.mac == "66:A3:92:39:49:11":
                assert "Hotel_Guest" in station.ssids
            if station.mac == "12:BA:8F:34:D5:07":
                assert "RandomCafe" in station.ssids
                assert "OnePlus_Device" in station.ssids


class TestCSVStation:
    """Tests for CSVStation dataclass."""

    def test_creation(self):
        """Test station creation."""
        station = CSVStation(
            mac="AA:BB:CC:DD:EE:FF",
            ssids=["Network1", "Network2"]
        )
        assert station.mac == "AA:BB:CC:DD:EE:FF"
        assert station.ssids == ["Network1", "Network2"]
        assert station.signal is None
        assert station.connected_time is None

    def test_creation_with_optional(self):
        """Test station creation with optional fields."""
        station = CSVStation(
            mac="AA:BB:CC:DD:EE:FF",
            ssids=["Network1"],
            signal="-45",
            connected_time="100"
        )
        assert station.signal == "-45"
        assert station.connected_time == "100"
