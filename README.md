# WiFi Hotspot

A lightweight WiFi access point solution for Linux. Create a software hotspot to share your internet connection with other devices.

## Features

- **Python Package**: Pure Python implementation using only standard library modules
- **CLI Interface**: User-friendly command-line interface
- **Hotspot Management**: Start/stop WiFi access points with customizable settings
- **DHCP/DNS**: Integrated dnsmasq for DHCP and DNS services
- **Probe Scanning**: Capture and analyze WiFi probe requests
- **Auto-Detection**: Automatically detect WiFi interfaces and roles
- **Credential Generation**: Generate memorable SSIDs and passwords
- **MAC Classification**: Identify real vs randomized MAC addresses
- **Test Coverage**: 94%+ test coverage with pytest

## Requirements

- Linux system with apt (Debian/Ubuntu-based)
- Python 3.10+
- Two WiFi interfaces (one for internet, one for hotspot)
- Root/sudo privileges

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd wifi-hotspot

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Or install without dev dependencies
pip install -e .
```

## Quick Start

```bash
# Install system dependencies
sudo hotspot setup

# Start the hotspot (random SSID/password)
sudo hotspot start

# Or with custom settings
sudo hotspot start --ssid MyNetwork --password SecretPass123!

# Monitor connected clients
hotspot monitor

# Stop the hotspot
sudo hotspot stop
```

## CLI Commands

### hotspot start

Start a WiFi hotspot.

```bash
hotspot start [OPTIONS]

Options:
  -i, --interface <name>     Hotspot interface (auto-detect if omitted)
  -n, --internet-if <name>  Internet interface (auto-detect if omitted)
      --ssid <name>         SSID name (random if omitted)
      --password <pass>     Password (auto-generate if omitted)
  -e, --encryption <mode>   Encryption: open|wep|wpa|wpa2 (default: wpa2)
  -g, --gateway <IP>        Gateway IP (default: 192.168.50.1)
      --dhcp-start <IP>     DHCP range start (default: 192.168.50.10)
      --dhcp-end <IP>       DHCP range end (default: 192.168.50.100)
      --dns <IP>             DNS server (default: 8.8.8.8)
  -c, --channel <num>        WiFi channel (default: 6)
  -m, --mode <mode>         WiFi mode: b|g|a|n (default: g)
```

### hotspot stop

Stop the hotspot and clean up resources.

```bash
hotspot stop
```

### hotspot monitor

Monitor connected clients and network status.

```bash
hotspot monitor
```

### hotspot scan

Scan for WiFi probe requests.

```bash
hotspot scan [OPTIONS]

Options:
  -i, --interface <name>    WiFi interface (auto-detect if omitted)
  -d, --duration <sec>     Scan duration in seconds
  -o, --output <file>      Output JSON file (default: ./probes.json)
      --cleanup            Restore managed mode after scan
```

### hotspot find-interfaces

Display detected WiFi interfaces.

```bash
hotspot find-interfaces
```

### hotspot setup

Install system dependencies (hostapd, dnsmasq, iptables).

```bash
sudo hotspot setup
```

### hotspot teardown

Remove installed software.

```bash
sudo hotspot teardown
```

## Python Library

Use the hotspot package in your own Python code:

```python
from hotspot import HotspotService
from hotspot.core.interface import InterfaceManager
from hotspot.credentials.generator import CredentialGenerator
from hotspot.scanner.probe import ProbeScanner

# Create and start a hotspot
config = HotspotConfig(
    hotspot_iface="wlan1",
    internet_iface="wlan0",
    ssid="MyNetwork",
    password="SecretPass123!"
)
service = HotspotService(config)
service.start()

# Detect interfaces
internal = InterfaceManager.get_internal_interface()
external = InterfaceManager.get_external_interface()

# Generate credentials
creds = CredentialGenerator.generate(ssid="MyNetwork", encryption="wpa2")

# Scan for probe requests
scanner = ProbeScanner(interface="wlan1", duration=60)
scanner.run()
```

## Project Structure

```
wifi-hotspot/
├── src/hotspot/              # Python package
│   ├── __init__.py          # Package exports
│   ├── __main__.py          # Entry point
│   ├── py.typed             # PEP 561 marker
│   ├── cli/                 # CLI commands
│   │   ├── base.py          # Base classes, argument parser
│   │   ├── start.py         # Start command
│   │   ├── stop.py          # Stop command
│   │   ├── monitor.py       # Monitor command
│   │   ├── scan.py          # Scan command
│   │   ├── setup.py         # Setup command
│   │   ├── teardown.py      # Teardown command
│   │   └── find_interfaces.py  # Find interfaces command
│   ├── core/                # Core utilities
│   │   ├── interface.py     # Interface detection/management
│   │   ├── mac.py           # MAC address utilities
│   │   ├── network.py       # Network configuration
│   │   ├── firewall.py      # iptables management
│   │   └── process.py       # Process management
│   ├── services/            # Service management
│   │   ├── hostapd.py      # hostapd daemon
│   │   ├── dnsmasq.py       # dnsmasq daemon
│   │   └── hotspot.py       # Combined hotspot service
│   ├── credentials/          # Credential handling
│   │   ├── generator.py     # SSID/password generation
│   │   └── validator.py     # Credential validation
│   ├── scanner/             # WiFi scanning
│   │   ├── parser.py       # CSV parsing
│   │   └── probe.py        # Probe request scanner
│   └── utils/               # Utilities
│       ├── logging.py       # Logging configuration
│       ├── config.py        # Configuration dataclass
│       └── exceptions.py    # Custom exceptions
├── scripts/                 # Legacy Bash scripts
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   └── conftest.py          # pytest fixtures
├── pyproject.toml           # Project configuration
└── README.md
```

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/hotspot --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_config.py -v
```

## Configuration Defaults

### Network Settings

| Setting | Default |
|---------|---------|
| Gateway IP | 192.168.50.1/24 |
| DHCP Range | 192.168.50.10 - 192.168.50.100 |
| DHCP Lease | 12 hours |
| DNS Server | 8.8.8.8 |

### WiFi Settings

| Setting | Default |
|---------|---------|
| Mode | g (2.4GHz) |
| Channel | 6 |
| Security | WPA2-PSK |

## Troubleshooting

### No internet interface found
```bash
# Check interfaces
hotspot find-interfaces

# Manually specify
sudo hotspot start --internet-if wlan0
```

### No hotspot interface found
```bash
# Verify adapter supports AP mode
iw list | grep -A10 "Supported interface modes"

# Manually specify
sudo hotspot start --interface wlan1
```

### hostapd failed to start
```bash
# Kill existing hostapd processes
sudo pkill hostapd

# Retry
sudo hotspot start
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/hotspot --cov-report=term-missing
```

## License

MIT License
