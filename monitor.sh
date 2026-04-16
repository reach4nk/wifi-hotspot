#!/bin/bash
# Exit immediately if a command fails
set -e

# =============================================================================
# monitor.sh - Monitor connected clients on the hotspot
# =============================================================================
# Displays real-time information about devices connected to the hotspot:
#   1. Connected WiFi stations (from hostapd)
#   2. DHCP leases (assigned IPs and hostnames)
#   3. ARP table (active devices on the network)

# Get script directory and load shared functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get the interface hosting the hotspot
HOTSPOT_IF=$(get_external_interface)

# Paths to data files
LEASE_FILE="/var/lib/misc/dnsmasq.leases"    # DHCP lease information
CTRL_PATH="/var/run/hostapd"                # hostapd control socket

# Clear the screen for a clean display
clear

# Display header with interface info
echo "========================================"
echo " Hotspot Monitor"
echo " Interface: $HOTSPOT_IF"
echo "========================================"
echo ""

# ---------------------------------------------------------------------------
# Section 1: Connected WiFi Stations
# ---------------------------------------------------------------------------
# Shows devices currently associated with the access point
echo "Connected WiFi Stations (MAC level):"
echo "----------------------------------------"

# Check if hostapd control socket exists
# -S: Socket exists
if [ -S "$CTRL_PATH/$HOTSPOT_IF" ]; then
    # hostapd_cli: Command-line tool to communicate with hostapd
    # all_sta: List all associated stations
    # awk: Parse the output to extract MAC, signal, and connection time
    hostapd_cli -p $CTRL_PATH -i $HOTSPOT_IF all_sta | \
    awk '/^STA/ {mac=$2} /signal=/ {sig=$1} /connected_time=/ {time=$1; printf "MAC: %-18s Signal: %-10s %s\n", mac, sig, time}'
else
    echo "hostapd control socket not found."
fi

# ---------------------------------------------------------------------------
# Section 2: DHCP Leases
# ---------------------------------------------------------------------------
# Shows which IPs have been assigned by dnsmasq
echo ""
echo "DHCP Leases (IP / MAC / Hostname):"
echo "----------------------------------------"

# Check if DHCP lease file exists
# Format: timestamp mac ip hostname
if [ -f "$LEASE_FILE" ]; then
    # awk: Extract fields 3 (IP), 2 (MAC), 4 (hostname)
    awk '{printf "IP: %-15s MAC: %-18s Hostname: %s\n", $3, $2, $4}' $LEASE_FILE
else
    echo "No lease file found."
fi

# ---------------------------------------------------------------------------
# Section 3: ARP Table
# ---------------------------------------------------------------------------
# Shows all devices known on the network (from ARP cache)
echo ""
echo "ARP Table (Active Devices):"
echo "----------------------------------------"

# ip neigh show: Display ARP cache for the interface
ip neigh show dev $HOTSPOT_IF

echo ""
