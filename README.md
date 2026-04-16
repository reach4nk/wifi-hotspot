# WiFi Hotspot

A lightweight WiFi access point solution for Linux. Create a software hotspot to share your internet connection with other devices.

This project provides a Python package (`src/hotspot/`) using only standard library modules with no external dependencies.

## Requirements

- Linux system with apt (Debian/Ubuntu-based)
- Python 3.10+
- Two WiFi interfaces:
  - **Internal interface**: Connected to the internet (managed mode)
  - **External interface**: Dedicated to hosting the hotspot (master/monitor mode)
- Root/sudo privileges

## System Dependencies

| Tool | Description | License | Repository/Website |
|------|-------------|---------|-------------------|
| [hostapd](https://w1.fi/hostapd/) | IEEE 802.11 AP and authentication servers | BSD-3-Clause | [GitHub](https://w1.fi/hostapd/) |
| [dnsmasq](http://www.thekelleys.org.uk/dnsmasq/) | Lightweight DNS/DHCP server | GPL-2.0 | [GitHub](https://thekelleys.org.uk/dnsmasq/) |
| [airodump-ng](https://www.aircrack-ng.org/) | WiFi security auditing suite | GPL-2.0 | [GitHub](https://github.com/aircrack-ng/aircrack-ng) |
| [iptables](https://www.netfilter.org/projects/iptables/) | Packet filtering and NAT | GPL-2.0 | [Website](https://www.netfilter.org/) |
| [iw](https://wireless.wiki.kernel.org/en/users/documentation/iw) | Linux WiFi configuration | GPL-2.0 | [Website](https://wireless.wiki.kernel.org/) |

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
# Import the library
python3 -c "from hotspot import HotspotService; print('Library imported successfully')"
```

### Build CLI

After `pip install -e .`, the `hotspot` command is available:

```bash
# Show CLI help
hotspot --help

# Run commands (requires sudo for system operations)
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
sudo hotspot setup

# 2. Start the hotspot
sudo hotspot start

# 3. Connect devices
# Use the displayed SSID and password to connect

# 4. Monitor connected clients
hotspot monitor

# 5. Stop the hotspot
sudo hotspot stop
```

## Usage

### Starting the Hotspot

```bash
sudo hotspot start
```

Output displays the generated SSID and password:

```
INFO: Starting hotspot...
INFO:   Hotspot interface: wlan1
INFO:   Internet interface: wlan0
INFO:   Gateway: 192.168.50.1
INFO:   SSID: !ColdNet482🛜
INFO:   Password: WarmLion382#
INFO:   Encryption: wpa2
INFO: Hotspot started successfully

Hotspot started successfully.
  SSID: !ColdNet482🛜
  Password: WarmLion382#
  Gateway: 192.168.50.1
```

### Command Line Options

```bash
hotspot start [OPTIONS]

OPTIONS:
    -i, --interface <name>       External WiFi interface (auto-detect if omitted)
    -n, --internet-if <name>    Internet interface (auto-detect if omitted)
        --ssid <name>           SSID name (random if omitted)
        --password <pass>       Password (auto-generate if omitted)
    -e, --encryption <mode>    Encryption: open|wep|wpa|wpa2 (default: wpa2)
    -g, --gateway <IP>         Gateway IP (default: 192.168.50.1)
        --dhcp-start <IP>      DHCP range start (default: 192.168.50.10)
        --dhcp-end <IP>        DHCP range end (default: 192.168.50.100)
        --dns <IP>             DNS server (default: 8.8.8.8)
    -c, --channel <num>         WiFi channel (default: 6)
    -m, --mode <mode>          WiFi mode: b|g|a|n (default: g)
```

### Examples

```bash
# Default (random SSID/password, WPA2)
sudo hotspot start

# Custom SSID only
sudo hotspot start --ssid MyNetwork

# Custom SSID and password
sudo hotspot start --ssid MyNetwork --password SecretPass123!

# Open network (no password)
sudo hotspot start --ssid FreeWiFi --encryption open

# WEP encryption (auto-generates key)
sudo hotspot start --ssid OldDevice --encryption wep

# WPA encryption (TKIP)
sudo hotspot start --ssid HomeNet --encryption wpa --password SecurePass456!

# Different channel and gateway
sudo hotspot start --ssid HomeNet -c 11 -g 10.0.0.1

# Custom DHCP range
sudo hotspot start --ssid OfficeNet --dhcp-start 10.0.0.50 --dhcp-end 10.0.0.100

# Custom DNS server
sudo hotspot start --ssid HomeNet --dns 1.1.1.1
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
hotspot monitor
```

Displays:
- Connected WiFi stations (MAC addresses)
- DHCP leases (IP, MAC, hostname assignments)
- ARP table for active devices

### Scanning for Probe Requests

```bash
hotspot scan [OPTIONS]
```

Captures WiFi probe requests from devices searching for networks. Features:
- **Real-time updates**: Updates `probes.json` as new MACs/SSIDs are discovered
- **JSON merging**: Combines results with existing `probes.json` (MAC-based deduplication)
- **Persistent results**: Each MAC accumulates all SSIDs it ever probed

Useful for:
- Discovering what networks devices are looking for
- Analyzing client WiFi behavior
- Creating a database of SSIDs for targeted hotspot attacks

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
hotspot scan -d 60

# Scan with custom output file
hotspot scan -d 60 -o scan_results.json

# Continuous scan (Ctrl+C to stop)
hotspot scan
```

#### Output Format

```json
{
  "interface": "wlan1",
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

**Note:** The interface remains in monitor mode after scanning. Use `--cleanup` to restore managed mode.

### Finding Interfaces

```bash
hotspot find-interfaces
```

Displays detected internal (internet-connected) and external (hotspot) interfaces.

### Stopping the Hotspot

```bash
sudo hotspot stop
```

Gracefully stops services and removes network configuration.

### Installing Software

```bash
sudo hotspot setup
```

Installs hostapd, dnsmasq, and iptables.

### Removing Software

```bash
sudo hotspot teardown
```

Removes hostapd and dnsmasq packages and cleans up dependencies.

## Project Structure

```
wifi-hotspot/
├── src/hotspot/           # Python package (src layout)
│   ├── cli/               # CLI commands (start, stop, monitor, scan, setup, teardown)
│   ├── core/               # Core utilities (interface, mac, network, firewall, process)
│   ├── credentials/        # Credential generation and validation
│   ├── scanner/            # WiFi probe scanner (airodump-ng integration)
│   ├── services/           # Service management (hostapd, dnsmasq, hotspot)
│   └── utils/              # Utilities (logging, config, exceptions)
├── scripts/                # Legacy Bash scripts
├── tests/                  # pytest tests
│   └── unit/               # Unit tests with mocks
├── pyproject.toml          # Python project configuration
└── README.md
```

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
- Check that `iw dev` shows an interface in Managed mode
- Manually specify: `hotspot start --internet-if wlan0`

### "No external interface found"
- Ensure you have a second WiFi interface capable of master/monitor mode
- Some adapters do not support AP mode
- Manually specify: `hotspot start --interface wlan1`

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

### Hotspot (start)
1. **Interface Detection**: Uses `iw` to identify WiFi interfaces by mode (Managed vs Master/Monitor)
2. **Network Setup**: Assigns static IP to the external interface (default: 192.168.50.1/24)
3. **SSID/Password Generation**: Randomly generates memorable network credentials (or uses provided values)
4. **DHCP Server**: dnsmasq assigns IPs to connected clients (configurable range)
5. **NAT Routing**: iptables masquerades traffic from hotspot clients to the internet
6. **Access Point**: hostapd broadcasts the WiFi network and handles authentication

### Probe Scanning (scan)
1. **Monitor Mode**: Puts interface in monitor mode to capture all WiFi frames
2. **airodump-ng**: Captures probe request frames from nearby clients
3. **Real-time Parsing**: Monitors CSV output and updates JSON immediately
4. **MAC Deduplication**: Merges results by MAC address, accumulating all probed SSIDs
5. **Persistent Storage**: Results saved to `probes.json` and updated in real-time

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

The project follows Python best practices:
- OOP design with separation of concerns
- Type hints throughout
- ruff/pylint configuration in `pyproject.toml`
- 94%+ test coverage

## License

See project license file.
