#!/usr/bin/env python3
"""
scan.py - Capture WiFi probe requests and merge results in real-time

Uses airodump-ng to capture probe request frames from nearby clients.
Monitors the CSV output file and updates probes.json immediately
when new MACs or SSIDs are discovered.
"""

import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional


class ScanSession:
    def __init__(self, interface: str, duration: Optional[int] = None,
                 output: Optional[str] = None, restore_managed: bool = False):
        self.interface = interface
        self.duration = duration
        self.output = output or "./probes.json"
        self.restore_managed = restore_managed
        self.temp_base = None
        self.csv_file = None
        self.airodump_pid = None
        self.interrupted = False
        
        # In-memory clients dictionary: mac -> {'class': ..., 'mac': ..., 'ssids': [...]}
        self.clients: Dict[str, Dict] = {}
        # Track seen MACs to detect new entries
        self.seen_macs: set = set()
        
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def _handle_interrupt(self, signum, frame):
        print("\n[Interrupt] Saving and stopping...")
        self.interrupted = True
    
    def _is_valid_mac(self, mac: str) -> bool:
        """Check if string looks like a valid MAC address."""
        if not mac:
            return False
        parts = mac.split(':')
        if len(parts) != 6:
            return False
        return all(len(p) == 2 and all(c in '0123456789abcdefABCDEF' for c in p) for p in parts)
    
    def _is_randomized_mac(self, mac: str) -> str:
        """Detect MAC address randomization."""
        if not self._is_valid_mac(mac):
            return "unknown"
        first_byte = mac.split(':')[0].upper()
        if len(first_byte) >= 2 and first_byte[1] in '26AE':
            return "local"
        return "actual"
    
    def _setup_monitor_mode(self):
        """Ensure interface is in monitor mode."""
        try:
            result = subprocess.run(
                ['iw', 'dev', self.interface, 'info'],
                capture_output=True, text=True
            )
            if 'type Monitor' in result.stdout:
                print(f"[Setup] Interface {self.interface} already in monitor mode")
                subprocess.run(['ip', 'link', 'set', self.interface, 'up'],
                             capture_output=True)
                return True
            
            print(f"[Setup] Enabling monitor mode on {self.interface}...")
            subprocess.run(['ip', 'link', 'set', self.interface, 'down'],
                         capture_output=True)
            subprocess.run(['iw', 'dev', self.interface, 'set', 'type', 'monitor'],
                         capture_output=True)
            subprocess.run(['ip', 'link', 'set', self.interface, 'up'],
                         capture_output=True)
            return True
        except Exception as e:
            print(f"[Error] Failed to setup monitor mode: {e}", file=sys.stderr)
            return False
    
    def _restore_managed_mode(self):
        """Restore managed mode on interface."""
        try:
            print(f"[Cleanup] Restoring managed mode on {self.interface}...")
            subprocess.run(['ip', 'link', 'set', self.interface, 'down'],
                         capture_output=True)
            subprocess.run(['iw', 'dev', self.interface, 'set', 'type', 'managed'],
                         capture_output=True)
            subprocess.run(['ip', 'link', 'set', self.interface, 'up'],
                         capture_output=True)
        except Exception as e:
            print(f"[Error] Failed to restore managed mode: {e}", file=sys.stderr)
    
    def _load_existing(self):
        """Load existing probes.json into memory."""
        if not os.path.exists(self.output):
            print(f"[Load] No existing {self.output}, starting fresh")
            return
        
        try:
            with open(self.output, 'r') as f:
                data = json.load(f)
            
            if 'clients' in data:
                for client in data['clients']:
                    mac = client.get('mac', '')
                    if mac and self._is_valid_mac(mac):
                        self.clients[mac] = {
                            'class': client.get('class', 'unknown'),
                            'mac': mac,
                            'ssids': list(client.get('ssids', []))
                        }
            
            print(f"[Load] Loaded {len(self.clients)} existing clients")
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Warn] Could not load existing file: {e}", file=sys.stderr)
    
    def _save_results(self):
        """Save current clients to JSON file."""
        result = {
            'interface': self.interface,
            'clients': sorted(self.clients.values(), key=lambda x: x['mac'])
        }
        
        with open(self.output, 'w') as f:
            json.dump(result, f, indent=2)
    
    def _parse_csv_entries(self) -> int:
        """Parse CSV file and update clients dictionary. Returns count of updates."""
        if not self.csv_file or not os.path.exists(self.csv_file):
            return 0
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            return 0
        
        # Find the Station MAC section
        if 'Station MAC' not in content:
            return 0
        
        # Extract lines after "Station MAC"
        station_section = content.split('Station MAC')[1]
        lines = station_section.strip().split('\n')
        
        # Skip the first line (header)
        if len(lines) <= 1:
            return 0
        
        new_macs_found = 0
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            # Parse CSV line
            try:
                reader = csv.reader([line])
                row = next(reader)
            except:
                continue
            
            if not row or len(row) < 1:
                continue
            
            mac = row[0].strip()
            
            # Validate MAC
            if not self._is_valid_mac(mac):
                continue
            
            # Extract probed SSIDs (columns 7 onwards)
            probed_ssids = []
            if len(row) > 6:
                for ssid in row[6:]:
                    ssid = ssid.strip()
                    if ssid:
                        probed_ssids.append(ssid)
            
            if not probed_ssids:
                continue
            
            # Check if this is a new MAC
            is_new_mac = mac not in self.seen_macs
            
            if is_new_mac:
                self.clients[mac] = {
                    'class': self._is_randomized_mac(mac),
                    'mac': mac,
                    'ssids': probed_ssids
                }
                self.seen_macs.add(mac)
                new_macs_found += 1
            else:
                # Merge SSIDs for existing MAC
                existing_ssids = set(self.clients[mac]['ssids'])
                new_ssids = [s for s in probed_ssids if s not in existing_ssids]
                if new_ssids:
                    existing_ssids.update(probed_ssids)
                    self.clients[mac]['ssids'] = sorted(existing_ssids)
                    new_macs_found += 1
        
        return new_macs_found
    
    def _start_airodump(self) -> bool:
        """Start airodump-ng in background."""
        self.temp_base = tempfile.mktemp(prefix='wifi_scan_')
        self.csv_file = f"{self.temp_base}-01.csv"
        
        # Clean up any existing temp files
        for f in Path('/tmp').glob('wifi_scan_*'):
            try:
                f.unlink()
            except:
                pass
        
        print(f"[Scan] Starting on {self.interface} (Ctrl+C to stop)...")
        
        cmd = [
            'airodump-ng',
            '--output-format', 'csv',
            '--write-interval', '1',
            '-w', self.temp_base,
            self.interface
        ]
        
        try:
            self.airodump_pid = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"[Scan] Running (PID: {self.airodump_pid.pid})...")
            
            # Wait for CSV file to be created
            time.sleep(2)
            
            if self.airodump_pid.poll() is not None:
                print("[Error] airodump-ng failed to start", file=sys.stderr)
                return False
            
            return True
            
        except Exception as e:
            print(f"[Error] airodump-ng error: {e}", file=sys.stderr)
            return False
    
    def _monitor_loop(self):
        """Monitor CSV file and update probes.json in real-time."""
        interval = 2
        elapsed = 0
        
        while self.airodump_pid and self.airodump_pid.poll() is None:
            if self.interrupted:
                break
            if self.duration and elapsed >= self.duration:
                break
            
            # Check for new entries
            new_found = self._parse_csv_entries()
            
            if new_found > 0:
                print(f"[Update] Found {new_found} new/updated MACs, {len(self.clients)} total")
                self._save_results()
            
            time.sleep(interval)
            elapsed += interval
    
    def cleanup(self):
        """Clean up resources."""
        # Stop airodump if still running
        if self.airodump_pid and self.airodump_pid.poll() is None:
            self.airodump_pid.terminate()
            try:
                self.airodump_pid.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.airodump_pid.kill()
        
        # Do a final CSV parse to catch any remaining entries
        new_found = self._parse_csv_entries()
        if new_found > 0 or self.clients:
            print(f"[Final] Saving final results: {len(self.clients)} clients")
            self._save_results()
        
        # Restore managed mode if requested
        if self.restore_managed:
            self._restore_managed_mode()
        else:
            print(f"[Cleanup] Interface {self.interface} in monitor mode")
        
        # Clean up temp files
        if self.temp_base:
            for f in Path('/tmp').glob(f'{os.path.basename(self.temp_base)}-*'):
                try:
                    f.unlink()
                except:
                    pass
    
    def run(self):
        """Main scan workflow."""
        # Load existing data first
        self._load_existing()
        
        # Set up monitor mode
        if not self._setup_monitor_mode():
            return 1
        
        # Start airodump-ng
        if not self._start_airodump():
            return 1
        
        # Monitor and update in real-time
        self._monitor_loop()
        
        return 0


def main():
    parser = argparse.ArgumentParser(
        description='Scan for WiFi probe requests and merge results in real-time',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s -d 60              Scan for 60 seconds
  %(prog)s -i wlan1 -d 30    Scan on specific interface
  %(prog)s -o probes.json     Custom output file
  %(prog)s --cleanup          Restore managed mode after scan
        '''
    )
    
    parser.add_argument('-i', '--interface', help='WiFi interface (auto-detect if omitted)')
    parser.add_argument('-d', '--duration', type=int, help='Scan duration in seconds')
    parser.add_argument('-o', '--output', help='Output JSON file (default: ./probes.json)')
    parser.add_argument('--cleanup', action='store_true', help='Restore managed mode after scan')
    
    args = parser.parse_args()
    
    # Check for root
    if os.geteuid() != 0:
        print("[Error] This script must be run as root", file=sys.stderr)
        return 1
    
    # Check for required tools
    for tool in ['iw', 'airodump-ng']:
        if subprocess.run(['which', tool], capture_output=True).returncode != 0:
            print(f"[Error] Required tool not found: {tool}", file=sys.stderr)
            return 1
    
    # Auto-detect interface if not specified
    interface = args.interface
    if not interface:
        print("[Detect] Auto-detecting interface...")
        try:
            result = subprocess.run(
                ['iwconfig'],
                capture_output=True, text=True
            )
            for line in result.stdout.split('\n'):
                if 'Mode:Master' in line or 'Mode:Monitor' in line:
                    interface = line.split()[0]
                    break
            
            if not interface:
                print("[Error] No monitor or master interface found", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"[Error] Interface detection failed: {e}", file=sys.stderr)
            return 1
    
    print(f"[Detect] Using: {interface}")
    
    # Run scan
    session = ScanSession(
        interface=interface,
        duration=args.duration,
        output=args.output,
        restore_managed=args.cleanup
    )
    
    try:
        return session.run()
    finally:
        session.cleanup()


if __name__ == '__main__':
    sys.exit(main())
