# Stop local services

Write-Host "Stopping services..." -ForegroundColor Cyan
Set-Location docker
docker-compose down
Set-Location ..
Write-Host "Services stopped!" -ForegroundColor Green
