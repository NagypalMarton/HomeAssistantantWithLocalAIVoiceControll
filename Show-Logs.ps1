# Show logs from all services

Write-Host "Showing logs (Ctrl+C to exit)..." -ForegroundColor Cyan
Set-Location docker
docker-compose logs -f
Set-Location ..
