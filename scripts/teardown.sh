#!/bin/bash

# =============================================================================
# teardown.sh - Remove all hotspot software
# =============================================================================
# WARNING: This completely removes hostapd and dnsmasq from your system.
# Use only if you want to uninstall the hotspot functionality.

# Remove the hotspot software packages and their configuration files
# --purge: Also removes configuration files
apt remove --purge -y hostapd dnsmasq

# Remove automatically installed dependencies that are no longer needed
apt autoremove -y

echo "Removed hotspot software."
