#!/bin/bash
# =============================================================================
# scan.sh - Capture WiFi probe requests from nearby clients
# =============================================================================
# Uses airodump-ng to capture probe request frames sent by WiFi clients
# searching for networks. Outputs JSON with client MACs and requested SSIDs.
#
# The MAC address classification helps identify:
#   - "local" MACs: Randomized addresses (privacy feature on modern devices)
#   - "actual" MACs: Real device MACs that could be tracked

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

OUTPUT_FILE=""
UNIQUE_ONLY=false
DURATION=""
MONITOR_IF=""
RESTORE_MANAGED=false
AIRODUMP_PID=""
CSV_FILE=""

# =============================================================================
# show_help() - Display usage information
# =============================================================================
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

# =============================================================================
# cleanup() - Restore system state on exit
# =============================================================================
# Called automatically via EXIT trap. Handles:
#   - Stopping airodump-ng process
#   - Optionally restoring managed mode (if --cleanup was specified)
#   - Leaving interface in monitor mode for use by start.sh (default)
# =============================================================================
cleanup() {
    # Stop airodump-ng if running
    if [ -n "$AIRODUMP_PID" ] && kill -0 "$AIRODUMP_PID" 2>/dev/null; then
        echo -e "\n[Cleanup] Stopping airodump-ng..."
        kill "$AIRODUMP_PID" 2>/dev/null || true
        wait "$AIRODUMP_PID" 2>/dev/null || true
        AIRODUMP_PID=""
    fi
    
    # Restore managed mode if --cleanup was specified
    if [ "$RESTORE_MANAGED" = true ] && [ -n "$MONITOR_IF" ]; then
        echo "[Cleanup] Restoring managed mode..."
        ip link set "$MONITOR_IF" down 2>/dev/null || true
        iw dev "$MONITOR_IF" set type managed 2>/dev/null || true
        ip link set "$MONITOR_IF" up 2>/dev/null || true
    elif [ -n "$MONITOR_IF" ]; then
        # Default: leave interface in monitor mode for start.sh
        echo "[Cleanup] Interface in monitor mode (ready for start.sh)"
    fi
}

trap cleanup EXIT

# =============================================================================
# handle_interrupt() - Graceful Ctrl+C handling
# =============================================================================
# Creates a stop file that the scan loop checks, allowing a clean shutdown
# instead of a hard kill.
# =============================================================================
handle_interrupt() {
    echo -e "\n[Interrupt] Saving..."
    touch /tmp/wifi_scan_stop
}

# =============================================================================
# setup_monitor_mode() - Enable monitor mode on interface
# =============================================================================
# Monitor mode allows capturing all WiFi frames, including probe requests
# from clients searching for networks.
#
# Args:
#   iface - Interface name to put in monitor mode
# =============================================================================
setup_monitor_mode() {
    local iface=$1
    
    # Check current mode using iw dev
    local current_mode=$(iw dev "$iface" info 2>/dev/null | grep -i 'type' | awk '{print $2}')
    
    # Already in monitor mode - just ensure it's up
    if [ "$current_mode" = "Monitor" ]; then
        MONITOR_IF="$iface"
        echo "[Setup] Already in monitor mode: $iface"
        ip link set "$MONITOR_IF" up 2>/dev/null || true
        return
    fi
    
    # Transition to monitor mode (requires interface to be down first)
    echo "[Setup] Enabling monitor mode on $iface..."
    ip link set "$iface" down 2>/dev/null || true
    iw dev "$iface" set type monitor 2>/dev/null || true
    ip link set "$iface" up 2>/dev/null || true
    MONITOR_IF="$iface"
}

# =============================================================================
# run_airodump_scan() - Execute airodump-ng and capture CSV output
# =============================================================================
# airodump-ng outputs CSV files that are deleted when the process exits.
# We capture the process PID and the CSV filename before killing, then
# read the data before cleanup.
#
# The CSV format:
#   - Header lines before data
#   - "Station MAC" section contains probe requests
#   - Columns: MAC, First time seen, Last time seen, Power, # packets, etc.
#   - Probed SSIDs appear in columns 7+ (comma-separated)
# =============================================================================
run_airodump_scan() {
    local temp_base="/tmp/wifi_scan_$$"
    
    echo "[Scan] Starting on $MONITOR_IF (Ctrl+C to stop)..."
    
    # Clean up any previous temp files
    rm -f "${temp_base}"-* 2>/dev/null || true
    CSV_FILE="${temp_base}-01.csv"
    
    # Start airodump-ng in background
    # --output-format csv: Use CSV output format
    # --write-interval 1: Write CSV file every second
    # -w: Base filename for output
    airodump-ng --output-format csv --write-interval 1 -w "$temp_base" "$MONITOR_IF" >/dev/null 2>&1 &
    AIRODUMP_PID=$!
    
    echo "[Scan] Running (PID: $AIRODUMP_PID)..."
    
    # Give airodump time to start and create the CSV file
    sleep 2
    
    # Verify airodump is still running
    if ! kill -0 "$AIRODUMP_PID" 2>/dev/null; then
        echo "[Error] airodump-ng failed"
        return
    fi
    
    # Scan loop - runs until duration expires, stop file exists, or process dies
    local elapsed=0
    local sleep_interval=2
    local stop_file="/tmp/wifi_scan_stop"
    
    while kill -0 "$AIRODUMP_PID" 2>/dev/null; do
        # Check for stop file (created by handle_interrupt on Ctrl+C)
        [ -f "$stop_file" ] && break
        # Check if duration limit reached
        [ -n "$DURATION" ] && [ $elapsed -ge "$DURATION" ] && break
        sleep "$sleep_interval"
        elapsed=$((elapsed + sleep_interval))
    done
    
    echo "[Scan] Stopping..."
    kill "$AIRODUMP_PID" 2>/dev/null || true
    wait "$AIRODUMP_PID" 2>/dev/null || true
    AIRODUMP_PID=""
    
    # Find the CSV file that was created (may have index suffix like -01, -02)
    for csv in "${temp_base}"-*.csv; do
        [ -f "$csv" ] && [ -s "$csv" ] && CSV_FILE="$csv" && break
    done
    
    [ -f "$CSV_FILE" ] && echo "[Scan] Captured: $(stat -c%s "$CSV_FILE") bytes"
}

# =============================================================================
# is_randomized_mac() - Detect MAC address randomization
# =============================================================================
# Modern devices randomize their MAC address when probing for networks
# to prevent tracking. The randomization can be detected by checking
# the second character of the first byte:
#   - Normal (non-randomized): 0, 1, 4, 5, 8, 9, C, D (even numbers, C/D)
#   - Randomized (local): 2, 6, A, E (the "locally administered" bit is set)
#
# The least significant bit of the first byte is the "Universal/Local" bit:
#   - 0 = Universally administered (real MAC assigned by manufacturer)
#   - 1 = Locally administered (randomized or custom MAC)
#
# So: 2=0010, 6=0110, A=1010, E=1110 - all have LSB=0 but bit 1=1 = local
#
# Args:
#   mac - MAC address to check (format: AA:BB:CC:DD:EE:FF)
# Returns:
#   0 if MAC appears randomized (local)
#   1 if MAC appears real (actual)
# =============================================================================
is_randomized_mac() {
    local mac="$1"
    # Extract first byte and convert to uppercase for consistent comparison
    local first_byte=$(echo "$mac" | cut -d':' -f1 | tr '[:lower:]' '[:upper:]')
    # Get the second character of the first byte
    # e.g., for "A2:...", second char is "2"
    local second_char="${first_byte:1:1}"
    
    # Check if second char indicates local (randomized) addressing
    case "$second_char" in
        2|6|A|E) return 0 ;;
        *) return 1 ;;
    esac
}

# =============================================================================
# parse_probes() - Parse airodump CSV and generate JSON output
# =============================================================================
# The airodump-ng CSV format has two sections:
#   1. AP data (header + access points)
#   2. Station data (client probe requests) - starts after "Station MAC" line
#
# Client line format (space after commas):
#   MAC, First Time, Last Time, Power, # packets, BSSID, Probed SSIDs (col 7+)
#
# Args:
#   csv_file - Path to the CSV file to parse
# Output:
#   JSON object with scan metadata and array of clients
# =============================================================================
parse_probes() {
    local csv_file="$1"
    
    [ -f "$csv_file" ] && [ -s "$csv_file" ] || return 1
    
    echo "[Parse] Processing $csv_file..." >&2
    
    local tmp_file="/tmp/probes_parse_$$.txt"
    
    # Extract lines after "Station MAC" header (probe request data)
    # grep -A 50000: Get up to 50000 lines after "Station MAC" match
    # tail -n +2: Skip the "Station MAC" header line itself
    grep -A 50000 'Station MAC' "$csv_file" | tail -n +2 > "$tmp_file"
    
    # Associative array: MAC address -> pipe-separated list of SSIDs
    declare -A mac_ssids
    
    # Parse each line of client data
    while IFS= read -r line; do
        # Skip empty lines
        [ -z "${line// /}" ] && continue
        
        # Extract MAC address (column 1, trim whitespace)
        mac=$(echo "$line" | awk -F',' '{print $1}' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\r')
        
        # Extract probed SSIDs from columns 7 onwards
        # This handles SSIDs that may contain commas by taking all remaining columns
        probed=$(echo "$line" | awk -F',' '{for(i=7;i<=NF;i++) printf "%s,", $i}' | sed 's/,$//' | tr -d '\r')
        
        [ -z "$mac" ] && continue
        
        # Split comma-separated SSIDs into array
        IFS=',' read -ra ssid_array <<< "$probed"
        for ssid in "${ssid_array[@]}"; do
            # Trim whitespace from SSID
            ssid=$(echo "$ssid" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\r')
            [ -z "$ssid" ] && continue
            
            # Append SSID to this MAC's list (pipe-separated for later parsing)
            if [ -z "${mac_ssids[$mac]}" ]; then
                mac_ssids[$mac]="$ssid"
            else
                mac_ssids[$mac]="${mac_ssids[$mac]}|$ssid"
            fi
        done
    done < "$tmp_file"
    
    rm -f "$tmp_file"
    
    local count=${#mac_ssids[@]}
    echo "[Result] $count unique clients" >&2
    
    # Generate JSON output
    {
        echo "{"
        echo "  \"scan_time\": \"$(date -Iseconds)\","
        echo "  \"interface\": \"$MONITOR_IF\","
        echo "  \"clients\": ["
        
        local first=true
        for mac in "${!mac_ssids[@]}"; do
            # Classify MAC as "local" (randomized) or "actual" (real)
            local class="actual"
            if is_randomized_mac "$mac"; then
                class="local"
            fi
            
            # Split pipe-separated SSIDs back into array
            local ssids="${mac_ssids[$mac]}"
            IFS='|' read -ra ssid_list <<< "$ssids"
            
            # Comma separator between objects (not before first)
            [ "$first" = true ] && first=false || echo ","
            
            echo "    {"
            echo -n "      \"class\": \"$class\", \"mac\": \"$mac\", \"ssids\": ["
            
            local first_ssid=true
            for s in "${ssid_list[@]}"; do
                [ -z "$s" ] && continue
                # Comma separator between SSIDs
                [ "$first_ssid" = true ] && first_ssid=false || echo -n ", "
                echo -n "\"$s\""
            done
            
            echo "    ]}"
        done
        
        echo ""
        echo "  ]"
        echo "}"
    }
}

# =============================================================================
# main() - Entry point for scan.sh
# =============================================================================
# Command-line arguments:
#   -i, --interface   WiFi interface to use (auto-detect if omitted)
#   -d, --duration    Scan duration in seconds (default: continuous)
#   -o, --output      Output JSON file path
#   --unique          Filter to show only unique SSIDs
#   --cleanup         Restore managed mode when done
#   -h, --help        Show usage information
# =============================================================================
main() {
    local INTERFACE=""
    
    # Parse command-line arguments
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
    
    # Auto-detect interface if not specified
    if [ -z "$INTERFACE" ]; then
        echo "[Detect] Auto-detecting interface..."
        INTERFACE=$(get_external_interface)
        [ -z "$INTERFACE" ] && { echo "[Error] No interface found"; exit 1; }
    fi
    echo "[Detect] Using: $INTERFACE"
    
    # Verify required tools are installed
    command -v iw &>/dev/null || { echo "[Error] iw not found"; exit 1; }
    command -v airodump-ng &>/dev/null || { echo "[Error] airodump-ng not found"; exit 1; }
    
    # Set up monitor mode and run scan
    setup_monitor_mode "$INTERFACE"
    
    # Set up signal handlers
    trap handle_interrupt INT      # Handle Ctrl+C gracefully
    trap cleanup EXIT                # Clean up on exit
    
    run_airodump_scan
    
    # Parse results and write output file
    if [ -f "$CSV_FILE" ] && [ -s "$CSV_FILE" ]; then
        parse_probes "$CSV_FILE" > /tmp/scan_result.json
        
        if [ -n "$OUTPUT_FILE" ]; then
            cp /tmp/scan_result.json "$OUTPUT_FILE"
            echo "[Output] Saved: $OUTPUT_FILE"
        else
            cp /tmp/scan_result.json ./probes.json
            echo "[Output] Saved: ./probes.json"
        fi
    else
        echo "{ \"scan_time\": \"$(date -Iseconds)\", \"interface\": \"$MONITOR_IF\", \"probes\": [] }"
    fi
}

# Execute main with all command-line arguments
main "$@"
