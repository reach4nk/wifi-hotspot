# WiFi Hotspot

A lightweight WiFi access point solution for Linux. Create a software hotspot to share your internet connection with other devices.

This project provides both a Python package (`src/hotspot/`) and Bash scripts (`scripts/`) for managing WiFi hotspots. The Python version uses only standard library modules with no external dependencies.

## Requirements

- Linux system with apt (Debian/Ubuntu-based)
- Python 3.10+ (for Python package)
- Two WiFi interfaces:
  - **Internal interface**: Connected to the internet (managed mode)
  - **External interface**: Dedicated to hosting the hotspot (master mode)
- Root/sudo privileges

## System Dependencies

This project relies on the following system tools (installed via `setup.sh` or `setup.py`):

| Tool | Description | License | Repository/Website |
|------|-------------|---------|-------------------|
| [hostapd](https://w1.fi/hostapd/) | IEEE 802.11 AP and authentication servers | BSD-3-Clause | [GitHub](https://w1.fi/hostapd/) |
| [dnsmasq](http://www.thekelleys.org.uk/dnsmasq/) | Lightweight DNS/DHCP server | GPL-2.0 | [GitHub](https://thekelleys.org.uk/dnsmasq/) |
| [aircrack-ng](https://www.aircrack-ng.org/) | WiFi security auditing suite (airodump-ng) | GPL-2.0 | [GitHub](https://github.com/aircrack-ng/aircrack-ng) |
| [iptables](https://www.netfilter.org/projects/iptables/) | Packet filtering and NAT | GPL-2.0 | [Website](https://www.netfilter.org/) |
| [wireless-tools](https://hewlettpackard.github.io/wireless-tools/) | Linux WiFi configuration (iwconfig, iw) | GPL-2.0 | [GitHub](https://hewlettpackard.github.io/wireless-tools/) |

## Setup and Installation

### Download

```bash
git clone <repository-url>
cd wifi-hotspot
```

### Python Setup

```bash
# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install the package with dev dependencies
pip install -e ".[dev]"

# Or install without dev dependencies
pip install -e .
```

### Build Library

The package is installed in editable mode. To verify:

```bash
# Import the library (or use installed package after pip install -e .)
PYTHONPATH=src python3 -c "from hotspot import HotspotService; print('Library imported successfully')"
```

### Build CLI

After `pip install -e .`, the `hotspot` command is available:

```bash
# Show CLI help
hotspot --help

# Run commands (may require sudo for system operations)
hotspot start --ssid MyNetwork
hotspot stop
hotspot monitor
hotspot scan -d 60
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src/hotspot --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_config.py -v
```

## Quick Start

```bash
# 1. Install dependencies
sudo ./setup.py

# 2. Start the hotspot
sudo ./start.py

# 3. Connect devices
# Use the displayed SSID and password to connect

# 4. Monitor connected clients
./monitor.py

# 5. Stop the hotspot
sudo ./stop.py
```

## Project Structure

```
wifi-hotspot/
├── src/hotspot/           # Python package (src layout)
│   ├── cli/               # CLI commands
│   ├── core/              # Core utilities (interface, mac, network, firewall)
│   ├── credentials/       # Credential generation and validation
│   ├── scanner/           # WiFi probe scanner
│   ├── services/          # Service management (hostapd, dnsmasq)
│   └── utils/             # Utilities (logging, config, exceptions)
├── scripts/               # Bash scripts (legacy)
├── tests/                 # pytest tests
│   ├── unit/             # Unit tests
│   └── fixtures/          # Test fixtures
├── pyproject.toml         # Python project configuration
└── README.md
```

## Usage

### Python Package

```bash
# Install the package
pip install -e .

# Run CLI commands
hotspot start --ssid MyNetwork
hotspot stop
hotspot monitor
hotspot scan -d 60
```

### Bash Scripts

```bash
# Install dependencies
sudo ./scripts/setup.sh

# Start the hotspot
sudo ./scripts/start.sh --ssid MyNetwork

# Stop the hotspot
sudo ./scripts/stop.sh
```

## Usage

### Starting the Hotspot

```bash
sudo ./start.py
# or
sudo ./start.sh
```

Output displays the generated SSID and password:

```
[1] Configuring interface...
[2] Writing hostapd config...
[3] Writing dnsmasq config...
[4] Enabling IP forwarding...
[5] Setting iptables rules...
[6] Starting dnsmasq...
[7] Starting hostapd...

Hotspot started.
SSID: !ColdNet482🛜
Password: WarmLion382#
Encryption: wpa2
```

### Command Line Options

```bash
./start.py [OPTIONS]
# or
./start.sh [OPTIONS]

OPTIONS:
    -i, --interface <name>       External WiFi interface (auto-detect if omitted)
    -n, --internet-if <name>     Internet interface (auto-detect if omitted)
        --ssid <name>            SSID name (random if omitted)
        --password <pass>       Password (auto-generate if omitted)
    -e, --encryption <mode>     Encryption: open|wep|wpa|wpa2 (default: wpa2)
    -g, --gateway <IP>           Gateway IP (default: 192.168.50.1)
        --dhcp-start <IP>       DHCP range start (default: 192.168.50.10)
        --dhcp-end <IP>          DHCP range end (default: 192.168.50.100)
        --dns <IP>               DNS server (default: 8.8.8.8)
    -c, --channel <num>          WiFi channel (default: 6)
    -m, --mode <mode>            WiFi mode: b|g|a|n (default: g)
    -h, --help                   Show help message
```

### Examples

```bash
# Default (random SSID/password, WPA2)
sudo ./start.py

# Custom SSID only
sudo ./start.py --ssid MyNetwork

# Custom SSID and password
sudo ./start.py --ssid MyNetwork --password SecretPass123!

# Open network (no password)
sudo ./start.py --ssid FreeWiFi --encryption open

# WEP encryption (auto-generates key)
sudo ./start.py --ssid OldDevice --encryption wep

# WPA encryption (TKIP)
sudo ./start.py --ssid HomeNet --encryption wpa --password SecurePass456!

# Different channel and gateway
sudo ./start.py --ssid HomeNet -c 11 -g 10.0.0.1

# Custom DHCP range
sudo ./start.py --ssid OfficeNet --dhcp-start 10.0.0.50 --dhcp-end 10.0.0.100

# Custom DNS server
sudo ./start.py --ssid HomeNet --dns 1.1.1.1
```

### Encryption Modes

| Mode | Security | Password |
|------|----------|----------|
| `open` | None (open network) | Not required |
| `wep` | WEP (legacy) | Auto-generated 26-character hex key |
| `wpa` | WPA (TKIP) | 8-63 characters |
| `wpa2` | WPA2 (CCMP) | 8-63 characters |

### Monitoring Connected Clients

```bash
./monitor.py
# or
./monitor.sh
```

Displays:
- Connected WiFi stations (MAC address, signal strength, connection time)
- DHCP leases (IP, MAC, hostname assignments)
- ARP table for active devices

### Scanning for Probe Requests

```bash
python3 ./scan.py [OPTIONS]
```

Captures WiFi probe requests from devices searching for networks. Features:
- **Real-time updates**: Updates `probes.json` as new MACs/SSIDs are discovered
- **JSON merging**: Combines results with existing `probes.json` (MAC-based deduplication)
- **Persistent results**: Each MAC accumulates all SSIDs it ever probed

Useful for:
- Discovering what networks devices are looking for
- Creating a database of SSIDs for targeted hotspot attacks
- Analyzing client WiFi behavior

#### Options

| Option | Description |
|--------|-------------|
| `-i, --interface` | WiFi interface (auto-detect if omitted) |
| `-d, --duration` | Scan duration in seconds (default: continuous) |
| `-o, --output` | Output JSON file (default: ./probes.json) |
| `--cleanup` | Restore managed mode after scan |

#### Examples

```bash
# Scan for 60 seconds
python3 ./scan.py -d 60

# Scan with custom output file
python3 ./scan.py -d 60 -o scan_results.json

# Continuous scan (Ctrl+C to stop)
python3 ./scan.py
```

#### Output Format

```json
{
  "interface": "wlxf4f26d1c2b2b",
  "clients": [
    {
      "class": "actual",
      "mac": "2C:BE:EE:0A:FD:AA",
      "ssids": ["HV_GT", "Marriott_CONFERENCE", "Marriott_GUEST"]
    },
    {
      "class": "local",
      "mac": "82:0C:D0:C6:A8:41",
      "ssids": ["Mariott_STUDIO", "Marriott_LOBBY"]
    }
  ]
}
```

- `class: "actual"` - Real MAC address
- `class: "local"` - Randomized MAC address (2nd char of 1st byte is 2, 6, A, or E)

**Note:** The interface remains in monitor mode after scanning for use with `start.sh`. Use `--cleanup` to restore managed mode.

#### Deprecated: scan.sh

The legacy `scan.sh` is deprecated. Use `scan.py` instead for:
- Better real-time CSV monitoring
- Proper JSON merging with deduplication
- Cleaner Python-based parsing

### Stopping the Hotspot

```bash
sudo ./stop.py
# or
sudo ./stop.sh
```

Gracefully stops services and removes network configuration.

### Finding Interfaces

```bash
./find_interfaces.py
# or
./find_interfaces.sh
```

Displays detected internal (internet-connected) and external (hotspot) interfaces.

### Removing Software

```bash
sudo ./teardown.py
# or
sudo ./teardown.sh
```

Removes hostapd and dnsmasq packages and cleans up dependencies.

## Configuration

### Default Network Settings

| Setting | Value |
|---------|-------|
| Gateway IP | 192.168.50.1/24 |
| DHCP Range | 192.168.50.10 - 192.168.50.100 |
| DHCP Lease Time | 12 hours |
| DNS Server | 8.8.8.8 (Google) |

### Default WiFi Settings

| Setting | Value |
|---------|-------|
| Standard | IEEE 802.11n (backward compatible with b/g) |
| Mode | g (2.4GHz) |
| Channel | 6 |
| Security | WPA2-PSK with CCMP encryption |

### SSID and Password Format (Auto-generated)

- **SSID**: `!{Adjective}{Noun}{3-digit-number}🛜` (e.g., `!ColdNet482🛜`)
- **Password**: `{Word}{3-digit-number}{special-char}` (e.g., `WarmLion382#`)

## Troubleshooting

### "No internet interface found"
- Ensure your internal WiFi interface is connected to a network
- Check that `iwconfig` shows an interface in Managed mode
- Manually specify: `--internet-if wlan0`

### "No external interface found"
- Ensure you have a second WiFi interface capable of master mode
- Some adapters do not support AP mode
- Manually specify: `--interface wlan1`

### "hostapd failed to start"
- Check that no other hostapd process is running: `pkill hostapd`
- Verify your WiFi adapter supports master mode: `iw list`

### Clients cannot connect
- Check if hostapd is running: `ps aux | grep hostapd`
- Verify iptables rules: `sudo iptables -t nat -L`
- Check dnsmasq logs: `journalctl -u dnsmasq`

### Internet not shared
- Verify IP forwarding is enabled: `sysctl net.ipv4.ip_forward`
- Check the internal interface is up and has an IP address

## How It Works

### Hotspot (start.sh)
1. **Interface Detection**: Uses `iwconfig` to identify WiFi interfaces by mode (Managed vs Master)
2. **Network Setup**: Assigns static IP to the external interface (default: 192.168.50.1/24)
3. **SSID/Password Generation**: Randomly generates memorable network credentials (or uses provided values)
4. **DHCP Server**: dnsmasq assigns IPs to connected clients (configurable range)
5. **NAT Routing**: iptables masquerades traffic from hotspot clients to the internet
6. **Access Point**: hostapd broadcasts the WiFi network and handles authentication

### Probe Scanning (scan.py)
1. **Monitor Mode**: Puts interface in monitor mode to capture all WiFi frames
2. **airodump-ng**: Captures probe request frames from nearby clients
3. **Real-time Parsing**: Python monitors CSV output and updates JSON immediately
4. **MAC Deduplication**: Merges results by MAC address, accumulating all probed SSIDs
5. **Persistent Storage**: Results saved to `probes.json` and updated in real-time

### Architecture

The project uses a modular design with library + CLI separation:

**Python Package (`src/hotspot/`):**
- `hotspot.core`: Core utilities (interface detection, MAC classification, process management, network, firewall)
- `hotspot.credentials`: SSID/password generation and validation
- `hotspot.services`: hostapd/dnsmasq lifecycle management
- `hotspot.scanner`: WiFi probe request scanning
- `hotspot.cli`: Command-line interface commands
- `hotspot.utils`: Logging, configuration, exceptions

**Bash Scripts (`scripts/`):**
- Same module structure with equivalent functionality in Bash

## Development

### Running Tests

```bash
# Install dev dependencies (already included with pip install -e ".[dev]")
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/hotspot --cov-report=term-missing
```

### Code Quality

The project follows Python best practices and includes ruff configuration in `pyproject.toml`.
