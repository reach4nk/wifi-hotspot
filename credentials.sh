#!/bin/bash
# =============================================================================
# credentials.sh - Credential generation utilities
# =============================================================================
# Functions for generating WiFi credentials:
#   - Random word generation (adjective + noun + number)
#   - WPA/WPA2 password generation
#   - WEP key generation

# =============================================================================
# WORD LISTS
# =============================================================================

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

# =============================================================================
# RANDOM WORD GENERATION
# =============================================================================

# -----------------------------------------------------------------------------
# random_element()
# Pick a random element from an array.
# Internal function used by other generators.
#
# Args:
#   array_name - Name of the array variable
# Returns:
#   A random element from the array
# -----------------------------------------------------------------------------
random_element() {
    local array_name="$1"
    local arr=("${!array_name}")
    echo "${arr[$RANDOM % ${#arr[@]}]}"
}

# -----------------------------------------------------------------------------
# random_word()
# Generate a memorable random word (adjective + noun + number).
# Example: "BlueNode482"
#
# Returns:
#   A random word string
# -----------------------------------------------------------------------------
random_word() {
    local adj=$(random_element ADJECTIVES[@])
    local noun=$(random_element NOUNS[@])
    local num=$((100 + RANDOM % 900))
    echo "${adj}${noun}${num}"
}

# -----------------------------------------------------------------------------
# random_word_simple()
# Generate a random word without number suffix.
# Example: "BlueNode"
#
# Returns:
#   A random word string
# -----------------------------------------------------------------------------
random_word_simple() {
    local adj=$(random_element ADJECTIVES[@])
    local noun=$(random_element NOUNS[@])
    echo "${adj}${noun}"
}

# =============================================================================
# PASSWORD GENERATION
# =============================================================================

# -----------------------------------------------------------------------------
# random_special_char()
# Get a random special character.
#
# Returns:
#   A random special character
# -----------------------------------------------------------------------------
random_special_char() {
    random_element SPECIAL_CHARS[@]
}

# -----------------------------------------------------------------------------
# generate_password()
# Generate a WPA/WPA2 password (word + special char).
# Example: "BlueNode382#"
# Meets WPA minimum 8 character requirement.
#
# Returns:
#   A password string
# -----------------------------------------------------------------------------
generate_password() {
    local base=$(random_word)
    local special=$(random_special_char)
    echo "${base}${special}"
}

# -----------------------------------------------------------------------------
# generate_simple_password()
# Generate a simple password (just words, no special char).
# Example: "BlueNode382"
#
# Returns:
#   A password string
# -----------------------------------------------------------------------------
generate_simple_password() {
    random_word
}

# -----------------------------------------------------------------------------
# generate_passphrase()
# Generate a passphrase from multiple random words.
# Example: "Blue Node 482 Star"
#
# Args:
#   word_count - Number of words (default: 3)
# Returns:
#   A passphrase string
# -----------------------------------------------------------------------------
generate_passphrase() {
    local word_count="${1:-3}"
    local words=()
    
    for ((i=0; i<word_count; i++)); do
        words+=($(random_word_simple))
    done
    
    local num=$((10 + RANDOM % 90))
    echo "${words[*]} $num"
}

# =============================================================================
# WEP KEY GENERATION
# =============================================================================

# -----------------------------------------------------------------------------
# generate_wep_key()
# Generate a WEP encryption key (26 hex characters).
# WEP uses hexadecimal keys for encryption.
#
# Returns:
#   A 26-character hex string
# -----------------------------------------------------------------------------
generate_wep_key() {
    openssl rand -hex 13
}

# -----------------------------------------------------------------------------
# generate_wep_key_128bit()
# Generate a 128-bit WEP key (32 hex characters).
#
# Returns:
#   A 32-character hex string
# -----------------------------------------------------------------------------
generate_wep_key_128bit() {
    openssl rand -hex 26
}

# =============================================================================
# SSID GENERATION
# =============================================================================

# -----------------------------------------------------------------------------
# generate_ssid()
# Generate a WiFi SSID with distinctive prefix.
# Example: "!BlueNode482🛜" (WiFi emoji suffix)
#
# Args:
#   prefix - Prefix character (default: "!")
# Returns:
#   An SSID string
# -----------------------------------------------------------------------------
generate_ssid() {
    local prefix="${1:-!}"
    echo "${prefix}$(random_word)🛜"
}

# -----------------------------------------------------------------------------
# generate_simple_ssid()
# Generate a simple SSID without emoji.
# Example: "BlueNode482"
#
# Returns:
#   An SSID string
# -----------------------------------------------------------------------------
generate_simple_ssid() {
    random_word
}

# =============================================================================
# VALIDATION
# =============================================================================

# -----------------------------------------------------------------------------
# validate_wpa_password()
# Check if a password meets WPA requirements.
# WPA/WPA2 requires 8-63 characters.
#
# Args:
#   password - Password to validate
# Returns: 0 if valid, 1 if invalid
# -----------------------------------------------------------------------------
validate_wpa_password() {
    local password="$1"
    local len=${#password}
    
    if [[ $len -lt 8 ]]; then
        log_error "Password too short (min 8 chars): $len"
        return 1
    fi
    
    if [[ $len -gt 63 ]]; then
        log_error "Password too long (max 63 chars): $len"
        return 1
    fi
    
    return 0
}

# -----------------------------------------------------------------------------
# validate_wep_key()
# Check if a key is valid WEP format (26 hex chars).
#
# Args:
#   key - Key to validate
# Returns: 0 if valid, 1 if invalid
# -----------------------------------------------------------------------------
validate_wep_key() {
    local key="$1"
    
    if ! [[ $key =~ ^[0-9a-fA-F]{26}$ ]]; then
        log_error "Invalid WEP key (must be 26 hex characters)"
        return 1
    fi
    
    return 0
}

# -----------------------------------------------------------------------------
# validate_ssid()
# Check if an SSID is valid.
# 802.11 SSIDs: 1-32 bytes
#
# Args:
#   ssid - SSID to validate
# Returns: 0 if valid, 1 if invalid
# -----------------------------------------------------------------------------
validate_ssid() {
    local ssid="$1"
    local len=${#ssid}
    
    if [[ $len -lt 1 ]]; then
        log_error "SSID cannot be empty"
        return 1
    fi
    
    if [[ $len -gt 32 ]]; then
        log_error "SSID too long (max 32 chars): $len"
        return 1
    fi
    
    return 0
}

# =============================================================================
# CREDENTIAL SET VALIDATION
# =============================================================================

# -----------------------------------------------------------------------------
# validate_encryption_mode()
# Validate encryption mode string.
#
# Args:
#   mode - Encryption mode (open, wep, wpa, wpa2)
# Returns: 0 if valid, 1 if invalid
# -----------------------------------------------------------------------------
validate_encryption_mode() {
    local mode="$1"
    
    case "$mode" in
        open|wep|wpa|wpa2) return 0 ;;
        *) 
            log_error "Invalid encryption mode: $mode"
            return 1
            ;;
    esac
}

# -----------------------------------------------------------------------------
# ensure_valid_credentials()
# Validate and generate credentials if needed.
# Outputs SSID and password on single line separated by |
#
# Args:
#   ssid - SSID (generated if empty)
#   password - Password (generated based on encryption if empty)
#   encryption - Encryption mode (default: wpa2)
# Returns:
#   Outputs "ssid|password" on stdout
# -----------------------------------------------------------------------------
ensure_valid_credentials() {
    local ssid="$1"
    local password="$2"
    local encryption="${3:-wpa2}"
    
    validate_encryption_mode "$encryption" || return 1
    
    case "$encryption" in
        open)
            password=""
            [[ -z "$ssid" ]] && ssid=$(generate_ssid)
            ;;
        wep)
            [[ -z "$ssid" ]] && ssid=$(generate_ssid)
            [[ -z "$password" ]] && password=$(generate_wep_key)
            validate_wep_key "$password" || return 1
            ;;
        wpa|wpa2)
            [[ -z "$ssid" ]] && ssid=$(generate_ssid)
            [[ -z "$password" ]] && password=$(generate_password)
            validate_wpa_password "$password" || return 1
            ;;
    esac
    
    validate_ssid "$ssid" || return 1
    
    echo "${ssid}|${password}"
}
