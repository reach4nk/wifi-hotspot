#!/bin/bash
set -e

# =============================================================================
# monitor.sh - Monitor connected clients on the hotspot
# =============================================================================
# Displays real-time information about devices connected to the hotspot:
#   - Connected WiFi stations (from hostapd)
#   - DHCP leases (assigned IPs and hostnames)
#   - ARP table (active devices on the network)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/skeleton.sh"
source "$SCRIPT_DIR/common.sh"
source "$SCRIPT_DIR/services.sh"

main() {
    require_root

    local HOTSPOT_IF=$(get_external_interface)
    local LEASE_FILE="/var/lib/misc/dnsmasq.leases"
    local CTRL_PATH="/var/run/hostapd"

    clear

    echo "========================================"
    echo " Hotspot Monitor"
    echo " Interface: $HOTSPOT_IF"
    echo "========================================"
    echo ""

    echo "Connected WiFi Stations:"
    echo "----------------------------------------"
    if [[ -S "$CTRL_PATH/$HOTSPOT_IF" ]]; then
        hostapd_cli -p "$CTRL_PATH" -i "$HOTSPOT_IF" all_sta 2>/dev/null | \
        awk '/^STA/ {mac=$2} /signal=/ {sig=$1} /connected_time=/ {time=$1; 
            printf "MAC: %-18s Signal: %-10s %s\n", mac, sig, time}' || \
            echo "No stations connected"
    else
        echo "hostapd control socket not found."
    fi

    echo ""
    echo "DHCP Leases:"
    echo "----------------------------------------"
    get_dhcp_leases | awk '{printf "IP: %-15s MAC: %-18s Hostname: %s\n", $3, $2, $4}' || \
        echo "No active leases"

    echo ""
    echo "ARP Table:"
    echo "----------------------------------------"
    ip neigh show dev "$HOTSPOT_IF" 2>/dev/null || echo "No ARP entries"

    echo ""
}

main "$@"
