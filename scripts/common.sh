#!/bin/bash
# =============================================================================
# common.sh - Core shared utilities for WiFi hotspot scripts
# =============================================================================
# This file contains common utility functions used by multiple scripts.
# Source this file at the beginning of any script that needs these functions:
#   source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# =============================================================================
# INTERFACE DETECTION
# =============================================================================

# -----------------------------------------------------------------------------
# get_internal_interface()
# Detects the WiFi interface connected to the internet (managed mode).
# Returns: The interface name (e.g., "wlan0") that is in Managed mode
# -----------------------------------------------------------------------------
get_internal_interface() {
    internal_interface=$(iwconfig 2>/dev/null | grep -B 1 'Mode:Managed' | grep -o '^[^ ]*')
    echo "$internal_interface"
}

# -----------------------------------------------------------------------------
# get_external_interface()
# Detects the WiFi interface available for hosting (master or monitor mode).
# Returns: The interface name in Master or Monitor mode
# -----------------------------------------------------------------------------
get_external_interface() {
    external_interface=$(iwconfig 2>/dev/null | grep -B 1 -E 'Mode:(Master|Monitor)' | grep -o '^[^ ]*')
    echo "$external_interface"
}

# -----------------------------------------------------------------------------
# get_interface_mode()
# Get the current mode of a wireless interface.
# Args: iface - Interface name
# Returns: "Managed", "Master", "Monitor", or empty if not found
# -----------------------------------------------------------------------------
get_interface_mode() {
    local iface="$1"
    iw dev "$iface" info 2>/dev/null | grep -i 'type' | awk '{print $2}'
}

# -----------------------------------------------------------------------------
# is_interface_up()
# Check if an interface is up and running.
# Args: iface - Interface name
# Returns: 0 if up, 1 if down
# -----------------------------------------------------------------------------
is_interface_up() {
    local iface="$1"
    ip link show "$iface" 2>/dev/null | grep -q "state UP" && return 0 || return 1
}

# =============================================================================
# MAC ADDRESS UTILITIES
# =============================================================================

# -----------------------------------------------------------------------------
# is_randomized_mac()
# Detect MAC address randomization (WiFi privacy feature).
# 
# The second character of the first byte indicates local vs universal:
#   Local (randomized): 2, 6, A, E
#   Universal (real):    0, 1, 4, 5, 8, 9, C, D
#
# Args: mac - MAC address (format: AA:BB:CC:DD:EE:FF)
# Returns: 0 if randomized (local), 1 if real (actual)
# -----------------------------------------------------------------------------
is_randomized_mac() {
    local mac="$1"
    local first_byte=$(echo "$mac" | cut -d':' -f1 | tr '[:lower:]' '[:upper:]')
    local second_char="${first_byte:1:1}"
    
    case "$second_char" in
        2|6|A|E) return 0 ;;
        *) return 1 ;;
    esac
}

# -----------------------------------------------------------------------------
# classify_mac()
# Classify a MAC address as 'local' or 'actual'.
# Args: mac - MAC address
# Returns: "local" or "actual"
# -----------------------------------------------------------------------------
classify_mac() {
    local mac="$1"
    if is_randomized_mac "$mac"; then
        echo "local"
    else
        echo "actual"
    fi
}

# -----------------------------------------------------------------------------
# normalize_mac()
# Normalize MAC address to uppercase with colons.
# Args: mac - MAC address in any common format
# Returns: MAC in format AA:BB:CC:DD:EE:FF
# -----------------------------------------------------------------------------
normalize_mac() {
    local mac="$1"
    echo "$mac" | sed 's/[-:]/:/g' | tr '[:lower:]' '[:upper:]'
}

# =============================================================================
# PROCESS UTILITIES
# =============================================================================

# -----------------------------------------------------------------------------
# is_process_running()
# Check if a process with given PID is running.
# Args: pid - Process ID
# Returns: 0 if running, 1 if not
# -----------------------------------------------------------------------------
is_process_running() {
    local pid="$1"
    kill -0 "$pid" 2>/dev/null
}

# -----------------------------------------------------------------------------
# get_process_pids()
# Get PIDs of running processes matching a pattern.
# Args: pattern - Process name or pattern (passed to pgrep)
# Returns: PIDs, one per line, or empty if none found
# -----------------------------------------------------------------------------
get_process_pids() {
    local pattern="$1"
    pgrep -f "$pattern" 2>/dev/null || true
}

# -----------------------------------------------------------------------------
# kill_process()
# Kill a process by PID with optional timeout.
# Args: pid - Process ID, timeout - Seconds to wait (default: 5)
# -----------------------------------------------------------------------------
kill_process() {
    local pid="$1"
    local timeout="${2:-5}"
    
    if ! is_process_running "$pid"; then
        return 0
    fi
    
    kill "$pid" 2>/dev/null || return 1
    
    local count=0
    while is_process_running "$pid" && [[ $count -lt $timeout ]]; do
        sleep 1
        ((count++))
    done
    
    if is_process_running "$pid"; then
        kill -9 "$pid" 2>/dev/null || true
        return 1
    fi
    return 0
}

# =============================================================================
# NETWORK UTILITIES
# =============================================================================

# -----------------------------------------------------------------------------
# wait_for_interface()
# Wait for an interface to appear.
# Args: iface - Interface name, timeout - Max seconds to wait (default: 10)
# Returns: 0 if interface found, 1 if timeout
# -----------------------------------------------------------------------------
wait_for_interface() {
    local iface="$1"
    local timeout="${2:-10}"
    local count=0
    
    while ! ip link show "$iface" &>/dev/null && [[ $count -lt $timeout ]]; do
        sleep 1
        ((count++))
    done
    
    [[ $count -lt $timeout ]]
}

# -----------------------------------------------------------------------------
# is_valid_ip()
# Check if a string is a valid IPv4 address.
# Args: ip - IP address string
# Returns: 0 if valid, 1 if invalid
# -----------------------------------------------------------------------------
is_valid_ip() {
    local ip="$1"
    [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]
}

# -----------------------------------------------------------------------------
# is_valid_mac()
# Check if a string is a valid MAC address.
# Args: mac - MAC address string
# Returns: 0 if valid, 1 if invalid
# -----------------------------------------------------------------------------
is_valid_mac() {
    local mac="$1"
    [[ $mac =~ ^[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$ ]]
}

# =============================================================================
# FILE UTILITIES
# =============================================================================

# -----------------------------------------------------------------------------
# ensure_directory()
# Create a directory if it doesn't exist.
# Args: path - Directory path
# -----------------------------------------------------------------------------
ensure_directory() {
    local path="$1"
    [[ -d "$path" ]] || mkdir -p "$path"
}

# -----------------------------------------------------------------------------
# is_file_empty()
# Check if a file is empty or doesn't exist.
# Args: path - File path
# Returns: 0 if empty or doesn't exist, 1 if has content
# -----------------------------------------------------------------------------
is_file_empty() {
    local path="$1"
    [[ ! -f "$path" ]] || [[ ! -s "$path" ]]
}
