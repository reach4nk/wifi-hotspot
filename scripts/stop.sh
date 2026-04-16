#!/bin/bash

# =============================================================================
# stop.sh - Stop the WiFi hotspot
# =============================================================================
# Safely stops the hotspot by:
#   1. Stopping hostapd and dnsmasq services
#   2. Removing firewall/NAT rules
#   3. Disabling IP forwarding
#   4. Cleaning up interface configuration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/skeleton.sh"
source "$SCRIPT_DIR/common.sh"
source "$SCRIPT_DIR/firewall.sh"
source "$SCRIPT_DIR/services.sh"
source "$SCRIPT_DIR/network.sh"

# =============================================================================
# MAIN
# =============================================================================

main() {
    require_root

    local HOTSPOT_IF=$(get_external_interface)
    local INTERNET_IF=$(get_internal_interface)

    log_info "Stopping hotspot services..."
    
    log_info "[1/4] Stopping hostapd and dnsmasq..."
    stop_hotspot_services

    log_info "[2/4] Removing firewall rules..."
    if [[ -n "$HOTSPOT_IF" ]] && [[ -n "$INTERNET_IF" ]]; then
        teardown_hotspot_firewall "$INTERNET_IF" "$HOTSPOT_IF"
    fi

    log_info "[3/4] Disabling IP forwarding..."
    disable_ip_forwarding

    log_info "[4/4] Cleaning up interface..."
    if [[ -n "$HOTSPOT_IF" ]]; then
        teardown_hotspot_interface "$HOTSPOT_IF"
    fi

    log_info "Hotspot stopped."
}

main "$@"
