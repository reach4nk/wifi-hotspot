#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

DEFAULT_GATEWAY="192.168.50.1"
DEFAULT_DHCP_START="192.168.50.10"
DEFAULT_DHCP_END="192.168.50.100"
DEFAULT_DNS="8.8.8.8"
DEFAULT_CHANNEL="6"
DEFAULT_WIFI_MODE="g"
DEFAULT_ENCRYPTION="wpa2"

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

SPECIAL_CHARS=("!" "@" "#" "$" "%" "&" "*" "+" "-" "=" "?" "_" "~")

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Start a WiFi hotspot with customizable settings.

OPTIONS:
    -i, --interface <name>       External WiFi interface (auto-detect if omitted)
    -n, --internet-if <name>      Internet interface (auto-detect if omitted)
        --ssid <name>            SSID name (random if omitted)
        --password <pass>        Password (auto-generate if omitted)
    -e, --encryption <mode>      Encryption: open|wep|wpa|wpa2 (default: wpa2)
    -g, --gateway <IP>           Gateway IP (default: $DEFAULT_GATEWAY)
        --dhcp-start <IP>        DHCP range start (default: $DEFAULT_DHCP_START)
        --dhcp-end <IP>          DHCP range end (default: $DEFAULT_DHCP_END)
        --dns <IP>               DNS server (default: $DEFAULT_DNS)
    -c, --channel <num>          WiFi channel (default: $DEFAULT_CHANNEL)
    -m, --mode <mode>            WiFi mode: b|g|a|n (default: $DEFAULT_WIFI_MODE)
    -h, --help                    Show this help message

EXAMPLES:
    $(basename "$0")                           # Random SSID/password, WPA2
    $(basename "$0") --ssid MyNetwork          # Custom SSID, random password
    $(basename "$0") --ssid FreeWiFi -e open   # Open network
    $(basename "$0") -e wep --ssid OldDevice   # WEP encryption
    $(basename "$0") --ssid Home -p Secret123! # Custom password
    $(basename "$0") -c 11 -g 10.0.0.1         # Different channel and gateway

EOF
}

random_word() {
    local adj=${ADJECTIVES[$RANDOM % ${#ADJECTIVES[@]}]}
    local noun=${NOUNS[$RANDOM % ${#NOUNS[@]}]}
    local num=$((100 + RANDOM % 900))
    echo "${adj}${noun}${num}"
}

generate_password() {
    local base=$(random_word)
    local special=${SPECIAL_CHARS[$RANDOM % ${#SPECIAL_CHARS[@]}]}
    echo "${base}${special}"
}

generate_wep_key() {
   openssl rand -hex 13
}

parse_args() {
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

set_defaults() {
    [[ -z "$HOTSPOT_IF" ]] && HOTSPOT_IF=$(get_external_interface)
    [[ -z "$INTERNET_IF" ]] && INTERNET_IF=$(get_internal_interface)
    [[ -z "$GATEWAY" ]] && GATEWAY="$DEFAULT_GATEWAY"
    [[ -z "$DHCP_START" ]] && DHCP_START="$DEFAULT_DHCP_START"
    [[ -z "$DHCP_END" ]] && DHCP_END="$DEFAULT_DHCP_END"
    [[ -z "$DNS" ]] && DNS="$DEFAULT_DNS"
    [[ -z "$CHANNEL" ]] && CHANNEL="$DEFAULT_CHANNEL"
    [[ -z "$WIFI_MODE" ]] && WIFI_MODE="$DEFAULT_WIFI_MODE"
    [[ -z "$ENCRYPTION" ]] && ENCRYPTION="$DEFAULT_ENCRYPTION"
    [[ -z "$SSID" ]] && SSID="!$(random_word)🛜"

    case "$ENCRYPTION" in
        open)
            PASSWORD=""
            ;;
        wep)
            [[ -z "$PASSWORD" ]] && PASSWORD=$(generate_wep_key)
            ;;
        wpa|wpa2)
            [[ -z "$PASSWORD" ]] && PASSWORD=$(generate_password)
            ;;
        *)
            echo "Invalid encryption mode: $ENCRYPTION"
            echo "Valid options: open, wep, wpa, wpa2"
            exit 1
            ;;
    esac
}

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

    case "$ENCRYPTION" in
        open)
            echo "wpa=0" >> /tmp/hostapd.conf
            ;;
        wep)
            echo "wpa=0" >> /tmp/hostapd.conf
            echo "wep_default_key=0" >> /tmp/hostapd.conf
            echo "wep_key0=$PASSWORD" >> /tmp/hostapd.conf
            ;;
        wpa)
            echo "wpa=1" >> /tmp/hostapd.conf
            echo "wpa_passphrase=$PASSWORD" >> /tmp/hostapd.conf
            echo "wpa_key_mgmt=WPA-PSK" >> /tmp/hostapd.conf
            echo "wpa_pairwise=TKIP" >> /tmp/hostapd.conf
            ;;
        wpa2)
            echo "wpa=2" >> /tmp/hostapd.conf
            echo "wpa_passphrase=$PASSWORD" >> /tmp/hostapd.conf
            echo "wpa_key_mgmt=WPA-PSK" >> /tmp/hostapd.conf
            echo "rsn_pairwise=CCMP" >> /tmp/hostapd.conf
            ;;
    esac
}

write_dnsmasq_config() {
    cat > /tmp/dnsmasq.conf << EOF
interface=$HOTSPOT_IF
bind-interfaces
dhcp-range=$DHCP_START,$DHCP_END,12h
server=$DNS
EOF
}

main() {
    parse_args "$@"
    set_defaults

    echo "[1] Configuring interface..."
    ip link set $HOTSPOT_IF down
    ip addr flush dev $HOTSPOT_IF
    ip addr add $GATEWAY/24 dev $HOTSPOT_IF
    ip link set $HOTSPOT_IF up

    echo "[2] Writing hostapd config..."
    write_hostapd_config

    echo "[3] Writing dnsmasq config..."
    write_dnsmasq_config

    echo "[4] Enabling IP forwarding..."
    sysctl -w net.ipv4.ip_forward=1

    echo "[5] Setting iptables rules..."
    iptables -t nat -A POSTROUTING -o $INTERNET_IF -j MASQUERADE
    iptables -A FORWARD -i $INTERNET_IF -o $HOTSPOT_IF -m state --state RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i $HOTSPOT_IF -o $INTERNET_IF -j ACCEPT

    echo "[6] Starting dnsmasq..."
    dnsmasq -C /tmp/dnsmasq.conf

    echo "[7] Starting hostapd..."
    hostapd -B /tmp/hostapd.conf

    echo ""
    echo "Hotspot started."
    echo "SSID: $SSID"
    [[ -n "$PASSWORD" ]] && echo "Password: $PASSWORD"
    echo "Encryption: $ENCRYPTION"
}

main "$@"
