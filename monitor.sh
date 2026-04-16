#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

HOTSPOT_IF=$(get_external_interface)
LEASE_FILE="/var/lib/misc/dnsmasq.leases"
CTRL_PATH="/var/run/hostapd"

clear

echo "========================================"
echo " Hotspot Monitor"
echo " Interface: $HOTSPOT_IF"
echo "========================================"
echo ""

echo "Connected WiFi Stations (MAC level):"
echo "----------------------------------------"

if [ -S "$CTRL_PATH/$HOTSPOT_IF" ]; then
    hostapd_cli -p $CTRL_PATH -i $HOTSPOT_IF all_sta | \
    awk '/^STA/ {mac=$2} /signal=/ {sig=$1} /connected_time=/ {time=$1; printf "MAC: %-18s Signal: %-10s %s\n", mac, sig, time}'
else
    echo "hostapd control socket not found."
fi

echo ""
echo "DHCP Leases (IP / MAC / Hostname):"
echo "----------------------------------------"

if [ -f "$LEASE_FILE" ]; then
    awk '{printf "IP: %-15s MAC: %-18s Hostname: %s\n", $3, $2, $4}' $LEASE_FILE
else
    echo "No lease file found."
fi

echo ""
echo "ARP Table (Active Devices):"
echo "----------------------------------------"
ip neigh show dev $HOTSPOT_IF

echo ""
