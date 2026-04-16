# WiFi Hotspot

A lightweight Bash-based WiFi access point solution for Linux. Create a software hotspot to share your internet connection with other devices.

## Requirements

- Linux system with apt (Debian/Ubuntu-based)
- Two WiFi interfaces:
  - **Internal interface**: Connected to the internet (managed mode)
  - **External interface**: Dedicated to hosting the hotspot (master mode)
- Root/sudo privileges

## Quick Start

```bash
# 1. Install dependencies
sudo ./setup.sh

# 2. Start the hotspot
sudo ./start.sh

# 3. Connect devices
# Use the displayed SSID and password to connect

# 4. Monitor connected clients
./monitor.sh

# 5. Stop the hotspot
sudo ./stop.sh
```

## Scripts

| Script | Description |
|--------|-------------|
| `common.sh` | Shared library with interface detection functions. |
| `setup.sh` | Installs hostapd, dnsmasq, and iptables. Stops services to prevent conflicts. |
| `start.sh` | Starts the hotspot. Configurable via CLI arguments. |
| `stop.sh` | Stops hostapd and dnsmasq, removes iptables rules, and cleans up network config. |
| `monitor.sh` | Shows connected clients, DHCP leases, and ARP table. |
| `find_interfaces.sh` | Displays detected WiFi interfaces (internal and external). |
| `teardown.sh` | Removes all hotspot software packages. |

## Usage

### Starting the Hotspot

```bash
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
sudo ./start.sh

# Custom SSID only
sudo ./start.sh --ssid MyNetwork

# Custom SSID and password
sudo ./start.sh --ssid MyNetwork --password SecretPass123!

# Open network (no password)
sudo ./start.sh --ssid FreeWiFi --encryption open

# WEP encryption (auto-generates key)
sudo ./start.sh --ssid OldDevice --encryption wep

# WPA encryption (TKIP)
sudo ./start.sh --ssid HomeNet --encryption wpa --password SecurePass456!

# Different channel and gateway
sudo ./start.sh --ssid HomeNet -c 11 -g 10.0.0.1

# Custom DHCP range
sudo ./start.sh --ssid OfficeNet --dhcp-start 10.0.0.50 --dhcp-end 10.0.0.100

# Custom DNS server
sudo ./start.sh --ssid HomeNet --dns 1.1.1.1
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
./monitor.sh
```

Displays:
- Connected WiFi stations (MAC address, signal strength, connection time)
- DHCP leases (IP, MAC, hostname assignments)
- ARP table for active devices

### Stopping the Hotspot

```bash
sudo ./stop.sh
```

Gracefully stops services and removes network configuration.

### Finding Interfaces

```bash
./find_interfaces.sh
```

Displays detected internal (internet-connected) and external (hotspot) interfaces.

### Removing Software

```bash
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

1. **Interface Detection**: Uses `iwconfig` to identify WiFi interfaces by mode (Managed vs Master)
2. **Network Setup**: Assigns static IP to the external interface (default: 192.168.50.1/24)
3. **SSID/Password Generation**: Randomly generates memorable network credentials (or uses provided values)
4. **DHCP Server**: dnsmasq assigns IPs to connected clients (configurable range)
5. **NAT Routing**: iptables masquerades traffic from hotspot clients to the internet
6. **Access Point**: hostapd broadcasts the WiFi network and handles authentication
