#!/bin/bash

# =============================================================================
# scan.sh - DEPRECATED - Use scan.py instead
# =============================================================================
# This script is deprecated. Please use scan.py instead for better JSON handling
# and real-time probe capture with merging support.
#
# DEPRECATED: scan.py provides better:
#   - Real-time CSV monitoring
#   - Proper JSON merging
#   - Cleaner Python-based parsing
#
# To use the new version:
#   python3 ./scan.py -d 60
# =============================================================================

# Exit if called (warn user)
if [[ "${SCAN_DEPRECATED_WARNED:-0}" != "1" ]]; then
    echo "WARNING: scan.sh is deprecated. Use: python3 ./scan.py -d <seconds>"
    echo ""
    export SCAN_DEPRECATED_WARNED=1
fi

# =============================================================================
# scan.sh - Capture WiFi probe requests from nearby clients
# =============================================================================
# Uses airodump-ng to capture probe request frames sent by WiFi clients
# searching for networks. Outputs JSON with client MACs and requested SSIDs.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/skeleton.sh"
source "$SCRIPT_DIR/common.sh"
source "$SCRIPT_DIR/network.sh"

OUTPUT_FILE=""
UNIQUE_ONLY=false
DURATION=""
MONITOR_IF=""
RESTORE_MANAGED=false
AIRODUMP_PID=""
CSV_FILE=""

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Scan for WiFi probe requests.

OPTIONS:
    -i, --interface <name>    WiFi interface (auto-detect if omitted)
    -d, --duration <sec>      Scan duration in seconds (default: continuous)
    -o, --output <file>       Output JSON file (default: ./probes.json)
        --unique               Show only unique SSIDs
        --cleanup              Restore managed mode after scan
    -h, --help               Show this help message

EXAMPLES:
    $(basename "$0") -d 60 -o probes.json

EOF
}

INTERRUPTED=false

cleanup() {
    echo -e "\n[Cleanup] Stopping airodump-ng..."
    if [[ -n "$AIRODUMP_PID" ]] && is_process_running "$AIRODUMP_PID"; then
        kill_process "$AIRODUMP_PID" 5
        AIRODUMP_PID=""
    fi
    
    if [[ "$RESTORE_MANAGED" == true ]] && [[ -n "$MONITOR_IF" ]]; then
        echo "[Cleanup] Restoring managed mode..."
        teardown_monitor_mode "$MONITOR_IF"
    elif [[ -n "$MONITOR_IF" ]]; then
        echo "[Cleanup] Interface in monitor mode (ready for start.sh)"
    fi
}

handle_interrupt() {
    echo -e "\n[Interrupt] Saving..."
    INTERRUPTED=true
}

run_airodump_scan() {
    local temp_base="/tmp/wifi_scan_$$"
    
    rm -f "${temp_base}"-* 2>/dev/null || true
    
    echo "[Scan] Starting on $MONITOR_IF (Ctrl+C to stop)..."
    
    CSV_FILE="${temp_base}-01.csv"
    
    airodump-ng --output-format csv --write-interval 1 -w "$temp_base" "$MONITOR_IF" >/dev/null 2>&1 &
    AIRODUMP_PID=$!
    
    echo "[Scan] Running (PID: $AIRODUMP_PID)..."
    
    sleep 2
    
    if ! is_process_running "$AIRODUMP_PID"; then
        log_error "airodump-ng failed"
        return 1
    fi
    
    local elapsed=0
    local sleep_interval=2
    
    while is_process_running "$AIRODUMP_PID"; do
        [[ "$INTERRUPTED" == true ]] && break
        [[ -n "$DURATION" ]] && [[ $elapsed -ge "$DURATION" ]] && break
        sleep "$sleep_interval"
        elapsed=$((elapsed + sleep_interval))
    done
    
    echo "[Scan] Stopping..."
    kill_process "$AIRODUMP_PID" 5
    AIRODUMP_PID=""
    
    for csv in "${temp_base}"-*.csv; do
        [[ -f "$csv" ]] && [[ -s "$csv" ]] && CSV_FILE="$csv" && break
    done
    
    if [[ -f "$CSV_FILE" ]]; then
        echo "[Scan] Captured: $(stat -c%s "$CSV_FILE") bytes"
    fi
}

parse_probes() {
    local csv_file="$1"
    
    if is_file_empty "$csv_file"; then
        return 1
    fi
    
    echo "[Parse] Processing $csv_file..." >&2
    
    local tmp_file="/tmp/probes_parse_$$.txt"
    grep -A 50000 'Station MAC' "$csv_file" | tail -n +2 > "$tmp_file"
    
    declare -A mac_ssids
    
    while IFS= read -r line; do
        [[ -z "${line// /}" ]] && continue
        
        mac=$(echo "$line" | awk -F',' '{print $1}' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\r')
        probed=$(echo "$line" | awk -F',' '{for(i=7;i<=NF;i++) printf "%s,", $i}' | sed 's/,$//' | tr -d '\r')
        
        [[ -z "$mac" ]] && continue
        
        IFS=',' read -ra ssid_array <<< "$probed"
        for ssid in "${ssid_array[@]}"; do
            ssid=$(echo "$ssid" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\r')
            [[ -z "$ssid" ]] && continue
            
            if [[ -z "${mac_ssids[$mac]}" ]]; then
                mac_ssids[$mac]="$ssid"
            else
                mac_ssids[$mac]="${mac_ssids[$mac]}|$ssid"
            fi
        done
    done < "$tmp_file"
    
    rm -f "$tmp_file"
    
    local count=${#mac_ssids[@]}
    echo "[Result] $count unique clients" >&2
    
    for mac in "${!mac_ssids[@]}"; do
        local ssids="${mac_ssids[$mac]}"
        echo "$mac|$ssids"
    done
}

load_existing_json() {
    local json_file="$1"
    declare -A mac_ssids
    
    if [[ ! -f "$json_file" ]] || is_file_empty "$json_file"; then
        return
    fi
    
    while IFS='|' read -r mac ssids; do
        mac_ssids["$mac"]="$ssids"
    done < <(grep '"mac":' "$json_file" | sed 's/.*"mac": *"\([^"]*\)".*/\1/' | while read -r mac; do
        local ssids=$(grep -A1 "\"mac\": *\"$mac\"" "$json_file" | grep '"ssids":' | sed 's/.*\[ *\(.*\) *\].*/\1/' | tr -d '"' | tr ',' '|' | sed 's/|*$//')
        echo "$mac|$ssids"
    done)
}

output_merged_json() {
    local -n mac_ref="$1"
    echo "{"
    echo "  \"interface\": \"$MONITOR_IF\","
    echo "  \"clients\": ["
    
    local first=true
    for mac in "${!mac_ref[@]}"; do
        local class=$(classify_mac "$mac")
        local ssids="${mac_ref[$mac]}"
        
        IFS='|' read -ra ssid_array <<< "$ssids"
        declare -A unique_ssids
        for s in "${ssid_array[@]}"; do
            [[ -n "$s" ]] && unique_ssids["$s"]=1
        done
        
        [[ "$first" == true ]] && first=false || echo ","
        echo "    {"
        echo -n "      \"class\": \"$class\", \"mac\": \"$mac\", \"ssids\": ["
        
        local first_ssid=true
        for s in "${!unique_ssids[@]}"; do
            [[ "$first_ssid" == true ]] && first_ssid=false || echo -n ", "
            echo -n "\"$s\""
        done
        
        echo "    ]}"
    done
    
    echo ""
    echo "  ]"
    echo "}"
}

main() {
    local INTERFACE=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--interface) INTERFACE="$2"; shift 2 ;;
            -d|--duration) DURATION="$2"; shift 2 ;;
            -o|--output) OUTPUT_FILE="$2"; shift 2 ;;
            --unique) UNIQUE_ONLY=true; shift ;;
            --cleanup) RESTORE_MANAGED=true; shift ;;
            -h|--help) show_help; exit 0 ;;
            *) echo "Unknown: $1"; show_help; exit 1 ;;
        esac
    done
    
    [[ -z "$OUTPUT_FILE" ]] && OUTPUT_FILE="./probes.json"
    
    require_root
    require_all_tools iw airodump-ng
    
    if [[ -z "$INTERFACE" ]]; then
        echo "[Detect] Auto-detecting interface..."
        INTERFACE=$(get_external_interface)
        [[ -z "$INTERFACE" ]] && { log_error "No interface found"; exit 1; }
    fi
    echo "[Detect] Using: $INTERFACE"
    
    setup_monitor_mode "$INTERFACE" || exit 1
    MONITOR_IF="$INTERFACE"
    
    trap cleanup EXIT
    trap handle_interrupt INT
    
    run_airodump_scan
    
    declare -A merged_clients
    
    if [[ -f "$OUTPUT_FILE" ]] && [[ -s "$OUTPUT_FILE" ]]; then
        echo "[Merge] Loading existing data from $OUTPUT_FILE..." >&2
        while IFS='|' read -r mac ssids; do
            [[ -n "$mac" ]] && merged_clients["$mac"]="$ssids"
        done < <(grep '"mac":' "$OUTPUT_FILE" | sed -E 's/.*"mac": *"([^"]*)".*/\1/' | while read -r mac; do
            local ssid_line=$(grep -B0 -A1 "\"mac\": *\"$mac\"" "$OUTPUT_FILE" 2>/dev/null | grep '"ssids":' | sed -E 's/.*\[(.*)\].*/\1/')
            local clean_ssids=$(echo "$ssid_line" | tr -d '"' | tr ',' '|' | sed 's/|$//')
            [[ -n "$mac" ]] && echo "$mac|${clean_ssids:-}"
        done)
    fi
    
    if [[ -f "$CSV_FILE" ]] && [[ -s "$CSV_FILE" ]]; then
        echo "[Merge] Adding new scan results..." >&2
        while IFS='|' read -r mac ssids; do
            [[ -z "$mac" ]] && continue
            
            if [[ -n "${merged_clients[$mac]}" ]]; then
                merged_clients["$mac"]="${merged_clients[$mac]}|${ssids}"
            else
                merged_clients["$mac"]="$ssids"
            fi
        done < <(parse_probes "$CSV_FILE")
    fi
    
    local count=${#merged_clients[@]}
    echo "[Merge] Total unique clients: $count" >&2
    
    output_merged_json merged_clients > "$OUTPUT_FILE"
    echo "[Output] Saved: $OUTPUT_FILE"
}

main "$@"
