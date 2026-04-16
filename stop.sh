#!/bin/bash

# =============================================================================
# stop.sh - Stop the WiFi hotspot
# =============================================================================
# Safely stops the hotspot by:
#   1. Killing hostapd and dnsmasq processes
#   2. Removing iptables NAT rules
#   3. Disabling IP forwarding
#   4. Bringing down the hotspot interface

# Load shared functions from common.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Detect which interfaces to use
INTERNET_IF=$(get_internal_interface)  # Interface with internet connection
HOTSPOT_IF=$(get_external_interface)  # Interface hosting the hotspot

# Step 1: Stop the services
# pkill sends SIGTERM to matching processes
# || true: Don't fail if process doesn't exist
echo "Stopping services..."
pkill hostapd || true    # Stop the access point daemon
pkill dnsmasq || true    # Stop the DHCP/DNS server

# Step 2: Remove iptables NAT rules
# These rules allowed traffic forwarding between interfaces
# Without them, clients can't access the internet
echo "Removing iptables rules..."
# -t nat: Work with NAT table
# -D POSTROUTING: Delete the masquerading rule (hides client IPs)
iptables -t nat -D POSTROUTING -o $INTERNET_IF -j MASQUERADE || true
# -D FORWARD: Delete forwarding rules
iptables -D FORWARD -i $INTERNET_IF -o $HOTSPOT_IF -m state --state RELATED,ESTABLISHED -j ACCEPT || true
iptables -D FORWARD -i $HOTSPOT_IF -o $INTERNET_IF -j ACCEPT || true

# Step 3: Disable IP forwarding
# This stops the kernel from forwarding packets between interfaces
sysctl -w net.ipv4.ip_forward=0

# Step 4: Clean up the hotspot interface
# Flush: Remove all IP addresses from the interface
# down: Bring the interface down
ip addr flush dev $HOTSPOT_IF
ip link set $HOTSPOT_IF down

echo "Hotspot stopped."
