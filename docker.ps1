# Docker Compose Helper Script for Windows
# Spam Detection System

param(
    [Parameter(Position=0)]
    [ValidateSet('build', 'up', 'down', 'restart', 'logs', 'clean', 'test', 'ps', 'help')]
    [string]$Command = 'help'
)

function Show-Help {
    Write-Host "Spam Detection System - Docker Commands" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  .\docker.ps1 build       - Build all Docker images"
    Write-Host "  .\docker.ps1 up          - Start all services"
    Write-Host "  .\docker.ps1 down        - Stop all services"
    Write-Host "  .\docker.ps1 restart     - Restart all services"
    Write-Host "  .\docker.ps1 logs        - View logs from all services"
    Write-Host "  .\docker.ps1 clean       - Remove all containers, images, and volumes"
    Write-Host "  .\docker.ps1 test        - Test all service endpoints"
    Write-Host "  .\docker.ps1 ps          - Show running containers"
    Write-Host ""
}

function Build-Services {
    Write-Host "Building all services..." -ForegroundColor Green
    docker-compose build
}

function Start-Services {
    Write-Host "Starting all services..." -ForegroundColor Green
    docker-compose up -d
    Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    Write-Host ""
    Write-Host "Services should be ready at:" -ForegroundColor Cyan
    Write-Host "  UI Gateway:         http://localhost:5000" -ForegroundColor White
    Write-Host "  Model Service:      http://localhost:5001" -ForegroundColor White
    Write-Host "  Prediction Service: http://localhost:5002" -ForegroundColor White
    Write-Host ""
    Write-Host "Use '.\docker.ps1 logs' to view service logs" -ForegroundColor Yellow
}

function Stop-Services {
    Write-Host "Stopping all services..." -ForegroundColor Green
    docker-compose down
}

function Restart-Services {
    Write-Host "Restarting all services..." -ForegroundColor Green
    docker-compose restart
}

function Show-Logs {
    Write-Host "Showing logs (press Ctrl+C to exit)..." -ForegroundColor Green
    docker-compose logs -f
}

function Clean-Services {
    Write-Host "Cleaning up all containers, images, and volumes..." -ForegroundColor Red
    $confirmation = Read-Host "Are you sure? This will remove all data (y/N)"
    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        docker-compose down -v
        docker system prune -f
        Write-Host "Cleanup complete!" -ForegroundColor Green
    } else {
        Write-Host "Cleanup cancelled." -ForegroundColor Yellow
    }
}

function Test-Services {
    Write-Host "Testing services..." -ForegroundColor Green
    Write-Host ""

    Write-Host "Testing Model Service..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5001/health" -UseBasicParsing -TimeoutSec 5
        Write-Host "✓ Model Service: $($response.Content)" -ForegroundColor Green
    } catch {
        Write-Host "✗ Model Service: Not responding" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "Testing Prediction Service..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5002/health" -UseBasicParsing -TimeoutSec 5
        Write-Host "✓ Prediction Service: $($response.Content)" -ForegroundColor Green
    } catch {
        Write-Host "✗ Prediction Service: Not responding" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "Testing UI Gateway..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/" -UseBasicParsing -TimeoutSec 5
        Write-Host "✓ UI Gateway: Responding (Status: $($response.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "✗ UI Gateway: Not responding" -ForegroundColor Red
    }
    Write-Host ""
}

function Show-Ps {
    Write-Host "Running containers:" -ForegroundColor Green
    docker-compose ps
}

# Execute command
switch ($Command) {
    'build'   { Build-Services }
    'up'      { Start-Services }
    'down'    { Stop-Services }
    'restart' { Restart-Services }
    'logs'    { Show-Logs }
    'clean'   { Clean-Services }
    'test'    { Test-Services }
    'ps'      { Show-Ps }
    'help'    { Show-Help }
}

