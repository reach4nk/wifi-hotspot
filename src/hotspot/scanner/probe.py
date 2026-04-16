"""WiFi probe request scanner using airodump-ng."""

from __future__ import annotations

import csv
import json
import os
import re
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from hotspot.core.mac import MACClassifier, MACClass
from hotspot.core.interface import InterfaceManager
from hotspot.scanner.parser import CSVParser
from hotspot.utils.logging import get_logger

logger = get_logger("scanner")


@dataclass
class ProbeClient:
    """Represents a client discovered via probe requests."""

    mac: str
    mac_class: MACClass
    ssids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "class": self.mac_class.value,
            "mac": self.mac,
            "ssids": self.ssids,
        }


class ProbeScanner:
    """Scans for WiFi probe requests using airodump-ng."""

    DEFAULT_OUTPUT = "./probes.json"
    STATION_HEADER = "Station MAC"

    def __init__(
        self,
        interface: str,
        duration: Optional[int] = None,
        output: Optional[str] = None,
        restore_managed: bool = False,
    ) -> None:
        """Initialize probe scanner.

        Args:
            interface: WiFi interface to use.
            duration: Scan duration in seconds (None for continuous).
            output: Output JSON file path.
            restore_managed: Whether to restore managed mode on cleanup.
        """
        self.interface = interface
        self.duration = duration
        self.output = output or self.DEFAULT_OUTPUT
        self.restore_managed = restore_managed

        self.temp_base: Optional[str] = None
        self.csv_file: Optional[str] = None
        self.airodump_proc: Optional[subprocess.Popen[bytes]] = None
        self.interrupted = False

        self._clients: dict[str, ProbeClient] = {}
        self._seen_macs: set[str] = set()

        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum: int, frame) -> None:
        """Handle interrupt signal."""
        logger.info("Interrupt received, saving and stopping...")
        self.interrupted = True

    def _setup_monitor_mode(self) -> bool:
        """Set up monitor mode on interface.

        Returns:
            True on success.
        """
        from hotspot.core.network import NetworkManager

        result = subprocess.run(
            ["iw", "dev", self.interface, "info"],
            capture_output=True,
            text=True,
            check=False,
        )
        if "type Monitor" in result.stdout:
            logger.info("Interface %s already in monitor mode", self.interface)
            subprocess.run(
                ["ip", "link", "set", self.interface, "up"],
                capture_output=True,
                check=False
            )
            return True

        logger.info("Enabling monitor mode on %s...", self.interface)

        subprocess.run(
            ["ip", "link", "set", self.interface, "down"],
            capture_output=True,
            check=False
        )
        result = subprocess.run(
            ["iw", "dev", self.interface, "set", "type", "monitor"],
            capture_output=True,
            check=False
        )
        if result.returncode != 0:
            logger.error("Failed to set monitor mode: %s", result.stderr.decode())
            return False

        subprocess.run(
            ["ip", "link", "set", self.interface, "up"],
            capture_output=True,
            check=False
        )
        return True

    def _restore_managed_mode(self) -> None:
        """Restore managed mode on interface."""
        logger.info("Restoring managed mode on %s...", self.interface)

        subprocess.run(
            ["ip", "link", "set", self.interface, "down"],
            capture_output=True,
            check=False
        )
        subprocess.run(
            ["iw", "dev", self.interface, "set", "type", "managed"],
            capture_output=True,
            check=False
        )
        subprocess.run(
            ["ip", "link", "set", self.interface, "up"],
            capture_output=True,
            check=False
        )

    def _load_existing(self) -> None:
        """Load existing probes.json into memory."""
        if not os.path.exists(self.output):
            logger.info("No existing %s, starting fresh", self.output)
            return

        try:
            with open(self.output, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "clients" in data:
                for client in data["clients"]:
                    mac = client.get("mac", "")
                    if mac and CSVParser.is_valid_mac(mac):
                        ssids = client.get("ssids", [])
                        if isinstance(ssids, list):
                            self._clients[mac] = ProbeClient(
                                mac=mac,
                                mac_class=MACClassifier.classify(mac),
                                ssids=ssids,
                            )
                            self._seen_macs.add(mac)

            logger.info("Loaded %d existing clients", len(self._clients))

        except (json.JSONDecodeError, OSError) as err:
            logger.warning("Could not load existing file: %s", err)

    def _save_results(self) -> None:
        """Save current clients to JSON file."""
        result = {
            "interface": self.interface,
            "clients": sorted(
                [c.to_dict() for c in self._clients.values()],
                key=lambda x: x["mac"]
            ),
        }

        with open(self.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    def _parse_csv_entries(self) -> int:
        """Parse CSV file and update clients.

        Returns:
            Number of new/updated MACs.
        """
        if not self.csv_file or not os.path.exists(self.csv_file):
            return 0

        stations = CSVParser.parse_file(self.csv_file)
        new_macs_found = 0

        for station in stations:
            mac = station.mac
            probed_ssids = station.ssids

            if not probed_ssids:
                continue

            is_new_mac = mac not in self._seen_macs

            if is_new_mac:
                self._clients[mac] = ProbeClient(
                    mac=mac,
                    mac_class=MACClassifier.classify(mac),
                    ssids=probed_ssids,
                )
                self._seen_macs.add(mac)
                new_macs_found += 1
            else:
                existing_ssids = set(self._clients[mac].ssids)
                new_ssids = [s for s in probed_ssids if s not in existing_ssids]
                if new_ssids:
                    existing_ssids.update(probed_ssids)
                    self._clients[mac].ssids = sorted(existing_ssids)
                    new_macs_found += 1

        return new_macs_found

    def _start_airodump(self) -> bool:
        """Start airodump-ng in background.

        Returns:
            True on success.
        """
        self.temp_base = tempfile.mktemp(prefix="wifi_scan_")
        self.csv_file = f"{self.temp_base}-01.csv"

        for f in Path("/tmp").glob("wifi_scan_*"):
            try:
                f.unlink()
            except OSError:
                pass

        logger.info("Starting scan on %s (Ctrl+C to stop)...", self.interface)

        cmd = [
            "airodump-ng",
            "--output-format", "csv",
            "--write-interval", "1",
            "-w", self.temp_base,
            self.interface
        ]

        try:
            self.airodump_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info("Running (PID: %d)...", self.airodump_proc.pid)

            time.sleep(2)

            if self.airodump_proc.poll() is not None:
                logger.error("airodump-ng failed to start")
                return False

            return True

        except OSError as err:
            logger.error("airodump-ng error: %s", err)
            return False

    def _monitor_loop(self) -> None:
        """Monitor CSV file and update probes.json in real-time."""
        interval = 2
        elapsed = 0

        while self.airodump_proc and self.airodump_proc.poll() is None:
            if self.interrupted:
                break
            if self.duration and elapsed >= self.duration:
                break

            new_found = self._parse_csv_entries()

            if new_found > 0:
                logger.info(
                    "Found %d new/updated MACs, %d total",
                    new_found,
                    len(self._clients)
                )
                self._save_results()

            time.sleep(interval)
            elapsed += interval

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.airodump_proc and self.airodump_proc.poll() is None:
            self.airodump_proc.terminate()
            try:
                self.airodump_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.airodump_proc.kill()

        new_found = self._parse_csv_entries()
        if new_found > 0 or self._clients:
            logger.info("Saving final results: %d clients", len(self._clients))
            self._save_results()

        if self.restore_managed:
            self._restore_managed_mode()
        else:
            logger.info("Interface %s in monitor mode", self.interface)

        if self.temp_base:
            for f in Path("/tmp").glob(f"{os.path.basename(self.temp_base)}-*"):
                try:
                    f.unlink()
                except OSError:
                    pass

    def run(self) -> int:
        """Run the scan workflow.

        Returns:
            Exit code (0 for success).
        """
        self._load_existing()

        if not self._setup_monitor_mode():
            return 1

        if not self._start_airodump():
            return 1

        self._monitor_loop()

        return 0

    @classmethod
    def detect_interface(cls) -> Optional[str]:
        """Auto-detect a suitable interface.

        Returns:
            Interface name or None.
        """
        result = subprocess.run(
            ["iwconfig"],
            capture_output=True,
            text=True,
            check=False
        )
        for line in result.stdout.split("\n"):
            if "Mode:Master" in line or "Mode:Monitor" in line:
                match = re.match(r"^(\S+)", line)
                if match:
                    return match.group(1)
        return None

    @classmethod
    def check_requirements(cls) -> list[str]:
        """Check for required tools.

        Returns:
            List of missing tools.
        """
        missing = []
        for tool in ["iw", "airodump-ng"]:
            result = subprocess.run(
                ["which", tool],
                capture_output=True,
                check=False
            )
            if result.returncode != 0:
                missing.append(tool)
        return missing
