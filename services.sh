#!/bin/bash
# =============================================================================
# services.sh - Service lifecycle management for hotspot daemons
# =============================================================================
# Functions for managing hostapd and dnsmasq services:
#   - Start/stop operations
#   - Configuration generation
#   - Status checking

# Global PID storage for service management
HOSTAPD_PID=""
DNSMASQ_PID=""
HOSTAPD_CONF=""
DNSMASQ_CONF=""

# =============================================================================
# HOSTAPD MANAGEMENT
# =============================================================================

# -----------------------------------------------------------------------------
# write_hostapd_config()
# Generate hostapd configuration file.
#
# Args:
#   iface - Wireless interface for AP
#   ssid - Network name
#   password - Security password (empty for open)
#   channel - WiFi channel (default: 6)
#   wifi_mode - Hardware mode: b, g, a, n (default: g)
#   encryption - Security mode: open, wep, wpa, wpa2 (default: wpa2)
# Returns:
#   Writes config to /tmp/hostapd.conf and sets HOSTAPD_CONF
# -----------------------------------------------------------------------------
write_hostapd_config() {
    local iface="$1"
    local ssid="$2"
    local password="$3"
    local channel="${4:-6}"
    local wifi_mode="${5:-g}"
    local encryption="${6:-wpa2}"
    
    HOSTAPD_CONF="/tmp/hostapd.conf"
    
    cat > "$HOSTAPD_CONF" << EOF
interface=$iface
driver=nl80211
ctrl_interface=/var/run/hostapd
ssid=$ssid
hw_mode=$wifi_mode
channel=$channel
ieee80211n=1
wmm_enabled=1
auth_algs=1
EOF

    case "$encryption" in
        open)
            echo "wpa=0" >> "$HOSTAPD_CONF"
            ;;
        wep)
            echo "wpa=0" >> "$HOSTAPD_CONF"
            echo "wep_default_key=0" >> "$HOSTAPD_CONF"
            echo "wep_key0=$password" >> "$HOSTAPD_CONF"
            ;;
        wpa)
            echo "wpa=1" >> "$HOSTAPD_CONF"
            echo "wpa_passphrase=$password" >> "$HOSTAPD_CONF"
            echo "wpa_key_mgmt=WPA-PSK" >> "$HOSTAPD_CONF"
            echo "wpa_pairwise=TKIP" >> "$HOSTAPD_CONF"
            ;;
        wpa2)
            echo "wpa=2" >> "$HOSTAPD_CONF"
            echo "wpa_passphrase=$password" >> "$HOSTAPD_CONF"
            echo "wpa_key_mgmt=WPA-PSK" >> "$HOSTAPD_CONF"
            echo "rsn_pairwise=CCMP" >> "$HOSTAPD_CONF"
            ;;
    esac
}

# -----------------------------------------------------------------------------
# start_hostapd()
# Start the hostapd access point daemon.
#
# Args:
#   config_file - Path to hostapd config (default: /tmp/hostapd.conf)
#   background - Run in background (default: true)
# Returns:
#   Sets HOSTAPD_PID on success
# -----------------------------------------------------------------------------
start_hostapd() {
    local config_file="${1:-$HOSTAPD_CONF}"
    local background="${2:-true}"
    
    if ! [[ -f "$config_file" ]]; then
        log_error "Hostapd config not found: $config_file"
        return 1
    fi
    
    if is_hostapd_running; then
        log_warn "hostapd already running"
        return 0
    fi
    
    if [[ "$background" == "true" ]]; then
        hostapd -B "$config_file" 2>/dev/null || {
            log_error "Failed to start hostapd"
            return 1
        }
        sleep 1
        HOSTAPD_PID=$(pgrep -f "hostapd.*$config_file" | head -1)
    else
        hostapd "$config_file"
        HOSTAPD_PID=""
    fi
    
    return 0
}

# -----------------------------------------------------------------------------
# stop_hostapd()
# Stop the hostapd access point daemon.
# -----------------------------------------------------------------------------
stop_hostapd() {
    local pids=$(get_process_pids "hostapd")
    
    if [[ -z "$pids" ]]; then
        log_info "hostapd not running"
        return 0
    fi
    
    for pid in $pids; do
        kill_process "$pid" 5
    done
    
    rm -f "$HOSTAPD_CONF"
    HOSTAPD_PID=""
    return 0
}

# -----------------------------------------------------------------------------
# is_hostapd_running()
# Check if hostapd is currently running.
# Returns: 0 if running, 1 if not
# -----------------------------------------------------------------------------
is_hostapd_running() {
    local pids=$(get_process_pids "hostapd")
    [[ -n "$pids" ]]
}

# =============================================================================
# DNSMASQ MANAGEMENT
# =============================================================================

# -----------------------------------------------------------------------------
# write_dnsmasq_config()
# Generate dnsmasq configuration file for DHCP/DNS.
#
# Args:
#   iface - Interface for DHCP server
#   dhcp_start - First IP in DHCP range
#   dhcp_end - Last IP in DHCP range
#   dns_server - Upstream DNS server (default: 8.8.8.8)
#   lease_time - DHCP lease duration (default: 12h)
# Returns:
#   Writes config to /tmp/dnsmasq.conf and sets DNSMASQ_CONF
# -----------------------------------------------------------------------------
write_dnsmasq_config() {
    local iface="$1"
    local dhcp_start="$2"
    local dhcp_end="$3"
    local dns_server="${4:-8.8.8.8}"
    local lease_time="${5:-12h}"
    
    DNSMASQ_CONF="/tmp/dnsmasq.conf"
    
    cat > "$DNSMASQ_CONF" << EOF
interface=$iface
bind-interfaces
dhcp-range=$dhcp_start,$dhcp_end,$lease_time
server=$dns_server
EOF
}

# -----------------------------------------------------------------------------
# start_dnsmasq()
# Start the dnsmasq DHCP/DNS daemon.
#
# Args:
#   config_file - Path to dnsmasq config (default: /tmp/dnsmasq.conf)
# Returns:
#   Sets DNSMASQ_PID on success
# -----------------------------------------------------------------------------
start_dnsmasq() {
    local config_file="${1:-$DNSMASQ_CONF}"
    
    if ! [[ -f "$config_file" ]]; then
        log_error "dnsmasq config not found: $config_file"
        return 1
    fi
    
    if is_dnsmasq_running; then
        log_warn "dnsmasq already running"
        return 0
    fi
    
    dnsmasq -C "$config_file" || {
        log_error "Failed to start dnsmasq"
        return 1
    }
    
    sleep 1
    DNSMASQ_PID=$(pgrep -f "dnsmasq.*$config_file" | head -1)
    return 0
}

# -----------------------------------------------------------------------------
# stop_dnsmasq()
# Stop the dnsmasq DHCP/DNS daemon.
# -----------------------------------------------------------------------------
stop_dnsmasq() {
    local pids=$(get_process_pids "dnsmasq")
    
    if [[ -z "$pids" ]]; then
        log_info "dnsmasq not running"
        return 0
    fi
    
    for pid in $pids; do
        kill_process "$pid" 5
    done
    
    rm -f "$DNSMASQ_CONF"
    DNSMASQ_PID=""
    return 0
}

# -----------------------------------------------------------------------------
# is_dnsmasq_running()
# Check if dnsmasq is currently running.
# Returns: 0 if running, 1 if not
# -----------------------------------------------------------------------------
is_dnsmasq_running() {
    local pids=$(get_process_pids "dnsmasq")
    [[ -n "$pids" ]]
}

# =============================================================================
# COMBINED OPERATIONS
# =============================================================================

# -----------------------------------------------------------------------------
# start_hotspot_services()
# Start both hostapd and dnsmasq services.
#
# Args:
#   All arguments passed to write_hostapd_config and write_dnsmasq_config
# Returns:
#   0 on success, 1 on failure
# -----------------------------------------------------------------------------
start_hotspot_services() {
    local iface="$1"
    local ssid="$2"
    local password="$3"
    local channel="${4:-6}"
    local wifi_mode="${5:-g}"
    local encryption="${6:-wpa2}"
    local dhcp_start="$7"
    local dhcp_end="$8"
    local dns_server="${9:-8.8.8.8}"
    
    write_dnsmasq_config "$iface" "$dhcp_start" "$dhcp_end" "$dns_server"
    start_dnsmasq || return 1
    
    write_hostapd_config "$iface" "$ssid" "$password" "$channel" "$wifi_mode" "$encryption"
    start_hostapd || return 1
    
    return 0
}

# -----------------------------------------------------------------------------
# stop_hotspot_services()
# Stop both hostapd and dnsmasq services.
# -----------------------------------------------------------------------------
stop_hotspot_services() {
    stop_hostapd
    stop_dnsmasq
}

# -----------------------------------------------------------------------------
# is_hotspot_running()
# Check if all hotspot services are running.
# Returns: 0 if running, 1 if any service is down
# -----------------------------------------------------------------------------
is_hotspot_running() {
    is_hostapd_running && is_dnsmasq_running
}

# -----------------------------------------------------------------------------
# get_hostapd_stations()
# Get list of connected stations from hostapd.
#
# Args:
#   iface - Hostapd interface name
# Returns:
#   List of station MAC addresses, one per line
# -----------------------------------------------------------------------------
get_hostapd_stations() {
    local iface="${1:-$(get_master_interfaces | head -1)}"
    local ctrl_path="/var/run/hostapd"
    
    if [[ -S "$ctrl_path/$iface" ]]; then
        hostapd_cli -p "$ctrl_path" -i "$iface" list 2>/dev/null || true
    fi
}

# -----------------------------------------------------------------------------
# get_dhcp_leases()
# Get current DHCP leases from dnsmasq.
# Returns:
#   List of leases (format: timestamp mac ip hostname), one per line
# -----------------------------------------------------------------------------
get_dhcp_leases() {
    local lease_file="/var/lib/misc/dnsmasq.leases"
    
    if [[ -f "$lease_file" ]]; then
        cat "$lease_file"
    fi
}
