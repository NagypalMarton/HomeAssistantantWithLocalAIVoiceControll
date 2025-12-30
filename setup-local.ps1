# Setup script for local development environment (Windows)

Write-Host "=== Home Assistant + Ollama Local Setup (Windows) ===" -ForegroundColor Cyan

# Check prerequisites
Write-Host "`nChecking prerequisites..." -ForegroundColor Yellow

# Check Docker
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "✓ Docker is installed" -ForegroundColor Green
    docker --version
} else {
    Write-Host "✗ Docker is not installed" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check Docker Compose
if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    Write-Host "✓ Docker Compose is installed" -ForegroundColor Green
} else {
    Write-Host "✗ Docker Compose is not installed" -ForegroundColor Red
    exit 1
}

# Check for NVIDIA GPU (optional for dev)
try {
    $nvidiaCheck = nvidia-smi 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ NVIDIA GPU detected" -ForegroundColor Green
        $GPU_AVAILABLE = $true
    } else {
        throw
    }
} catch {
    Write-Host "⚠ No NVIDIA GPU detected - Ollama will run on CPU" -ForegroundColor Yellow
    $GPU_AVAILABLE = $false
}

# Create necessary directories
Write-Host "`nCreating directories..." -ForegroundColor Yellow
$directories = @(
    "docker\home-assistant\config",
    "monitoring\zabbix\scripts",
    "monitoring\zabbix\templates"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Gray
    }
}

# Start services
Write-Host "`nStarting services with Docker Compose..." -ForegroundColor Yellow
Set-Location docker

if ($GPU_AVAILABLE) {
    docker-compose up -d
} else {
    Write-Host "Starting without GPU support..." -ForegroundColor Yellow
    docker-compose up -d --scale ollama=0
    Write-Host "Note: Ollama service is disabled. Enable GPU or use CPU-only version." -ForegroundColor Yellow
}

# Wait for services
Write-Host "`nWaiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host "`nChecking service health..." -ForegroundColor Yellow

$services = @{
    "homeassistant" = @{
        "name" = "Home Assistant"
        "url" = "http://localhost:8123"
    }
    "zabbix-web" = @{
        "name" = "Zabbix"
        "url" = "http://localhost:8080"
        "credentials" = "Admin/zabbix"
    }
    "ollama" = @{
        "name" = "Ollama"
        "url" = "http://localhost:11434"
    }
}

foreach ($container in $services.Keys) {
    $runningContainers = docker ps --format "{{.Names}}"
    if ($runningContainers -match $container) {
        $service = $services[$container]
        Write-Host "✓ $($service.name) is running" -ForegroundColor Green
        Write-Host "  Access at: $($service.url)" -ForegroundColor Gray
        if ($service.credentials) {
            Write-Host "  Credentials: $($service.credentials)" -ForegroundColor Gray
        }
    } else {
        Write-Host "✗ $($services[$container].name) failed to start" -ForegroundColor Red
    }
}

# Pull Ollama models if Ollama is running
if ($GPU_AVAILABLE -and (docker ps --format "{{.Names}}" | Select-String "ollama")) {
    Write-Host "`nPulling Ollama models..." -ForegroundColor Yellow
    
    Set-Location ..
    $modelsFile = "config\ollama\models.txt"
    if (Test-Path $modelsFile) {
        Get-Content $modelsFile | Where-Object { $_.Trim() -ne "" } | ForEach-Object {
            Write-Host "Pulling $_..." -ForegroundColor Gray
            docker exec ollama ollama pull $_
        }
    }
} else {
    Write-Host "`n⚠ Ollama is not running - skipping model download" -ForegroundColor Yellow
}

Set-Location ..

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "`nServices:" -ForegroundColor Yellow
Write-Host "  - Home Assistant: http://localhost:8123"
Write-Host "  - Zabbix: http://localhost:8080 (Admin/zabbix)"
if ($GPU_AVAILABLE) {
    Write-Host "  - Ollama API: http://localhost:11434"
}
Write-Host "`nUseful commands:" -ForegroundColor Yellow
Write-Host "  - Stop services: docker-compose -f docker\docker-compose.yml down"
Write-Host "  - View logs: docker-compose -f docker\docker-compose.yml logs -f"
Write-Host "  - Restart: docker-compose -f docker\docker-compose.yml restart"
Write-Host ""
