#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

OUTPUT_FILE=""
MERGE_FILE=""
UNIQUE_ONLY=false
DURATION=""
INTERFACE=""
MONITOR_IF=""
CLEANUP_NEEDED=false

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Scan for WiFi probe requests from devices searching for networks.
Requires a WiFi interface capable of monitor mode.

OPTIONS:
    -i, --interface <name>    WiFi interface for scanning (required)
    -d, --duration <sec>     Scan duration in seconds (default: continuous)
    -o, --output <file>      Output JSON file (default: stdout)
    -m, --merge <file>       Merge with existing scan database
        --unique             Show only unique SSIDs (aggregate clients)
    -h, --help               Show this help message

EXAMPLES:
    $(basename "$0") -i wlan1                    # Scan until Ctrl+C
    $(basename "$0") -i wlan1 -d 60              # Scan for 60 seconds
    $(basename "$0") -i wlan1 -o probes.json     # Save to file
    $(basename "$0") -i wlan1 --unique           # Show unique SSIDs
    $(basename "$0") -i wlan1 -m old_scan.json  # Merge with existing

OUTPUT FORMAT:
    JSON array of discovered probe requests with SSID, client MAC,
    BSSID being probed, signal strength, and timestamp.

EOF
}

cleanup() {
    if [ "$CLEANUP_NEEDED" = true ]; then
        echo -e "\n[Cleanup] Restoring interface..."
        ip link set "$INTERFACE" down 2>/dev/null || true
        iw dev "$INTERFACE" set type managed 2>/dev/null || true
        ip link set "$INTERFACE" up 2>/dev/null || true
        CLEANUP_NEEDED=false
    fi
}

trap cleanup EXIT INT TERM

setup_monitor_mode() {
    local iface=$1
    echo "[Setup] Enabling monitor mode on $iface..."
    
    ip link set "$iface" down 2>/dev/null || true
    
    if iw dev "$iface" set monitor 2>/dev/null; then
        MONITOR_IF="$iface"
    else
        iw dev "$iface" set type monitor 2>/dev/null || true
        MONITOR_IF="$iface"
    fi
    
    ip link set "$MONITOR_IF" up 2>/dev/null || true
    CLEANUP_NEEDED=true
    
    echo "[Setup] Monitor mode enabled on $MONITOR_IF"
}

parse_probe_request() {
    local line="$1"
    
    local ssid=$(echo "$line" | grep -oP '(?<=SSID: ).*?(?=\s+|$)' | head -1)
    [ -z "$ssid" ] && return 1
    
    local client_mac=$(echo "$line" | grep -oP 'SA:|Source address: \K[0-9a-fA-F:]+' | head -1)
    [ -z "$client_mac" ] && client_mac="Unknown"
    
    local bssid=$(echo "$line" | grep -oP 'BSSID:|BSS Id: \K[0-9a-fA-F:]+' | head -1)
    [ -z "$bssid" ] && bssid="ff:ff:ff:ff:ff:ff"
    
    local signal=$(echo "$line" | grep -oP 'signal: \K-?[0-9]+' | head -1)
    [ -z "$signal" ] && signal="0"
    
    local timestamp=$(echo "$line" | grep -oP '\d{2}:\d{2}:\d{2}' | head -1)
    [ -z "$timestamp" ] && timestamp=$(date +%H:%M:%S)
    
    local date_str=$(date +%Y-%m-%d)
    
    echo "$ssid|$client_mac|$bssid|$signal|$date_str|$timestamp"
}

generate_json() {
    local -n arr=$1
    local unique=$2
    
    echo "{"
    echo "  \"scan_time\": \"$(date -Iseconds)\","
    echo "  \"duration_seconds\": ${DURATION:-null},"
    echo "  \"interface\": \"$MONITOR_IF\","
    
    if [ "$unique" = true ]; then
        echo "  \"unique_ssids\": ["
        local first=true
        for ssid in $(echo "${arr[@]}" | tr ' ' '\n' | cut -d'|' -f1 | sort -u); do
            local clients=""
            local first_client=true
            while IFS='|' read -r s mac bssid signal date ts; do
                if [ "$s" = "$ssid" ]; then
                    if [ "$first_client" = true ]; then
                        first_client=false
                    else
                        clients+=","
                    fi
                    clients+="\"$mac\""
                fi
            done <<< "$(echo "${arr[@]}" | tr ' ' '\n' | grep "^${ssid}|")"
            
            if [ "$first" = true ]; then
                first=false
            else
                echo ","
            fi
            echo -n "    {\"ssid\": \"$ssid\", \"client_count\": $(echo "$clients" | tr ',' '\n' | wc -l), \"clients\": [$clients]}"
        done
        echo ""
        echo "  ]"
    else
        echo "  \"probes\": ["
        local first=true
        for entry in "${arr[@]}"; do
            IFS='|' read -r ssid client_mac bssid signal date ts <<< "$entry"
            local full_ts="${date}T${ts}"
            
            if [ "$first" = true ]; then
                first=false
            else
                echo ","
            fi
            echo -n "    {"
            echo -n "\"ssid\": \"$ssid\", "
            echo -n "\"client_mac\": \"$client_mac\", "
            echo -n "\"probed_bssid\": \"$bssid\", "
            echo -n "\"signal_dbm\": $signal, "
            echo -n "\"first_seen\": \"$full_ts\""
            echo -n "}"
        done
        echo ""
        echo "  ]"
    fi
    
    echo "}"
}

merge_existing() {
    if [ -f "$MERGE_FILE" ]; then
        if command -v jq &>/dev/null; then
            local existing=$(jq -r '.probes[] | "\(.ssid)|\(.client_mac)|\(.probed_bssid)|\(.signal_dbm)|\(.first_seen)"' "$MERGE_FILE" 2>/dev/null)
            echo "$existing"
        else
            echo "[Warning] jq not installed, skipping merge" >&2
        fi
    fi
}

scan_loop() {
    local temp_file=$(mktemp)
    
    echo "[Scan] Listening for probe requests..."
    echo "[Scan] Press Ctrl+C to stop"
    echo ""
    
    declare -A seen
    declare -a probes
    
    tcpdump -i "$MONITOR_IF" -e -l subtype probe-req 2>/dev/null | while read -r line; do
        local parsed=$(parse_probe_request "$line")
        if [ -n "$parsed" ]; then
            IFS='|' read -r ssid client_mac bssid signal date ts <<< "$parsed"
            local key="${client_mac}:${ssid}"
            
            if [ -z "${seen[$key]}" ]; then
                seen[$key]=1
                probes+=("$parsed")
                
                if [ "$UNIQUE_ONLY" = false ]; then
                    echo "[$(date +%H:%M:%S)] SSID: $ssid | Client: $client_mac | BSSID: $bssid | Signal: ${signal}dBm"
                fi
            fi
        fi
    done &
    
    local tcpdump_pid=$!
    
    if [ -n "$DURATION" ]; then
        sleep "$DURATION"
        kill $tcpdump_pid 2>/dev/null || true
    else
        wait $tcpdump_pid
    fi
}

main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--interface)
                INTERFACE="$2"
                shift 2
                ;;
            -d|--duration)
                DURATION="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            -m|--merge)
                MERGE_FILE="$2"
                shift 2
                ;;
            --unique)
                UNIQUE_ONLY=true
                shift
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
    
    if [ -z "$INTERFACE" ]; then
        echo "[Error] Interface is required. Use -i <interface>"
        show_help
        exit 1
    fi
    
    echo "[Check] Verifying dependencies..."
    command -v iw &>/dev/null || { echo "[Error] iw not found. Install wireless-tools."; exit 1; }
    command -v tcpdump &>/dev/null || { echo "[Error] tcpdump not found. Install tcpdump."; exit 1; }
    
    setup_monitor_mode "$INTERFACE"
    
    declare -a all_probes
    if [ -n "$MERGE_FILE" ] && [ -f "$MERGE_FILE" ]; then
        echo "[Merge] Loading existing data from $MERGE_FILE..."
        while IFS= read -r line; do
            all_probes+=("$line")
        done < <(merge_existing)
    fi
    
    declare -A seen
    declare -a probes
    local output=""
    
    echo "[Scan] Starting capture on $MONITOR_IF..."
    if [ -n "$DURATION" ]; then
        echo "[Scan] Duration: ${DURATION} seconds"
    fi
    echo ""
    
    timeout "${DURATION:-0}" tcpdump -i "$MONITOR_IF" -e -l subtype probe-req 2>/dev/null | while read -r line; do
        local ssid=$(echo "$line" | grep -oP '(?<=SSID: ).*?(?=\s*$)' | head -1 | tr -d '[:space:]')
        [ -z "$ssid" ] && continue
        
        local client_mac=$(echo "$line" | grep -oP '(SA:|Source address: )[0-9a-fA-F:]+' | grep -oP '[0-9a-fA-F:]{17}' | head -1)
        [ -z "$client_mac" ] && continue
        
        local bssid=$(echo "$line" | grep -oP '(BSSID:|BSS Id: )[0-9a-fA-F:]+' | grep -oP '[0-9a-fA-F:]{17}' | head -1)
        [ -z "$bssid" ] && bssid="ff:ff:ff:ff:ff:ff"
        
        local signal=$(echo "$line" | grep -oP 'signal: -?[0-9]+' | grep -oP '-?[0-9]+' | head -1)
        [ -z "$signal" ] && signal="0"
        
        local key="${client_mac}:${ssid}"
        if [ -z "${seen[$key]}" ]; then
            seen[$key]=1
            probes+=("${ssid}|${client_mac}|${bssid}|${signal}|$(date -Iseconds)")
            echo "[$(date +%H:%M:%S)] SSID: $ssid | Client: $client_mac | Signal: ${signal}dBm"
        fi
    done &
    
    local tcpdump_pid=$!
    
    if [ -n "$DURATION" ]; then
        sleep "$DURATION"
    else
        sleep 1
    fi
    
    wait $tcpdump_pid 2>/dev/null || true
    
    echo ""
    echo "[Scan] Capture complete."
    echo "[Scan] Found ${#probes[@]} unique probe requests."
    
    if [ ${#probes[@]} -gt 0 ]; then
        output=$(generate_json probes "$UNIQUE_ONLY")
        
        if [ -n "$OUTPUT_FILE" ]; then
            echo "$output" > "$OUTPUT_FILE"
            echo "[Output] Saved to $OUTPUT_FILE"
        else
            echo "$output"
        fi
    else
        echo "{ \"scan_time\": \"$(date -Iseconds)\", \"interface\": \"$MONITOR_IF\", \"probes\": [], \"message\": \"No probe requests captured\" }"
    fi
}

main "$@"
