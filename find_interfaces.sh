#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

internal=$(get_internal_interface)
external=$(get_external_interface)

echo "Internal Interface: $internal"
echo "External Interface: $external"

