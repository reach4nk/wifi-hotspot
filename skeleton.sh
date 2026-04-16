#!/bin/bash
# =============================================================================
# skeleton.sh - Base script template for WiFi hotspot scripts
# =============================================================================
# Source this file at the beginning of any script to get:
#   - Automatic SCRIPT_DIR detection
#   - Module sourcing helpers
#   - Logging functions (log_info, log_warn, log_error)
#   - Root privilege check (require_root)
#   - Cleanup handler (cleanup_on_exit)
#   - Signal handling (trap setup)
#
# Usage:
#   source "$(dirname "${BASH_SOURCE[0]}")/skeleton.sh"
#   init_script  # Call this in your main() function
# =============================================================================

# Detect the directory where the script (not this file) is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Global variables for script state
SKIP_CLEANUP=false
CLEANUP_HOOKS=()

# =============================================================================
# MODULE SOURCING
# =============================================================================

source_common() {
    source "$SCRIPT_DIR/common.sh"
}

source_credentials() {
    source "$SCRIPT_DIR/credentials.sh"
}

source_network() {
    source "$SCRIPT_DIR/network.sh"
}

source_firewall() {
    source "$SCRIPT_DIR/firewall.sh"
}

source_services() {
    source "$SCRIPT_DIR/services.sh"
}

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

log_info() {
    echo "[INFO] $*"
}

log_warn() {
    echo "[WARN] $*" >&2
}

log_error() {
    echo "[ERROR] $*" >&2
}

log_debug() {
    [[ "${DEBUG:-0}" == "1" ]] && echo "[DEBUG] $*" >&2 || true
}

# =============================================================================
# PRIVILEGE CHECKING
# =============================================================================

require_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

require_tool() {
    local tool="$1"
    if ! command -v "$tool" &>/dev/null; then
        log_error "Required tool not found: $tool"
        log_error "Run ./setup.sh to install dependencies"
        exit 1
    fi
}

require_all_tools() {
    for tool in "$@"; do
        require_tool "$tool"
    done
}

# =============================================================================
# CLEANUP HANDLING
# =============================================================================

cleanup_on_exit() {
    local exit_code=$?
    for hook in "${CLEANUP_HOOKS[@]}"; do
        eval "$hook"
    done
    exit $exit_code
}

add_cleanup_hook() {
    CLEANUP_HOOKS+=("$1")
}

register_cleanup_handler() {
    trap cleanup_on_exit EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
}

# =============================================================================
# SCRIPT INITIALIZATION
# =============================================================================

init_script() {
    require_root
    register_cleanup_handler
    log_info "$(basename "$0") initialized"
}

# =============================================================================
# CONFIG FILE HELPERS
# =============================================================================

write_config() {
    local path="$1"
    cat > "$path"
    chmod 600 "$path" 2>/dev/null || true
}

# =============================================================================
# TEMP FILE MANAGEMENT
# =============================================================================

create_temp_file() {
    mktemp
}

create_temp_dir() {
    mktemp -d
}

cleanup_temp_file() {
    local path="$1"
    add_cleanup_hook "rm -f '$path'"
}

cleanup_temp_dir() {
    local path="$1"
    add_cleanup_hook "rm -rf '$path'"
}

# =============================================================================
# STRING UTILITIES
# =============================================================================

trim() {
    local var="$1"
    echo "$var" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
}

is_empty() {
    local var="$1"
    [[ -z "${var// /}" ]]
}

# =============================================================================
# ARRAY UTILITIES  
# =============================================================================

array_contains() {
    local element="$1"
    shift
    local arr=("$@")
    for item in "${arr[@]}"; do
        [[ "$item" == "$element" ]] && return 0
    done
    return 1
}
