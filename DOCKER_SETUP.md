# Docker Setup Guide for Spam Detection System

This guide explains how to build and run the spam detection microservices using Docker.

## System Architecture

The system consists of 3 microservices:

1. **Model Service** (Port 5001) - Handles model training and management
2. **Prediction Service** (Port 5002) - Handles email spam predictions
3. **UI Gateway Service** (Port 5000) - Web interface for users

All services share a common volume for trained models.

## Prerequisites

- Docker Desktop installed and running
- At least 4GB of available RAM
- At least 10GB of free disk space

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Option 2: Using PowerShell Script

```powershell
# Run the automated setup script
.\docker.ps1
```

## Build Process

The build process will:

1. Create Python 3.11 slim containers for each service
2. Install system dependencies (gcc, g++)
3. Install Python packages from requirements.txt
4. Copy application code
5. Configure environment variables
6. Set up health checks

**Note**: The first build will take 10-20 minutes as it downloads and installs:
- PyTorch (~800MB)
- Stable-Baselines3 and dependencies
- TensorFlow (optional, for some features)
- All other Python packages

## Service Details

### Model Service

**Purpose**: Train and manage spam detection models using DQN reinforcement learning

**Endpoints**:
- `POST /train` - Train a new model
- `GET /models` - List all trained models
- `GET /model/<name>/metadata` - Get model details
- `DELETE /model/<name>` - Delete a model
- `POST /retrain` - Retrain with feedback data
- `GET /health` - Health check

**Environment Variables**:
- `MODEL_DIR=/shared/models` - Shared model storage
- `PYTHONUNBUFFERED=1` - Real-time logging

### Prediction Service

**Purpose**: Load models and perform spam predictions

**Endpoints**:
- `POST /predict` - Predict if an email is spam
- `POST /predict_batch` - Predict multiple emails
- `POST /feedback` - Submit feedback for model improvement
- `GET /feedback/pending` - Get pending feedback
- `POST /feedback/clear` - Clear feedback buffer
- `GET /health` - Health check

**Environment Variables**:
- `MODEL_DIR=/shared/models` - Shared model storage
- `MODEL_SERVICE_URL=http://model-service:5001` - Model service URL
- `GEMINI_API_KEY` - Optional: For LLM-based verification
- `PYTHONUNBUFFERED=1` - Real-time logging

### UI Gateway Service

**Purpose**: Web interface for users to interact with the system

**Endpoints**:
- `GET /` - Home page
- `GET /emails` - Email management interface
- `GET /models` - Model management interface
- Various API proxies to backend services

**Environment Variables**:
- `MODEL_SERVICE_URL=http://model-service:5001` - Model service URL
- `PREDICTION_SERVICE_URL=http://prediction-service:5002` - Prediction service URL
- `SECRET_KEY` - Flask session secret
- `DEBUG=False` - Production mode
- `HOST=0.0.0.0` - Listen on all interfaces
- `PORT=5000` - Service port
- `PYTHONUNBUFFERED=1` - Real-time logging

## Accessing the Services

Once the services are running:

- **Web UI**: http://localhost:5000
- **Model Service API**: http://localhost:5001
- **Prediction Service API**: http://localhost:5002

## Troubleshooting

### Build Failures

If the build fails with "exit code 2" during `pip install`:

1. Check that requirements.txt files exist in each service directory
2. Ensure you have internet connectivity
3. Try building with more memory: `docker-compose build --memory=4g`
4. Check Docker logs: `docker-compose logs`

### Connection Refused Errors

If you get "Connection refused" errors:

1. Check if services are running: `docker-compose ps`
2. Check health status: `docker-compose ps`
3. View service logs: `docker-compose logs model-service`
4. Ensure Docker network is created: `docker network ls`

### Port Conflicts

If ports are already in use:

1. Stop existing services: `docker-compose down`
2. Find processes using ports: 
   ```powershell
   Get-NetTCPConnection -LocalPort 5000,5001,5002
   ```
3. Kill the processes or change ports in docker-compose.yml

### Slow Performance

If services are slow:

1. Increase Docker Desktop memory allocation (Settings > Resources)
2. Use SSD for Docker storage
3. Reduce model complexity or training timesteps

## Shared Volume

The `./models` directory on the host is mounted to `/shared/models` in all containers. This allows:

- Models trained in model-service to be accessible in prediction-service
- Persistence of models across container restarts
- Easy backup by copying the models directory

## Health Checks

All services have health checks configured:

- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start Period**: 40 seconds

Check health status:
```bash
docker-compose ps
```

## Logs

View logs for debugging:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f model-service

# Last 100 lines
docker-compose logs --tail=100
```

Logs are also saved to:
- `./model-service/logs/`
- `./prediction-service/logs/`

## Stopping and Cleaning Up

```bash
# Stop services but keep data
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers, and remove volumes
docker-compose down -v

# Remove all images as well
docker-compose down --rmi all
```

## Production Deployment

For production:

1. Change `SECRET_KEY` in ui-gateway-service
2. Set `DEBUG=False`
3. Configure proper SSL/TLS
4. Use a reverse proxy (nginx, traefik)
5. Set up proper logging and monitoring
6. Use Docker secrets for sensitive data
7. Configure resource limits in docker-compose.yml

## Development Mode

For development with hot-reload:

1. Mount source code as volumes
2. Set `DEBUG=True`
3. Install watchdog for auto-reload

Example:
```yaml
model-service:
  volumes:
    - ./model-service:/app
  environment:
    - FLASK_DEBUG=1
```

## Backup and Restore

### Backup Models
```bash
# Create backup
tar -czf models-backup-$(date +%Y%m%d).tar.gz ./models/

# Or use PowerShell
Compress-Archive -Path .\models\* -DestinationPath "models-backup-$(Get-Date -Format 'yyyyMMdd').zip"
```

### Restore Models
```bash
# Extract backup
tar -xzf models-backup-20260119.tar.gz

# Or use PowerShell
Expand-Archive -Path "models-backup-20260119.zip" -DestinationPath .\models\
```

## Network Architecture

All services are connected via a custom bridge network (`spam-detection-network`), which allows:

- Service-to-service communication using service names
- Isolation from other Docker containers
- Custom DNS resolution

## Resource Requirements

Recommended resources:

- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 10GB for images and models
- **Network**: Stable internet for downloading dependencies

## Support

For issues or questions:

1. Check logs: `docker-compose logs`
2. Verify services are healthy: `docker-compose ps`
3. Rebuild from scratch: `docker-compose down -v && docker-compose build --no-cache`
4. Review this documentation
5. Check Docker Desktop status

## Version Information

- Docker Compose: 2.x+
- Python: 3.11
- Flask: 3.0.0
- Stable-Baselines3: 2.2.1
- PyTorch: 2.1.2
- Scikit-learn: 1.3.2

