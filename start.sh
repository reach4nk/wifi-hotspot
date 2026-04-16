#!/bin/bash
set -e

# =============================================================================
# start.sh - Start a WiFi hotspot access point
# =============================================================================
# Creates a software-based WiFi access point that shares your internet connection
# with other devices. Supports WPA2, WPA, WEP, and open networks.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/skeleton.sh"
source "$SCRIPT_DIR/common.sh"
source "$SCRIPT_DIR/credentials.sh"
source "$SCRIPT_DIR/network.sh"
source "$SCRIPT_DIR/firewall.sh"
source "$SCRIPT_DIR/services.sh"

# =============================================================================
# DEFAULT CONFIGURATION
# =============================================================================

DEFAULT_GATEWAY="192.168.50.1"
DEFAULT_DHCP_START="192.168.50.10"
DEFAULT_DHCP_END="192.168.50.100"
DEFAULT_DNS="8.8.8.8"
DEFAULT_CHANNEL="6"
DEFAULT_WIFI_MODE="g"
DEFAULT_ENCRYPTION="wpa2"

# =============================================================================
# USAGE
# =============================================================================

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Start a WiFi hotspot with customizable settings.

OPTIONS:
    -i, --interface <name>       External WiFi interface (auto-detect if omitted)
    -n, --internet-if <name>      Internet interface (auto-detect if omitted)
        --ssid <name>             SSID name (random if omitted)
        --password <pass>        Password (auto-generate if omitted)
    -e, --encryption <mode>       Encryption: open|wep|wpa|wpa2 (default: wpa2)
    -g, --gateway <IP>            Gateway IP (default: $DEFAULT_GATEWAY)
        --dhcp-start <IP>         DHCP range start (default: $DEFAULT_DHCP_START)
        --dhcp-end <IP>           DHCP range end (default: $DEFAULT_DHCP_END)
        --dns <IP>                DNS server (default: $DEFAULT_DNS)
    -c, --channel <num>           WiFi channel (default: $DEFAULT_CHANNEL)
    -m, --mode <mode>             WiFi mode: b|g|a|n (default: $DEFAULT_WIFI_MODE)
    -h, --help                    Show this help message

EXAMPLES:
    $(basename "$0")                           # Random SSID/password, WPA2
    $(basename "$0") --ssid MyNetwork        # Custom SSID, random password
    $(basename "$0") --ssid FreeWiFi -e open  # Open network
    $(basename "$0") -e wep --ssid OldDevice  # WEP encryption
    $(basename "$0") --ssid Home -p Secret123! # Custom password
    $(basename "$0") -c 11 -g 10.0.0.1       # Different channel and gateway

EOF
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    local HOTSPOT_IF=""
    local INTERNET_IF=""
    local SSID=""
    local PASSWORD=""
    local ENCRYPTION=""
    local GATEWAY=""
    local DHCP_START=""
    local DHCP_END=""
    local DNS=""
    local CHANNEL=""
    local WIFI_MODE=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--interface) HOTSPOT_IF="$2"; shift 2 ;;
            -n|--internet-if) INTERNET_IF="$2"; shift 2 ;;
            --ssid) SSID="$2"; shift 2 ;;
            --password) PASSWORD="$2"; shift 2 ;;
            -e|--encryption) ENCRYPTION="$2"; shift 2 ;;
            -g|--gateway) GATEWAY="$2"; shift 2 ;;
            --dhcp-start) DHCP_START="$2"; shift 2 ;;
            --dhcp-end) DHCP_END="$2"; shift 2 ;;
            --dns) DNS="$2"; shift 2 ;;
            -c|--channel) CHANNEL="$2"; shift 2 ;;
            -m|--mode) WIFI_MODE="$2"; shift 2 ;;
            -h|--help) show_help; exit 0 ;;
            *) echo "Unknown option: $1"; show_help; exit 1 ;;
        esac
    done

    require_root
    require_all_tools hostapd dnsmasq iw ip sysctl

    [[ -z "$HOTSPOT_IF" ]] && HOTSPOT_IF=$(get_external_interface)
    [[ -z "$INTERNET_IF" ]] && INTERNET_IF=$(get_internal_interface)
    
    [[ -z "$HOTSPOT_IF" ]] && { log_error "No hotspot interface found"; exit 1; }
    [[ -z "$INTERNET_IF" ]] && { log_error "No internet interface found"; exit 1; }

    [[ -z "$GATEWAY" ]] && GATEWAY="$DEFAULT_GATEWAY"
    [[ -z "$DHCP_START" ]] && DHCP_START="$DEFAULT_DHCP_START"
    [[ -z "$DHCP_END" ]] && DHCP_END="$DEFAULT_DHCP_END"
    [[ -z "$DNS" ]] && DNS="$DEFAULT_DNS"
    [[ -z "$CHANNEL" ]] && CHANNEL="$DEFAULT_CHANNEL"
    [[ -z "$WIFI_MODE" ]] && WIFI_MODE="$DEFAULT_WIFI_MODE"
    [[ -z "$ENCRYPTION" ]] && ENCRYPTION="$DEFAULT_ENCRYPTION"

    IFS='|' read -r SSID PASSWORD <<< "$(ensure_valid_credentials "$SSID" "$PASSWORD" "$ENCRYPTION")"

    log_info "Starting hotspot..."
    log_info "  Hotspot interface: $HOTSPOT_IF"
    log_info "  Internet interface: $INTERNET_IF"
    log_info "  Gateway: $GATEWAY"
    log_info "  SSID: $SSID"
    [[ -n "$PASSWORD" ]] && log_info "  Password: $PASSWORD"
    log_info "  Encryption: $ENCRYPTION"

    log_info "[1/5] Configuring interface..."
    setup_hotspot_interface "$HOTSPOT_IF" "$GATEWAY"

    log_info "[2/5] Setting up firewall..."
    setup_hotspot_firewall "$INTERNET_IF" "$HOTSPOT_IF"

    log_info "[3/5] Writing service configs..."
    write_dnsmasq_config "$HOTSPOT_IF" "$DHCP_START" "$DHCP_END" "$DNS"
    write_hostapd_config "$HOTSPOT_IF" "$SSID" "$PASSWORD" "$CHANNEL" "$WIFI_MODE" "$ENCRYPTION"

    log_info "[4/5] Starting dnsmasq..."
    start_dnsmasq || { log_error "Failed to start dnsmasq"; exit 1; }

    log_info "[5/5] Starting hostapd..."
    start_hostapd || { log_error "Failed to start hostapd"; exit 1; }

    add_cleanup_hook "stop_hotspot_services"
    add_cleanup_hook "teardown_hotspot_firewall $INTERNET_IF $HOTSPOT_IF"
    add_cleanup_hook "teardown_hotspot_interface $HOTSPOT_IF"

    echo ""
    echo "Hotspot started successfully."
    echo "  SSID: $SSID"
    [[ -n "$PASSWORD" ]] && echo "  Password: $PASSWORD"
    echo "  Gateway: $GATEWAY"
    echo ""
}

main "$@"
