# Start local services

Write-Host "Starting services..." -ForegroundColor Cyan
Set-Location docker
docker-compose up -d
Set-Location ..
Write-Host "Services started!" -ForegroundColor Green
Write-Host "Access at:" -ForegroundColor Yellow
Write-Host "  - Home Assistant: http://localhost:8123"
Write-Host "  - Zabbix: http://localhost:8080"
Write-Host "  - Ollama: http://localhost:11434"
