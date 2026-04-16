#!/bin/bash
# Exit immediately if a command fails
set -e

# =============================================================================
# setup.sh - Install and configure required software for WiFi hotspot
# =============================================================================

# Update package lists to get latest versions
apt update

# Install required packages:
#   hostapd  - WiFi access point daemon (creates the hotspot)
#   dnsmasq  - DHCP and DNS server (assigns IPs to clients)
#   iptables - Firewall for NAT/routing (shares internet connection)
apt install -y hostapd dnsmasq iptables

# Stop and disable services to prevent conflicts
# These services may try to use hostapd/dnsmasq configurations that interfere
# with our scripts. By stopping them, we ensure our scripts have full control.
echo "Stopping services"
systemctl stop hostapd || true
systemctl stop dnsmasq || true
systemctl disable hostapd || true
systemctl disable dnsmasq || true

echo "Setup complete."
