#!/bin/bash
# Zabbix external script to check Home Assistant health

HA_URL="${1:-http://home-assistant:8123}"

# Check Home Assistant API
response=$(curl -s -o /dev/null -w "%{http_code}" "${HA_URL}/api/")

if [ "$response" -eq 200 ]; then
    echo 1  # Healthy
else
    echo 0  # Unhealthy
fi
