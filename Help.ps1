# PowerShell utility scripts for Windows

function Show-Help {
    Write-Host "Home Assistant + Ollama LLM DevOps Project - Windows Commands" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  .\setup-local.ps1        - Setup local development environment"
    Write-Host "  .\Start-Services.ps1     - Start local services"
    Write-Host "  .\Stop-Services.ps1      - Stop local services"
    Write-Host "  .\Show-Logs.ps1          - View logs from all services"
    Write-Host "  .\Clean-All.ps1          - Clean up Docker volumes and containers"
    Write-Host ""
    Write-Host "Docker Compose commands:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker\docker-compose.yml up -d     - Start services"
    Write-Host "  docker-compose -f docker\docker-compose.yml down      - Stop services"
    Write-Host "  docker-compose -f docker\docker-compose.yml logs -f   - View logs"
    Write-Host "  docker-compose -f docker\docker-compose.yml restart   - Restart services"
    Write-Host ""
    Write-Host "Kubernetes deployment:" -ForegroundColor Yellow
    Write-Host "  (Requires bash/WSL) ./scripts/deploy-k8s.sh dev"
    Write-Host ""
}

Show-Help
