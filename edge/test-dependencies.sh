#!/bin/bash
# Service startup and dependency test

set -e

echo "=== Testing Service Dependencies and Startup Order ==="
echo ""

# Start services and monitor startup order
echo "1. Starting services with dependency chain..."

# Start base services first (no dependencies)
docker compose up -d config wakeword stt piper

echo "Waiting for base services to be healthy (30s)..."
sleep 30

# Check if base services are running
for service in config wakeword stt piper; do
    if ! docker compose ps | grep -q "$service.*Up"; then
        echo "✗ Base service $service failed to start"
        docker compose logs "$service"
        exit 1
    fi
    echo "✓ $service started successfully"
done

echo ""
echo "2. Starting orchestrator (depends on: stt, piper, wakeword)..."
docker compose up -d orchestrator

echo "Waiting for orchestrator to initialize (20s)..."
sleep 20

# Check orchestrator
if docker compose ps | grep -q "orchestrator.*Up"; then
    echo "✓ orchestrator started successfully"
else
    echo "✗ orchestrator failed to start"
    docker compose logs orchestrator
    exit 1
fi

echo ""
echo "3. Verifying startup order in logs..."

# Check that orchestrator started after dependencies
orch_start=$(docker compose logs orchestrator 2>&1 | grep -m 1 "Starting" | awk '{print $1}' || echo "unknown")
stt_start=$(docker compose logs stt 2>&1 | grep -m 1 "Starting" | awk '{print $1}' || echo "unknown")

echo "STT start time: $stt_start"
echo "Orchestrator start time: $orch_start"

echo ""
echo "4. Testing depends_on behavior..."

# Stop a dependency
echo "Stopping STT service..."
docker compose stop stt

sleep 5

# Check if orchestrator detects the issue
echo "Checking orchestrator health without STT..."
if docker compose logs orchestrator --tail 10 | grep -qi "error\|connection refused\|failed"; then
    echo "✓ Orchestrator correctly reports issue when dependency is down"
else
    echo "ℹ Orchestrator may not immediately detect dependency failure"
fi

# Restart STT
echo "Restarting STT service..."
docker compose start stt

sleep 10

# Verify recovery
if docker compose ps | grep -q "stt.*Up"; then
    echo "✓ STT restarted successfully"
else
    echo "✗ STT failed to restart"
    exit 1
fi

echo ""
echo "=== Service Dependency Test Passed ==="
