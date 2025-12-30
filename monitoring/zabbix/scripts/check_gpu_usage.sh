#!/bin/bash
# Zabbix external script to check GPU utilization

# Requires nvidia-smi to be available

if command -v nvidia-smi &> /dev/null; then
    # Get GPU utilization percentage
    gpu_util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -n1)
    echo "$gpu_util"
else
    echo 0
fi
