# Central Backend Startup Script for Windows
Write-Host "🚀 Starting Central Backend..." -ForegroundColor Green
Write-Host ""

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "📝 .env file not found. Running initialization..." -ForegroundColor Yellow
    docker-compose --profile setup run --rm init
    Write-Host ""
}

# Start all services
Write-Host "🐳 Starting Docker Compose services..." -ForegroundColor Green
docker-compose up -d

Write-Host ""
Write-Host "✅ Services started!" -ForegroundColor Green
Write-Host ""

Write-Host "📊 Checking service status..." -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "🔍 Waiting for services to be healthy..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Check health endpoints
Write-Host ""
Write-Host "Health checks:" -ForegroundColor Yellow
Write-Host "- User API: curl http://localhost:8000/api/v1/health"
Write-Host "- HA Manager: curl http://localhost:8001/api/v1/health"
Write-Host "- Ollama: curl http://localhost:11434/api/tags"

Write-Host ""
Write-Host "⚠️  Don't forget to pull the Ollama model:" -ForegroundColor Yellow
Write-Host "   docker exec central-ollama ollama pull ministral-3:3b-instruct-2512-q4_K_M" -ForegroundColor White
Write-Host ""
