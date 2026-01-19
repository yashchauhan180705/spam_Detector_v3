@echo off
REM Quick Start Script for Spam Detection System
REM This script builds and starts all services using Docker Compose

echo ========================================
echo Spam Detection System - Quick Start
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/3] Building Docker images...
docker-compose build
if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Starting services...
docker-compose up -d
if errorlevel 1 (
    echo ERROR: Failed to start services!
    pause
    exit /b 1
)

echo.
echo [3/3] Waiting for services to initialize...
timeout /t 15 /nobreak >nul

echo.
echo ========================================
echo Services are ready!
echo ========================================
echo.
echo Access the application at:
echo   Web UI:             http://localhost:5000
echo   Model Service:      http://localhost:5001
echo   Prediction Service: http://localhost:5002
echo.
echo To view logs:         docker-compose logs -f
echo To stop services:     docker-compose down
echo.
echo For more commands, see: docker.ps1 or DOCKER_GUIDE.md
echo.
pause

