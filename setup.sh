#!/bin/bash
set -e

apt update
apt install -y hostapd dnsmasq iptables

systemctl stop hostapd || true
systemctl stop dnsmasq || true
systemctl disable hostapd || true
systemctl disable dnsmasq || true

echo "Setup complete."
