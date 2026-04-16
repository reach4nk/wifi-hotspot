#!/bin/bash

# Function to get the internal Wi-Fi interface
get_internal_interface() {
    # Use iwconfig to find the internal interface
    internal_interface=$(iwconfig 2>/dev/null | grep -B 1 'Mode:Managed' | grep -o '^[^ ]*')
    echo "$internal_interface"
}

# Function to get the external Wi-Fi interface
get_external_interface() {
    # Use iwconfig to find the external interface
    external_interface=$(iwconfig 2>/dev/null | grep -B 1 'Mode:Master' | grep -o '^[^ ]*')
    echo "$external_interface"
}

# Check the interfaces
internal=$(get_internal_interface)
external=$(get_external_interface)

# Output the results
echo "Internal Interface: $internal"
echo "External Interface: $external"

