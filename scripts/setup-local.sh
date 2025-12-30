#!/bin/bash
# Setup script for local development environment

set -e

echo "=== Home Assistant + Ollama Local Setup ==="

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Check for NVIDIA GPU (optional for dev)
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA GPU detected"
    GPU_AVAILABLE=true
else
    echo "⚠ No NVIDIA GPU detected - Ollama will run on CPU"
    GPU_AVAILABLE=false
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p docker/home-assistant/config
mkdir -p monitoring/zabbix/scripts
mkdir -p monitoring/zabbix/templates

# Make scripts executable
echo "Setting script permissions..."
chmod +x monitoring/zabbix/scripts/*.sh
chmod +x scripts/*.sh

# Start services
echo "Starting services with Docker Compose..."
cd docker

if [ "$GPU_AVAILABLE" = true ]; then
    docker-compose up -d
else
    echo "Starting without GPU support..."
    docker-compose up -d --scale ollama=0
    echo "Note: Ollama service is disabled. Enable GPU or use CPU-only version."
fi

# Wait for services
echo "Waiting for services to start..."
sleep 10

# Check service health
echo "Checking service health..."

if docker ps | grep -q homeassistant; then
    echo "✓ Home Assistant is running"
    echo "  Access at: http://localhost:8123"
else
    echo "✗ Home Assistant failed to start"
fi

if docker ps | grep -q zabbix-web; then
    echo "✓ Zabbix is running"
    echo "  Access at: http://localhost:8080"
    echo "  Default credentials: Admin/zabbix"
else
    echo "✗ Zabbix failed to start"
fi

if docker ps | grep -q ollama; then
    echo "✓ Ollama is running"
    echo "  API at: http://localhost:11434"
    
    # Pull default models
    echo "Pulling Ollama models..."
    while IFS= read -r model; do
        if [ -n "$model" ]; then
            echo "Pulling $model..."
            docker exec ollama ollama pull "$model"
        fi
    done < ../config/ollama/models.txt
else
    echo "⚠ Ollama is not running"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Services:"
echo "  - Home Assistant: http://localhost:8123"
echo "  - Zabbix: http://localhost:8080 (Admin/zabbix)"
echo "  - Ollama API: http://localhost:11434"
echo ""
echo "To stop services: docker-compose down"
echo "To view logs: docker-compose logs -f"
