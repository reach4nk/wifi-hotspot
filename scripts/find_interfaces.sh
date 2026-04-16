#!/bin/bash

# =============================================================================
# find_interfaces.sh - Detect available WiFi interfaces
# =============================================================================
# Utility script to identify which WiFi interfaces are available on the system.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/skeleton.sh"
source "$SCRIPT_DIR/common.sh"

main() {
    log_info "Detecting WiFi interfaces..."
    
    local internal=$(get_internal_interface)
    local external=$(get_external_interface)
    local all_wireless=$(get_all_wireless_interfaces)
    
    echo ""
    echo "Wireless Interfaces:"
    echo "----------------------------------------"
    if [[ -n "$all_wireless" ]]; then
        echo "$all_wireless"
    else
        echo "  None found"
    fi
    
    echo ""
    echo "Detected Roles:"
    echo "----------------------------------------"
    echo "  Internet (Managed mode): ${internal:-None}"
    echo "  Hotspot (Master/Monitor): ${external:-None}"
    
    echo ""
}

main "$@"
