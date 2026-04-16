#!/bin/bash

# Function to get the internal Wi-Fi interface
get_internal_interface() {
    internal_interface=$(iwconfig 2>/dev/null | grep -B 1 'Mode:Managed' | grep -o '^[^ ]*')
    echo "$internal_interface"
}

# Function to get the external Wi-Fi interface
get_external_interface() {
    external_interface=$(iwconfig 2>/dev/null | grep -B 1 'Mode:Master' | grep -o '^[^ ]*')
    echo "$external_interface"
}

# Get interfaces
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
