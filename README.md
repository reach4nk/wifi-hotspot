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
| `setup.sh` | Installs hostapd, dnsmasq, and iptables. Stops services to prevent conflicts. |
| `start.sh` | Starts the hotspot. Configures network, generates SSID/password, and launches services. |
| `stop.sh` | Stops hostapd and dnsmasq, removes iptables rules, and cleans up network config. |
| `monitor.sh` | Shows connected clients, DHCP leases, and ARP table. |
| `find_interfaces.sh` | Displays detected WiFi interfaces (internal and external). |
| `teardown.sh` | Removes all hotspot software packages. |

## Configuration

### Network Settings

| Setting | Value |
|---------|-------|
| Gateway IP | 192.168.50.1/24 |
| DHCP Range | 192.168.50.10 - 192.168.50.100 |
| DHCP Lease Time | 12 hours |
| DNS Server | 8.8.8.8 (Google) |

### WiFi Settings

| Setting | Value |
|---------|-------|
| Standard | IEEE 802.11n (backward compatible with b/g) |
| Mode | g (2.4GHz) |
| Channel | 6 |
| Security | WPA2-PSK with CCMP encryption |

### SSID and Password Format

- **SSID**: `!{Adjective}{Noun}{3-digit-number}🛜` (e.g., `!ColdNet482🛜`)
- **Password**: `{Word}{3-digit-number}{special-char}` (e.g., `WarmLion382#`)

Each run generates a new random SSID and password.

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
```

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

## Troubleshooting

### "No internet interface found"
- Ensure your internal WiFi interface is connected to a network
- Check that `iwconfig` shows an interface in Managed mode

### "No external interface found"
- Ensure you have a second WiFi interface capable of master mode
- Some adapters do not support AP mode

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
2. **Network Setup**: Assigns static IP 192.168.50.1 to the external interface
3. **SSID/Password Generation**: Randomly generates memorable network credentials
4. **DHCP Server**: dnsmasq assigns IPs to connected clients (192.168.50.10-100)
5. **NAT Routing**: iptables masquerades traffic from hotspot clients to the internet
6. **Access Point**: hostapd broadcasts the WiFi network and handles WPA2 authentication
