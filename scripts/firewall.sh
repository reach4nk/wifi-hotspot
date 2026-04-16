#!/bin/bash
# =============================================================================
# firewall.sh - Firewall and NAT management utilities
# =============================================================================
# Functions for managing iptables rules and IP forwarding:
#   - NAT setup/teardown
#   - IP forwarding control
#   - Rule management

# =============================================================================
# IP FORWARDING
# =============================================================================

# -----------------------------------------------------------------------------
# enable_ip_forwarding()
# Enable IPv4 packet forwarding in the kernel.
# Required for routing packets between interfaces.
# -----------------------------------------------------------------------------
enable_ip_forwarding() {
    sysctl -w net.ipv4.ip_forward=1 2>/dev/null || {
        echo 1 > /proc/sys/net/ipv4/ip_forward
    }
}

# -----------------------------------------------------------------------------
# disable_ip_forwarding()
# Disable IPv4 packet forwarding.
# -----------------------------------------------------------------------------
disable_ip_forwarding() {
    sysctl -w net.ipv4.ip_forward=0 2>/dev/null || {
        echo 0 > /proc/sys/net/ipv4/ip_forward
    }
}

# -----------------------------------------------------------------------------
# is_ip_forwarding_enabled()
# Check if IP forwarding is currently enabled.
# Returns: 0 if enabled, 1 if disabled
# -----------------------------------------------------------------------------
is_ip_forwarding_enabled() {
    local value=$(cat /proc/sys/net/ipv4/ip_forward 2>/dev/null)
    [[ "$value" == "1" ]]
}

# =============================================================================
# NAT CONFIGURATION
# =============================================================================

# -----------------------------------------------------------------------------
# enable_nat()
# Enable NAT (Network Address Translation) between two interfaces.
# This allows devices on the internal interface to access the internet
# through the external interface.
#
# Args:
#   external_if - Interface connected to internet (e.g., "wlan0")
#   internal_if - Interface connected to clients (e.g., "wlan1")
# -----------------------------------------------------------------------------
enable_nat() {
    local external_if="$1"
    local internal_if="$2"
    
    enable_ip_forwarding
    
    iptables -t nat -A POSTROUTING -o "$external_if" -j MASQUERADE
    iptables -A FORWARD -i "$external_if" -o "$internal_if" \
        -m state --state RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i "$internal_if" -o "$external_if" -j ACCEPT
}

# -----------------------------------------------------------------------------
# disable_nat()
# Remove NAT configuration between two interfaces.
#
# Args:
#   external_if - External interface
#   internal_if - Internal interface
# -----------------------------------------------------------------------------
disable_nat() {
    local external_if="$1"
    local internal_if="$2"
    
    iptables -t nat -D POSTROUTING -o "$external_if" -j MASQUERADE 2>/dev/null || true
    iptables -D FORWARD -i "$external_if" -o "$internal_if" \
        -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
    iptables -D FORWARD -i "$internal_if" -o "$external_if" -j ACCEPT 2>/dev/null || true
}

# =============================================================================
# HOTSPOT FIREWALL SETUP
# =============================================================================

# -----------------------------------------------------------------------------
# setup_hotspot_firewall()
# Configure firewall rules for a hotspot access point.
#
# Args:
#   internet_if - Interface with internet (upstream)
#   hotspot_if - Interface hosting the hotspot
# -----------------------------------------------------------------------------
setup_hotspot_firewall() {
    local internet_if="$1"
    local hotspot_if="$2"
    
    enable_nat "$internet_if" "$hotspot_if"
}

# -----------------------------------------------------------------------------
# teardown_hotspot_firewall()
# Remove firewall rules for a hotspot access point.
#
# Args:
#   internet_if - Internet interface
#   hotspot_if - Hotspot interface
# -----------------------------------------------------------------------------
teardown_hotspot_firewall() {
    local internet_if="$1"
    local hotspot_if="$2"
    
    disable_nat "$internet_if" "$hotspot_if"
}

# =============================================================================
# RULE LISTING
# =============================================================================

# -----------------------------------------------------------------------------
# list_nat_rules()
# Display current NAT rules.
# -----------------------------------------------------------------------------
list_nat_rules() {
    iptables -t nat -L -n -v 2>/dev/null || echo "No NAT rules"
}

# -----------------------------------------------------------------------------
# list_forward_rules()
# Display current forwarding rules.
# -----------------------------------------------------------------------------
list_forward_rules() {
    iptables -L FORWARD -n -v 2>/dev/null || echo "No forward rules"
}

# -----------------------------------------------------------------------------
# count_firewall_rules()
# Count total number of active firewall rules.
# Returns: Number of rules
# -----------------------------------------------------------------------------
count_firewall_rules() {
    local count=$(iptables -L -n 2>/dev/null | grep -c '^Chain' || echo 0)
    echo $((count - 1))
}

# =============================================================================
# CHAIN MANAGEMENT
# =============================================================================

# -----------------------------------------------------------------------------
# flush_firewall()
# Flush all rules in the filter table.
# WARNING: This removes ALL iptables rules!
# -----------------------------------------------------------------------------
flush_firewall() {
    iptables -F
    iptables -X
    iptables -t nat -F
    iptables -t nat -X
}

# -----------------------------------------------------------------------------
# save_firewall()
# Save current iptables rules to a file.
# Args:
#   path - File path to save rules (default: /tmp/iptables.backup)
# -----------------------------------------------------------------------------
save_firewall() {
    local path="${1:-/tmp/iptables.backup}"
    iptables-save > "$path"
    echo "Rules saved to: $path"
}

# -----------------------------------------------------------------------------
# restore_firewall()
# Restore iptables rules from a file.
# Args:
#   path - File path to restore from (default: /tmp/iptables.backup)
# -----------------------------------------------------------------------------
restore_firewall() {
    local path="${1:-/tmp/iptables.backup}"
    if [[ -f "$path" ]]; then
        iptables-restore < "$path"
        echo "Rules restored from: $path"
    else
        log_error "No saved rules found at: $path"
        return 1
    fi
}
