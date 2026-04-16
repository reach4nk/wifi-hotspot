#!/bin/bash

# =============================================================================
# find_interfaces.sh - Detect available WiFi interfaces
# =============================================================================
# Utility script to identify which WiFi interfaces are available on the system.
# Run this to see which interface is connected to the internet (managed mode)
# and which is available for hosting (master/monitor mode).

# Get the directory where this script is located (allows running from anywhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load shared functions from common.sh
source "$SCRIPT_DIR/common.sh"

# Detect interfaces using functions from common.sh
# get_internal_interface(): Returns WiFi interface in Managed mode (internet)
# get_external_interface(): Returns WiFi interface in Master/Monitor mode (hotspot)
internal=$(get_internal_interface)
external=$(get_external_interface)

# Display results
echo "Internal Interface: $internal"
echo "External Interface: $external"

# Notes for user:
# - Internal interface: Connected to your router/internet (use for internet)
# - External interface: Available for hosting hotspot
