"""CSV parsing utilities for airodump-ng output."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from typing import Optional

from hotspot.core.mac import MACClassifier, MACClass, is_valid_mac


@dataclass
class CSVStation:
    """Represents a parsed station from airodump-ng CSV."""

    mac: str
    ssids: list[str] = field(default_factory=list)
    signal: Optional[str] = None
    connected_time: Optional[str] = None


class CSVParser:
    """Parses airodump-ng CSV output."""

    STATION_HEADER = "Station MAC"

    @staticmethod
    def is_valid_mac(mac: str) -> bool:
        """Check if string is a valid MAC address.

        Args:
            mac: MAC address string.

        Returns:
            True if valid, False otherwise.
        """
        return is_valid_mac(mac)

    @classmethod
    def parse_content(cls, content: str) -> list[CSVStation]:
        """Parse CSV content and extract stations.

        Args:
            content: CSV file content.

        Returns:
            List of parsed stations.
        """
        if cls.STATION_HEADER not in content:
            return []

        station_section = content.split(cls.STATION_HEADER)[1]
        lines = station_section.strip().split("\n")

        if len(lines) <= 1:
            return []

        stations = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue

            station = cls._parse_station_line(line)
            if station:
                stations.append(station)

        return stations

    @classmethod
    def _parse_station_line(cls, line: str) -> Optional[CSVStation]:
        """Parse a single station CSV line.

        Args:
            line: CSV line.

        Returns:
            Parsed station or None.
        """
        try:
            reader = csv.reader([line])
            row = next(reader)
        except Exception:
            return None

        if not row or len(row) < 1:
            return None

        mac = row[0].strip()

        if not cls.is_valid_mac(mac):
            return None

        ssids = []
        if len(row) > 6:
            for ssid in row[6:]:
                ssid = ssid.strip()
                if ssid:
                    ssids.append(ssid)

        if not ssids:
            return None

        return CSVStation(mac=mac, ssids=ssids)

    @classmethod
    def parse_file(cls, file_path: str) -> list[CSVStation]:
        """Parse airodump-ng CSV file.

        Args:
            file_path: Path to CSV file.

        Returns:
            List of parsed stations.
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            return []

        return cls.parse_content(content)
