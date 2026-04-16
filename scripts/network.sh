#!/bin/bash
# =============================================================================
# network.sh - Network interface configuration utilities
# =============================================================================
# Functions for managing WiFi interfaces:
#   - Monitor mode setup/teardown
#   - Hotspot interface IP configuration
#   - Interface state management

# =============================================================================
# MONITOR MODE
# =============================================================================

# -----------------------------------------------------------------------------
# setup_monitor_mode()
# Enable monitor mode on a wireless interface.
# 
# Monitor mode allows capturing all WiFi frames, including probe requests
# from clients searching for networks.
#
# Args:
#   iface - Interface name to put in monitor mode
# Returns:
#   0 on success, 1 on failure
# -----------------------------------------------------------------------------
setup_monitor_mode() {
    local iface="$1"
    
    local current_mode=$(get_interface_mode "$iface")
    
    if [[ "$current_mode" == "Monitor" ]]; then
        ip link set "$iface" up 2>/dev/null || true
        return 0
    fi
    
    ip link set "$iface" down 2>/dev/null || {
        log_error "Failed to bring interface down: $iface"
        return 1
    }
    
    iw dev "$iface" set type monitor 2>/dev/null || {
        log_error "Failed to set monitor mode: $iface"
        return 1
    }
    
    ip link set "$iface" up 2>/dev/null || {
        log_error "Failed to bring interface up: $iface"
        return 1
    }
    
    return 0
}

# -----------------------------------------------------------------------------
# teardown_monitor_mode()
# Restore managed mode on a wireless interface.
#
# Args:
#   iface - Interface name to restore
# Returns:
#   0 on success, 1 on failure
# -----------------------------------------------------------------------------
teardown_monitor_mode() {
    local iface="$1"
    
    ip link set "$iface" down 2>/dev/null || true
    
    iw dev "$iface" set type managed 2>/dev/null || {
        log_error "Failed to restore managed mode: $iface"
        return 1
    }
    
    ip link set "$iface" up 2>/dev/null || true
    return 0
}

# =============================================================================
# HOTSPOT INTERFACE CONFIGURATION
# =============================================================================

# -----------------------------------------------------------------------------
# setup_hotspot_interface()
# Configure an interface for hosting a hotspot.
#   1. Bring interface down
#   2. Flush existing IP addresses
#   3. Assign static IP address
#   4. Bring interface back up
#
# Args:
#   iface - Interface name
#   ip - Static IP address (e.g., "192.168.50.1")
#   netmask - Network mask bits (default: 24)
# Returns:
#   0 on success, 1 on failure
# -----------------------------------------------------------------------------
setup_hotspot_interface() {
    local iface="$1"
    local ip="$2"
    local netmask="${3:-24}"
    
    ip link set "$iface" down || {
        log_error "Failed to bring interface down: $iface"
        return 1
    }
    
    ip addr flush dev "$iface" || true
    
    ip addr add "${ip}/${netmask}" dev "$iface" || {
        log_error "Failed to assign IP: $ip to $iface"
        return 1
    }
    
    ip link set "$iface" up || {
        log_error "Failed to bring interface up: $iface"
        return 1
    }
    
    return 0
}

# -----------------------------------------------------------------------------
# teardown_hotspot_interface()
# Remove configuration from a hotspot interface.
#
# Args:
#   iface - Interface name
# Returns:
#   0 on success, 1 on failure
# -----------------------------------------------------------------------------
teardown_hotspot_interface() {
    local iface="$1"
    
    ip addr flush dev "$iface" || true
    ip link set "$iface" down || true
    
    return 0
}

# =============================================================================
# MASTER/AP MODE
# =============================================================================

# -----------------------------------------------------------------------------
# setup_ap_mode()
# Enable AP/Master mode on a wireless interface.
#
# Args:
#   iface - Interface name
# Returns:
#   0 on success, 1 on failure
# -----------------------------------------------------------------------------
setup_ap_mode() {
    local iface="$1"
    
    local current_mode=$(get_interface_mode "$iface")
    
    if [[ "$current_mode" == "Master" ]]; then
        return 0
    fi
    
    ip link set "$iface" down 2>/dev/null || true
    
    iw dev "$iface" set type __ap 2>/dev/null || {
        log_error "Failed to set AP mode: $iface"
        return 1
    }
    
    ip link set "$iface" up 2>/dev/null || true
    
    return 0
}

# =============================================================================
# INTERFACE QUERY FUNCTIONS
# =============================================================================

# -----------------------------------------------------------------------------
# get_all_wireless_interfaces()
# List all wireless interfaces on the system.
# Returns:
#   List of wireless interface names, one per line
# -----------------------------------------------------------------------------
get_all_wireless_interfaces() {
    iw dev 2>/dev/null | grep -E '^Interface' | awk '{print $2}'
}

# -----------------------------------------------------------------------------
# get_managed_interfaces()
# List all interfaces in managed (client) mode.
# Returns:
#   List of managed interface names, one per line
# -----------------------------------------------------------------------------
get_managed_interfaces() {
    iwconfig 2>/dev/null | grep -B 1 'Mode:Managed' | grep -o '^[^ ]*'
}

# -----------------------------------------------------------------------------
# get_monitor_interfaces()
# List all interfaces in monitor mode.
# Returns:
#   List of monitor interface names, one per line
# -----------------------------------------------------------------------------
get_monitor_interfaces() {
    iwconfig 2>/dev/null | grep -B 1 'Mode:Monitor' | grep -o '^[^ ]*'
}

# -----------------------------------------------------------------------------
# get_master_interfaces()
# List all interfaces in master (AP) mode.
# Returns:
#   List of master interface names, one per line
# -----------------------------------------------------------------------------
get_master_interfaces() {
    iwconfig 2>/dev/null | grep -B 1 'Mode:Master' | grep -o '^[^ ]*'
}

# =============================================================================
# INTERNET CONNECTIVITY
# =============================================================================

# -----------------------------------------------------------------------------
# get_default_gateway()
# Get the default gateway interface.
# Returns:
#   Interface name of default gateway, or empty if not found
# -----------------------------------------------------------------------------
get_default_gateway() {
    ip route show default 2>/dev/null | awk '/default/ {print $5}' | head -1
}

# -----------------------------------------------------------------------------
# has_internet()
# Check if an interface has internet connectivity.
# Args:
#   iface - Interface name to check
# Returns:
#   0 if connected, 1 if not
# -----------------------------------------------------------------------------
has_internet() {
    local iface="${1:-$(get_default_gateway)}"
    ping -c 1 -W 2 -I "$iface" 8.8.8.8 &>/dev/null
}
