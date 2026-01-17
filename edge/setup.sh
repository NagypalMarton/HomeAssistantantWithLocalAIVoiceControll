#!/usr/bin/env bash
# Setup script for Edge satellite configuration
# Asks for HA URL and token, generates random device name

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
  echo -e "${GREEN}[INFO]${NC} $*"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $*"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $*"
}

# Generate random device name
generate_device_name() {
  local adjectives=("Smart" "Quick" "Bright" "Clear" "Swift" "Keen" "Wise" "Noble" "Bold")
  local nouns=("Speaker" "Listener" "Voice" "Echo" "Beacon" "Relay" "Hub" "Node" "Point")
  local random_adj=${adjectives[$((RANDOM % ${#adjectives[@]}))]}
  local random_noun=${nouns[$((RANDOM % ${#nouns[@]}))]}
  local random_num=$((RANDOM % 999))
  echo "${random_adj}${random_noun}${random_num}"
}

# Validate HA token by making a test request
validate_ha_token() {
  local ha_url="$1"
  local ha_token="$2"

  # Remove trailing slash
  ha_url="${ha_url%/}"

  log_info "Validating Home Assistant connection..."
  
  if curl -fsS \
    -H "Authorization: Bearer $ha_token" \
    -H "Content-Type: application/json" \
    --max-time 5 \
    "${ha_url}/api/" >/dev/null 2>&1; then
    log_info "✓ Home Assistant connection successful"
    return 0
  else
    log_error "✗ Failed to connect to Home Assistant"
    log_error "  Check URL and token, and make sure HA is reachable"
    return 1
  fi
}

# Main setup
main() {
  echo ""
  echo "╔════════════════════════════════════════════════════════╗"
  echo "║         Edge Satellite Setup Configuration             ║"
  echo "╚════════════════════════════════════════════════════════╝"
  echo ""

  # Generate random device name
  DEVICE_NAME=$(generate_device_name)
  log_info "Generated device name: $DEVICE_NAME"
  echo ""

  # Prompt for HA URL
  read -p "Enter Home Assistant URL (e.g., http://192.168.1.100:8123): " HA_URL
  if [[ -z "$HA_URL" ]]; then
    log_error "Home Assistant URL cannot be empty"
    exit 1
  fi

  # Prompt for HA token
  echo ""
  read -sp "Enter Home Assistant Long-Lived Access Token: " HA_TOKEN
  echo ""
  if [[ -z "$HA_TOKEN" ]]; then
    log_error "Home Assistant token cannot be empty"
    exit 1
  fi

  # Validate connection
  echo ""
  if ! validate_ha_token "$HA_URL" "$HA_TOKEN"; then
    log_warn "Setup will continue, but verify your credentials"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log_info "Setup cancelled"
      exit 0
    fi
  fi

  # Create/update .env file
  cat > "$ENV_FILE" << EOF
# Home Assistant Configuration
HA_URL=$HA_URL
HA_TOKEN=$HA_TOKEN

# Device Configuration
DEVICE_NAME=$DEVICE_NAME

# Health Watcher Settings
CHECK_INTERVAL=15
ALERT_COOLDOWN=60
ALERT_TEXT="HA nem érhető el!"
EOF

  log_info "Configuration saved to $ENV_FILE"
  echo ""
  echo "╔════════════════════════════════════════════════════════╗"
  echo "║                 Setup Complete                         ║"
  echo "╚════════════════════════════════════════════════════════╝"
  echo ""
  echo "Device name: $DEVICE_NAME"
  echo "HA URL:      $HA_URL"
  echo "Token:       ••••••••••••••••"
  echo ""
  log_info "Next steps:"
  echo "  1. Start the stack:    docker compose up -d"
  echo "  2. Check logs:         docker compose logs -f"
  echo "  3. Monitor health:     systemctl --user status ha-healthwatch.service"
  echo ""
}

main "$@"
