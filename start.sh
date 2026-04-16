#!/bin/bash
set -e

# Function to get the internal Wi-Fi interface
get_internal_interface() {
    internal_interface=$(iwconfig 2>/dev/null | grep -B 1 'Mode:Managed' | grep -o '^[^ ]*')
    echo "$internal_interface"
}

# Function to get the external Wi-Fi interface
get_external_interface() {
    external_interface=$(iwconfig 2>/dev/null | grep -B 1 'Mode:Master' | grep -o '^[^ ]*')
    echo "$external_interface"
}

# Get interfaces
INTERNET_IF=$(get_internal_interface)
HOTSPOT_IF=$(get_external_interface)

GATEWAY="192.168.50.1"

# ---- Generate Smart SSID ----
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

# List of mobile-friendly special characters
SPECIAL_CHARS=("!" "@" "#" "$" "%" "&" "*" "+" "-" "=" "?" "_" "~")

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

PASSPHRASE=$(generate_password)
echo $PASSPHRASE

SSID="!$(random_word)🛜"

echo "[1] Configuring interface..."

ip link set $HOTSPOT_IF down
ip addr flush dev $HOTSPOT_IF
ip addr add $GATEWAY/24 dev $HOTSPOT_IF
ip link set $HOTSPOT_IF up

echo "[2] Writing hostapd config..."

cat > /tmp/hostapd.conf <<EOF
interface=$HOTSPOT_IF
driver=nl80211
ctrl_interface=/var/run/hostapd
ssid=$SSID
hw_mode=g
channel=6
ieee80211n=1
wmm_enabled=1
auth_algs=1
wpa=2
wpa_passphrase=$PASSPHRASE
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

echo "[3] Writing dnsmasq config..."

cat > /tmp/dnsmasq.conf <<EOF
interface=$HOTSPOT_IF
bind-interfaces
dhcp-range=192.168.50.10,192.168.50.100,12h
server=8.8.8.8
EOF

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

echo "Hotspot started."
echo "SSID: $SSID"
echo "Password: $PASSPHRASE"
