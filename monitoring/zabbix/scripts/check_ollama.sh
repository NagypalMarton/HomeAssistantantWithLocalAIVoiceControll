#!/bin/bash
# Zabbix external script to check Ollama health and model availability

OLLAMA_URL="${1:-http://ollama:11434}"

# Check Ollama API health
response=$(curl -s -o /dev/null -w "%{http_code}" "${OLLAMA_URL}/api/tags")

if [ "$response" -eq 200 ]; then
    # Get number of available models
    model_count=$(curl -s "${OLLAMA_URL}/api/tags" | jq '.models | length')
    echo "$model_count"
else
    echo 0  # Unhealthy
fi
