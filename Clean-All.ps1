# Clean up Docker volumes and containers

Write-Host "Cleaning up Docker resources..." -ForegroundColor Cyan

$response = Read-Host "This will remove all containers and volumes. Continue? (y/N)"
if ($response -ne 'y' -and $response -ne 'Y') {
    Write-Host "Cancelled" -ForegroundColor Yellow
    exit
}

Set-Location docker
docker-compose down -v
Set-Location ..

docker system prune -f

Write-Host "Cleanup complete!" -ForegroundColor Green
