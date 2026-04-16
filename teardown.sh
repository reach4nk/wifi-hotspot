#!/bin/bash
apt remove --purge -y hostapd dnsmasq
apt autoremove -y
echo "Removed hotspot software."
