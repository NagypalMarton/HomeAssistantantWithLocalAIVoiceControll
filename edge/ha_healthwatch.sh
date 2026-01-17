#!/usr/bin/env bash
# HA health watcher that speaks a Hungarian alert via Piper when HA is unreachable.
#
# Requirements:
# - Docker installed and running
# - Edge stack up (wyoming-piper and wyoming-satellite containers)
# - Shared volume ./tts-cache mounted to /cache in both containers (configured in docker-compose.yml)
#
# Usage:
#   HA_URL=http://homeassistant.local:8123 ./ha_healthwatch.sh
# Optional envs:
#   CHECK_INTERVAL=15   # seconds between checks
#   ALERT_COOLDOWN=60   # min seconds between repeated alerts
#   ALERT_TEXT="HA nem érhető el!"  # custom message in Hungarian

set -euo pipefail

HA_URL="${HA_URL:-http://homeassistant.local:8123}"
CHECK_INTERVAL="${CHECK_INTERVAL:-15}"
ALERT_COOLDOWN="${ALERT_COOLDOWN:-60}"
ALERT_TEXT="${ALERT_TEXT:-HA nem érhető el!}"
CACHE_WAV="/cache/ha_unavailable.wav"
PIPER_CONTAINER="wyoming-piper"
SATELLITE_CONTAINER="wyoming-satellite"

last_alert_ts=0

log() {
  echo "[ha_healthwatch] $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

require_container() {
  local name="$1"
  if ! docker ps --format '{{.Names}}' | grep -qx "$name"; then
    log "Container '$name' not running. Start the edge stack with: docker compose up -d"
    exit 1
  fi
}

synthesize_alert() {
  # Generate WAV using Piper in container
  docker exec "$PIPER_CONTAINER" bash -c "
    echo '$ALERT_TEXT' | /usr/src/.venv/bin/piper \
      --model /data/hu_HU-imre-medium.onnx \
      --output_file '$CACHE_WAV'
  " 2>&1 | grep -v "^\[" || true
}

play_alert() {
  # Play WAV from shared /cache using satellite's ALSA device
  docker exec -i "$SATELLITE_CONTAINER" aplay -D plughw:4,0 -r 22050 -c 1 -f S16_LE -t wav "$CACHE_WAV" >/dev/null 2>&1 || true
}

# Pre-flight checks
require_container "$PIPER_CONTAINER"
require_container "$SATELLITE_CONTAINER"

log "Watching HA availability at: $HA_URL (interval=${CHECK_INTERVAL}s, cooldown=${ALERT_COOLDOWN}s)"

while true; do
  if curl -fsS --max-time 3 "$HA_URL" >/dev/null; then
    # HA reachable
    :
  else
    now_ts=$(date +%s)
    if (( now_ts - last_alert_ts >= ALERT_COOLDOWN )); then
      log "HA unreachable → speaking alert"
      synthesize_alert || log "Failed to synthesize alert"
      play_alert || log "Failed to play alert"
      last_alert_ts=$now_ts
    fi
  fi
  sleep "$CHECK_INTERVAL"
done
