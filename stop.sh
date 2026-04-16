#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

INTERNET_IF=$(get_internal_interface)
HOTSPOT_IF=$(get_external_interface)

echo "Stopping services..."
pkill hostapd || true
pkill dnsmasq || true

echo "Removing iptables rules..."
iptables -t nat -D POSTROUTING -o $INTERNET_IF -j MASQUERADE || true
iptables -D FORWARD -i $INTERNET_IF -o $HOTSPOT_IF -m state --state RELATED,ESTABLISHED -j ACCEPT || true
iptables -D FORWARD -i $HOTSPOT_IF -o $INTERNET_IF -j ACCEPT || true

sysctl -w net.ipv4.ip_forward=0

ip addr flush dev $HOTSPOT_IF
ip link set $HOTSPOT_IF down

echo "Hotspot stopped."
