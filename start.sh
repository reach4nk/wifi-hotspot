#!/bin/bash
# Exit immediately if a command fails
set -e

# =============================================================================
# start.sh - Start a WiFi hotspot access point
# =============================================================================
# Creates a software-based WiFi access point that shares your internet connection
# with other devices. Supports WPA2, WPA, WEP, and open networks.
#
# What this script does:
#   1. Sets up the WiFi interface with a static IP
#   2. Configures hostapd for the access point
#   3. Configures dnsmasq for DHCP (IP assignment)
#   4. Sets up NAT/routing with iptables
#   5. Starts the services
#
# Requirements:
#   - Two WiFi interfaces (or one in monitor mode from scan.sh)
#   - hostapd, dnsmasq, iptables installed (see setup.sh)

# Get script directory and load shared functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# =============================================================================
# DEFAULT CONFIGURATION
# These values are used when not specified via command line arguments
# =============================================================================

# Network settings for the hotspot
DEFAULT_GATEWAY="192.168.50.1"      # IP address of the hotspot (clients use this as gateway)
DEFAULT_DHCP_START="192.168.50.10"  # First IP in DHCP range
DEFAULT_DHCP_END="192.168.50.100"   # Last IP in DHCP range
DEFAULT_DNS="8.8.8.8"              # DNS server for clients (Google DNS)

# WiFi settings
DEFAULT_CHANNEL="6"                   # WiFi channel (2.4GHz)
DEFAULT_WIFI_MODE="g"                # WiFi mode: b=11Mbps, g=54Mbps, a=5GHz, n=802.11n
DEFAULT_ENCRYPTION="wpa2"           # Encryption: open, wep, wpa, wpa2

# =============================================================================
# WORD LISTS FOR RANDOM SSID/PASSWORD GENERATION
# =============================================================================

# Adjectives and nouns are combined with random numbers to create memorable credentials
# Example: Blue + Node + 482 = "BlueNode482"
ADJECTIVES=(
"Blue" "Grey" "Dark" "Warm" "Cold" "Bold" "Soft" "Calm"
"Fast" "Tiny" "Huge" "Kind" "Wild" "Free" "Pure" "Safe"
"Rich" "Fair" "New" "Old" "Hot" "Wet" "Dry" "Zen"
"Red" "Cyan" "Gold" "Iron" "Snow" "Rain" "Star" "Moon"
"Glow" "Fire" "Wind" "Mist" "Wave" "Rock" "Echo" "Core"
"Peak" "Deep" "Sage" "Lush" "Hush" "Fury" "Dawn" "Fate"
"Nova" "Bolt"
)

NOUNS=(
"Node" "Link" "Port" "Net" "Hub" "Beam" "Star" "Moon"
"Comet" "Nova" "Orb" "Core" "Ring" "Axis" "Wave" "Pixel"
"Echo" "Flag" "Mine" "Bolt" "Lamp" "Grid" "Lens" "Path"
"Root" "Peak" "Gate" "Bolt" "Drip" "Loom" "Drift" "Scan"
"Ship" "Leaf" "Dust" "Mist" "Rain" "Hawk" "Wolf" "Lion"
"Bear" "Fox" "Rex" "Jet" "Sky" "Sun" "Sea" "Ark"
"Frog" "Owl"
)

# Special characters that work well on mobile keyboards
SPECIAL_CHARS=("!" "@" "#" "$" "%" "&" "*" "+" "-" "=" "?" "_" "~")

# =============================================================================
# USAGE INFORMATION
# =============================================================================

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Start a WiFi hotspot with customizable settings.

OPTIONS:
    -i, --interface <name>       External WiFi interface (auto-detect if omitted)
    -n, --internet-if <name>      Internet interface (auto-detect if omitted)
        --ssid <name>            SSID name (random if omitted)
        --password <pass>        Password (auto-generate if omitted)
    -e, --encryption <mode>       Encryption: open|wep|wpa|wpa2 (default: wpa2)
    -g, --gateway <IP>            Gateway IP (default: $DEFAULT_GATEWAY)
        --dhcp-start <IP>       DHCP range start (default: $DEFAULT_DHCP_START)
        --dhcp-end <IP>         DHCP range end (default: $DEFAULT_DHCP_END)
        --dns <IP>              DNS server (default: $DEFAULT_DNS)
    -c, --channel <num>           WiFi channel (default: $DEFAULT_CHANNEL)
    -m, --mode <mode>             WiFi mode: b|g|a|n (default: $DEFAULT_WIFI_MODE)
    -h, --help                    Show this help message

EXAMPLES:
    $(basename "$0")                           # Random SSID/password, WPA2
    $(basename "$0") --ssid MyNetwork          # Custom SSID, random password
    $(basename "$0") --ssid FreeWiFi -e open   # Open network
    $(basename "$0") -e wep --ssid OldDevice   # WEP encryption
    $(basename "$0") --ssid Home -p Secret123! # Custom password
    $(basename "$0") -c 11 -g 10.0.0.1        # Different channel and gateway

EOF
}

# =============================================================================
# RANDOM CREDENTIAL GENERATION
# =============================================================================

# Generate a random word from adjective + noun + number
# Example output: "BlueNode482"
random_word() {
    # $RANDOM: Bash built-in random number generator
    # ${#ARRAY[@]}: Length of array
    local adj=${ADJECTIVES[$RANDOM % ${#ADJECTIVES[@]}]}
    local noun=${NOUNS[$RANDOM % ${#NOUNS[@]}]}
    local num=$((100 + RANDOM % 900))  # Random number 100-999
    echo "${adj}${noun}${num}"
}

# Generate a WPA/WPA2 password
# Format: word + special_char (e.g., "BlueNode382#")
generate_password() {
    local base=$(random_word)
    local special=${SPECIAL_CHARS[$RANDOM % ${#SPECIAL_CHARS[@]}]}
    echo "${base}${special}"
}

# Generate a WEP key (26 hex characters)
# WEP uses hexadecimal keys for encryption
generate_wep_key() {
    openssl rand -hex 13  # 13 bytes = 26 hex characters
}

# =============================================================================
# COMMAND LINE ARGUMENT PARSING
# =============================================================================

parse_args() {
    # Loop through all arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--interface)
                HOTSPOT_IF="$2"
                shift 2
                ;;
            -n|--internet-if)
                INTERNET_IF="$2"
                shift 2
                ;;
            --ssid)
                SSID="$2"
                shift 2
                ;;
            --password)
                PASSWORD="$2"
                shift 2
                ;;
            -e|--encryption)
                ENCRYPTION="$2"
                shift 2
                ;;
            -g|--gateway)
                GATEWAY="$2"
                shift 2
                ;;
            --dhcp-start)
                DHCP_START="$2"
                shift 2
                ;;
            --dhcp-end)
                DHCP_END="$2"
                shift 2
                ;;
            --dns)
                DNS="$2"
                shift 2
                ;;
            -c|--channel)
                CHANNEL="$2"
                shift 2
                ;;
            -m|--mode)
                WIFI_MODE="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# =============================================================================
# SET DEFAULT VALUES
# =============================================================================

# Fill in any missing values with defaults or auto-detected values
set_defaults() {
    # Auto-detect interfaces if not specified
    [[ -z "$HOTSPOT_IF" ]] && HOTSPOT_IF=$(get_external_interface)
    [[ -z "$INTERNET_IF" ]] && INTERNET_IF=$(get_internal_interface)
    
    # Use defaults for network settings
    [[ -z "$GATEWAY" ]] && GATEWAY="$DEFAULT_GATEWAY"
    [[ -z "$DHCP_START" ]] && DHCP_START="$DEFAULT_DHCP_START"
    [[ -z "$DHCP_END" ]] && DHCP_END="$DEFAULT_DHCP_END"
    [[ -z "$DNS" ]] && DNS="$DEFAULT_DNS"
    [[ -z "$CHANNEL" ]] && CHANNEL="$DEFAULT_CHANNEL"
    [[ -z "$WIFI_MODE" ]] && WIFI_MODE="$DEFAULT_WIFI_MODE"
    [[ -z "$ENCRYPTION" ]] && ENCRYPTION="$DEFAULT_ENCRYPTION"
    
    # Generate random SSID if not specified
    # Format: !{word}🛜 (WiFi emoji)
    [[ -z "$SSID" ]] && SSID="!$(random_word)🛜"

    # Handle password generation based on encryption type
    case "$ENCRYPTION" in
        open)
            # No password for open networks
            PASSWORD=""
            ;;
        wep)
            # Generate WEP key if not provided
            [[ -z "$PASSWORD" ]] && PASSWORD=$(generate_wep_key)
            ;;
        wpa|wpa2)
            # Generate WPA password if not provided
            [[ -z "$PASSWORD" ]] && PASSWORD=$(generate_password)
            ;;
        *)
            echo "Invalid encryption mode: $ENCRYPTION"
            echo "Valid options: open, wep, wpa, wpa2"
            exit 1
            ;;
    esac
}

# =============================================================================
# CONFIGURATION FILE GENERATION
# =============================================================================

# Generate hostapd configuration file
# hostapd is the daemon that creates the WiFi access point
write_hostapd_config() {
    cat > /tmp/hostapd.conf << EOF
interface=$HOTSPOT_IF
driver=nl80211
ctrl_interface=/var/run/hostapd
ssid=$SSID
hw_mode=$WIFI_MODE
channel=$CHANNEL
ieee80211n=1
wmm_enabled=1
auth_algs=1
EOF

    # Add encryption-specific settings based on mode
    case "$ENCRYPTION" in
        open)
            # No encryption - open network
            echo "wpa=0" >> /tmp/hostapd.conf
            ;;
        wep)
            # WEP - legacy encryption (weak, but compatible with old devices)
            echo "wpa=0" >> /tmp/hostapd.conf
            echo "wep_default_key=0" >> /tmp/hostapd.conf
            echo "wep_key0=$PASSWORD" >> /tmp/hostapd.conf
            ;;
        wpa)
            # WPA with TKIP encryption
            echo "wpa=1" >> /tmp/hostapd.conf
            echo "wpa_passphrase=$PASSWORD" >> /tmp/hostapd.conf
            echo "wpa_key_mgmt=WPA-PSK" >> /tmp/hostapd.conf
            echo "wpa_pairwise=TKIP" >> /tmp/hostapd.conf
            ;;
        wpa2)
            # WPA2 with CCMP encryption (recommended)
            echo "wpa=2" >> /tmp/hostapd.conf
            echo "wpa_passphrase=$PASSWORD" >> /tmp/hostapd.conf
            echo "wpa_key_mgmt=WPA-PSK" >> /tmp/hostapd.conf
            echo "rsn_pairwise=CCMP" >> /tmp/hostapd.conf
            ;;
    esac
}

# Generate dnsmasq configuration file
# dnsmasq provides DHCP (IP assignment) and DNS services
write_dnsmasq_config() {
    cat > /tmp/dnsmasq.conf << EOF
interface=$HOTSPOT_IF
bind-interfaces
dhcp-range=$DHCP_START,$DHCP_END,12h
server=$DNS
EOF
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    # Parse command line arguments
    parse_args "$@"
    
    # Set default values for any missing configuration
    set_defaults

    # Step 1: Configure the WiFi interface
    # Bring interface down, assign static IP, bring back up
    echo "[1] Configuring interface..."
    ip link set $HOTSPOT_IF down
    ip addr flush dev $HOTSPOT_IF
    ip addr add $GATEWAY/24 dev $HOTSPOT_IF
    ip link set $HOTSPOT_IF up

    # Step 2: Write and apply hostapd configuration
    echo "[2] Writing hostapd config..."
    write_hostapd_config

    # Step 3: Write dnsmasq configuration for DHCP
    echo "[3] Writing dnsmasq config..."
    write_dnsmasq_config

    # Step 4: Enable IP forwarding in the kernel
    # This allows the system to forward packets between interfaces
    echo "[4] Enabling IP forwarding..."
    sysctl -w net.ipv4.ip_forward=1

    # Step 5: Set up NAT (Network Address Translation)
    # NAT allows multiple devices to share one internet connection
    echo "[5] Setting iptables rules..."
    # MASQUERADE: Hide client IPs behind our external interface
    iptables -t nat -A POSTROUTING -o $INTERNET_IF -j MASQUERADE
    # FORWARD: Allow established connections and new connections from hotspot
    iptables -A FORWARD -i $INTERNET_IF -o $HOTSPOT_IF -m state --state RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i $HOTSPOT_IF -o $INTERNET_IF -j ACCEPT

    # Step 6: Start DHCP/DNS server
    echo "[6] Starting dnsmasq..."
    dnsmasq -C /tmp/dnsmasq.conf

    # Step 7: Start the access point
    echo "[7] Starting hostapd..."
    hostapd -B /tmp/hostapd.conf  # -B: Run in background

    # Display success message with connection details
    echo ""
    echo "Hotspot started."
    echo "SSID: $SSID"
    [[ -n "$PASSWORD" ]] && echo "Password: $PASSWORD"
    echo "Encryption: $ENCRYPTION"
}

# Run the main function with all command line arguments
main "$@"
