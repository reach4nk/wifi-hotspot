#!/bin/bash

# =============================================================================
# common.sh - Shared functions for WiFi hotspot scripts
# =============================================================================
# This file contains common utility functions used by multiple scripts.
# Source this file at the beginning of any script that needs these functions:
#   source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# -----------------------------------------------------------------------------
# get_internal_interface()
# Detects the WiFi interface connected to the internet (managed mode).
# 
# Returns: The interface name (e.g., "wlan0") that is in Managed mode
# 
# How it works:
#   - Uses iwconfig to list wireless interfaces
#   - Searches for interfaces with Mode:Managed (client mode)
#   - Returns the interface name found before the "Mode:Managed" line
# -----------------------------------------------------------------------------
get_internal_interface() {
    # iwconfig: Lists wireless interface configuration
    # grep -B 1 'Mode:Managed': Finds the line BEFORE "Mode:Managed"
    # grep -o '^[^ ]*': Extracts the first word (interface name) from that line
    internal_interface=$(iwconfig 2>/dev/null | grep -B 1 'Mode:Managed' | grep -o '^[^ ]*')
    echo "$internal_interface"
}

# -----------------------------------------------------------------------------
# get_external_interface()
# Detects the WiFi interface available for hosting (master or monitor mode).
#
# Returns: The interface name in Master or Monitor mode
#
# Why both Master and Monitor?
#   - Master mode: Interface is already set up as an access point
#   - Monitor mode: Interface is used by scan.sh to capture probe requests
#   - Both can be used by start.sh to host the hotspot
# -----------------------------------------------------------------------------
get_external_interface() {
    # grep -E 'Mode:(Master|Monitor)': Matches either Master or Monitor mode
    external_interface=$(iwconfig 2>/dev/null | grep -B 1 -E 'Mode:(Master|Monitor)' | grep -o '^[^ ]*')
    echo "$external_interface"
}
