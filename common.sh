#!/bin/bash

get_internal_interface() {
    internal_interface=$(iwconfig 2>/dev/null | grep -B 1 'Mode:Managed' | grep -o '^[^ ]*')
    echo "$internal_interface"
}

get_external_interface() {
    external_interface=$(iwconfig 2>/dev/null | grep -B 1 'Mode:Master' | grep -o '^[^ ]*')
    echo "$external_interface"
}
