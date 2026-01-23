#!/bin/bash
set -e

echo "🚀 Starting Central Backend..."
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 .env file not found. Running initialization..."
    docker-compose --profile setup run --rm init
    echo ""
fi

# Start all services
echo "🐳 Starting Docker Compose services..."
docker-compose up -d

echo ""
echo "✅ Services started!"
echo ""
echo "📊 Checking service status..."
docker-compose ps

echo ""
echo "🔍 Waiting for services to be healthy..."
sleep 5

# Check health endpoints
echo ""
echo "Health checks:"
echo "- User API: curl http://localhost:8000/api/v1/health"
echo "- HA Manager: curl http://localhost:8001/api/v1/health"
echo "- Ollama: curl http://localhost:11434/api/tags"

echo ""
echo "⚠️  Don't forget to pull the Ollama model:"
echo "   docker exec central-ollama ollama pull ministral-3:3b-instruct-2512-q4_K_M"
echo ""
