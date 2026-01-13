#!/bin/bash
# Health check script for Edge services on ARM64

set -e

echo "=== Edge Services Health Check ==="
echo ""

# Wait for services to initialize
echo "Waiting for services to start..."
sleep 10

# Check if containers are running
echo "1. Checking container status..."
for service in config wakeword stt piper orchestrator; do
    if docker compose ps | grep -q "$service.*Up"; then
        echo "✓ $service is running"
    else
        echo "✗ $service is not running"
        docker compose logs "$service" --tail 20
        exit 1
    fi
done

echo ""
echo "2. Checking service ports..."

# Check TCP ports
check_port() {
    local service=$1
    local port=$2
    
    if docker compose exec -T "$service" timeout 2 nc -zv localhost "$port" 2>&1 | grep -q "succeeded\|open"; then
        echo "✓ $service responding on port $port"
        return 0
    else
        echo "✗ $service not responding on port $port"
        return 1
    fi
}

# Wyoming protocol ports
check_port "wakeword" "10400" || exit 1
check_port "stt" "10300" || exit 1
check_port "piper" "10200" || exit 1

# Config service HTTP
if docker compose exec -T config timeout 5 wget -q -O - http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ config responding on HTTP port 8000"
else
    echo "✗ config not responding on HTTP port 8000"
    exit 1
fi

echo ""
echo "3. Checking inter-service network connectivity..."

# Check if orchestrator can reach other services
for target_service in wakeword:10400 stt:10300 piper:10200; do
    service_name=$(echo $target_service | cut -d: -f1)
    service_port=$(echo $target_service | cut -d: -f2)
    
    if docker compose exec -T orchestrator timeout 3 nc -zv "$service_name" "$service_port" 2>&1 | grep -q "succeeded\|open"; then
        echo "✓ orchestrator → $target_service connection OK"
    else
        echo "✗ orchestrator → $target_service connection FAILED"
        exit 1
    fi
done

echo ""
echo "4. Checking volumes..."
docker compose exec -T orchestrator test -d /app/config && echo "✓ config_data volume mounted" || echo "✗ config_data volume missing"
docker compose exec -T stt test -d /data && echo "✓ whisper_data volume mounted" || echo "✗ whisper_data volume missing"

echo ""
echo "5. Memory usage check..."
total_mem=$(docker stats --no-stream --format "{{.MemUsage}}" | awk '{sum+=$1} END {print sum}')
echo "Total memory usage: ${total_mem}MB"

if [ "$total_mem" -gt 1800 ]; then
    echo "⚠ Memory usage high - may not work on 2GB Raspberry Pi"
else
    echo "✓ Memory usage acceptable for 2GB device"
fi

echo ""
echo "=== All Health Checks Passed ==="
