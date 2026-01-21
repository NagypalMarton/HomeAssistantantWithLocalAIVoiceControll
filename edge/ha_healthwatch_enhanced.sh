#!/usr/bin/env bash
# Enhanced HA health watcher that monitors satellite logs and alerts on ASR activity when HA is unreachable.
#
# Features:
# - Continuous HA availability monitoring
# - Satellite log monitoring for ASR events
# - Immediate alert after ASR when HA is down
# - Connection loss detection with immediate alert
#
# Requirements:
# - Docker installed and running
# - Edge stack up (wyoming-piper and wyoming-satellite containers)
# - Shared volume ./tts-cache mounted to /cache in both containers

set -euo pipefail

HA_URL="${HA_URL:-http://homeassistant.local:8123}"
HA_TOKEN="${HA_TOKEN:-}"
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"
ALERT_COOLDOWN="${ALERT_COOLDOWN:-60}"
ALERT_TEXT="${ALERT_TEXT:-A Home Assistant jelenleg nem elérhető!}"
DEVICE_NAME="${DEVICE_NAME:-EdgeSatellite}"
# once: csak az első riasztás minden kiesésre, repeat: periodikus ismétlés (alapértelmezett)
OFFLINE_ALERT_MODE="${OFFLINE_ALERT_MODE:-repeat}"
CACHE_WAV="/cache/ha_unavailable.wav"
PIPER_CONTAINER="wyoming-piper"
SATELLITE_CONTAINER="wyoming-satellite"

last_alert_ts=0
ha_was_available=true
alert_sent_for_outage=false
last_log_line=""

log() {
  echo "[ha_healthwatch_enhanced] $(date '+%Y-%m-%d %H:%M:%S') - $*"
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

check_ha() {
  curl_opts=(-fsS --max-time 3)
  
  if [[ -n "$HA_TOKEN" ]]; then
    curl_opts+=(-H "Authorization: Bearer $HA_TOKEN")
  fi
  
  if curl "${curl_opts[@]}" "$HA_URL" >/dev/null 2>&1; then
    return 0  # HA available
  else
    return 1  # HA unavailable
  fi
}

alert_with_cooldown() {
  local reason="$1"
  now_ts=$(date +%s)
  if (( now_ts - last_alert_ts >= ALERT_COOLDOWN )); then
    log "HA unreachable ($reason) → speaking alert"
    synthesize_alert || log "Failed to synthesize alert"
    play_alert || log "Failed to play alert"
    last_alert_ts=$now_ts
  else
    log "HA unreachable ($reason) but cooldown active ($(( ALERT_COOLDOWN - (now_ts - last_alert_ts) ))s remaining)"
  fi
}

monitor_satellite_logs() {
  # Monitor satellite logs for ASR activity (transcript events)
  docker logs -f --tail=0 "$SATELLITE_CONTAINER" 2>&1 | while read -r line; do
    # Check for transcript/ASR completion indicators
    if [[ "$line" =~ (transcript|Transcribed|speech_to_text|recognized|ASR) ]]; then
      log "ASR activity detected in satellite logs"
      
      # Immediately check HA availability
      if ! check_ha; then
        if [[ "$OFFLINE_ALERT_MODE" == "once" && "$alert_sent_for_outage" == true ]]; then
          log "HA down after ASR, but alert already sent for this outage (once mode)"
        else
          log "HA check failed after ASR → alert"
          alert_with_cooldown "asr event"
          alert_sent_for_outage=true
        fi
      fi
    fi
    
    # Check for HA connection errors in logs
    if [[ "$line" =~ (timeout|connection.*refused|failed.*connect|unreachable) ]] && [[ "$line" =~ (home.*assistant|HA) ]]; then
      log "HA connection error detected in satellite logs"
      if ! check_ha; then
        if [[ "$OFFLINE_ALERT_MODE" == "once" && "$alert_sent_for_outage" == true ]]; then
          log "HA down (log error), alert already sent for this outage (once mode)"
        else
          alert_with_cooldown "satellite log error"
          alert_sent_for_outage=true
        fi
      fi
    fi
  done
}

monitor_ha_periodic() {
  local previous_state=true
  
  while true; do
    if check_ha; then
      if ! $previous_state; then
        log "HA is now available (restored)"
        ha_was_available=true
        alert_sent_for_outage=false
      fi
      previous_state=true
    else
      if $previous_state; then
        log "HA connection lost → immediate alert"
        synthesize_alert || log "Failed to synthesize alert"
        play_alert || log "Failed to play alert"
        last_alert_ts=$(date +%s)
        ha_was_available=false
        alert_sent_for_outage=true
      else
        if [[ "$OFFLINE_ALERT_MODE" == "repeat" ]]; then
          alert_with_cooldown "periodic check"
          alert_sent_for_outage=true
        else
          log "HA still down (once mode) — no repeat alert"
        fi
      fi
      previous_state=false
    fi
    
    sleep "$CHECK_INTERVAL"
  done
}

# Pre-flight checks
require_container "$PIPER_CONTAINER"
require_container "$SATELLITE_CONTAINER"

log "Enhanced HA health monitoring started"
log "HA URL: $HA_URL"
log "Periodic check interval: ${CHECK_INTERVAL}s"
log "Alert cooldown: ${ALERT_COOLDOWN}s"
log "Monitoring satellite logs for ASR events..."

# Run periodic monitoring in background
monitor_ha_periodic &
periodic_pid=$!

# Run satellite log monitoring in foreground
monitor_satellite_logs &
log_monitor_pid=$!

# Wait for both processes
wait $periodic_pid $log_monitor_pid
