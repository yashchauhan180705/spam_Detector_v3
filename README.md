# Spam Detection System - Docker Setup

[![CI Pipeline](https://github.com/yashchauhan180705/spam_Detector_v3/actions/workflows/ci.yml/badge.svg)](https://github.com/yashchauhan180705/spam_Detector_v3/actions/workflows/ci.yml)
[![Docker Publish](https://github.com/yashchauhan180705/spam_Detector_v3/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/yashchauhan180705/spam_Detector_v3/actions/workflows/docker-publish.yml)
[![Code Quality](https://github.com/yashchauhan180705/spam_Detector_v3/actions/workflows/code-quality.yml/badge.svg)](https://github.com/yashchauhan180705/spam_Detector_v3/actions/workflows/code-quality.yml)

A microservices-based spam email detection system using reinforcement learning, fully containerized with Docker.

## 🏗️ Architecture

The system consists of three microservices:

1. **Model Service** (Port 5001) - Handles ML model training and management
2. **Prediction Service** (Port 5002) - Performs spam/ham predictions
3. **UI Gateway Service** (Port 5000) - Web interface and API gateway

## 🚀 Quick Start with Docker

### Prerequisites
- Docker Desktop installed and running
- Docker Compose V2+

### Starting the System

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### Accessing the Application

Once all services are running:
- **Web UI**: http://localhost:5000
- **Model Service API**: http://localhost:5001
- **Prediction Service API**: http://localhost:5002

### Stopping the System

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears all data)
docker-compose down -v
```

## 📝 Service Details

### Model Service
- **Purpose**: Train and manage spam detection models using DQN (Deep Q-Network)
- **Endpoints**:
  - `GET /health` - Health check
  - `POST /train` - Train a new model
  - `POST /retrain` - Retrain with feedback data
  - `GET /models` - List all models
  - `GET /model/<name>/metadata` - Get model metadata
  - `DELETE /model/<name>` - Delete a model

### Prediction Service
- **Purpose**: Predict spam/ham for emails
- **Endpoints**:
  - `GET /health` - Health check
  - `POST /predict` - Predict single email
  - `POST /predict/batch` - Predict multiple emails
  - `POST /feedback` - Submit prediction feedback
  - `GET /feedback/stats` - Get feedback statistics

### UI Gateway Service
- **Purpose**: Web interface and orchestration
- **Features**:
  - Email classification interface
  - Model training interface
  - Model fine-tuning with feedback
  - Excel file upload support

## 🔧 Configuration

### Environment Variables

You can customize the services by modifying the `docker-compose.yml` file or creating a `.env` file:

```env
# Model Service
MODEL_DIR=/shared/models

# Prediction Service
MODEL_SERVICE_URL=http://model-service:5001

# UI Gateway
SECRET_KEY=your-secret-key-here
DEBUG=False
```

## 📦 Data Persistence

Models are stored in a shared volume mapped to `./models` on your host machine. This ensures:
- Models persist across container restarts
- Models are shared between services
- Easy backup and version control

## 🛠️ Development

### Building Individual Services

```bash
# Build only model service
docker-compose build model-service

# Build only prediction service
docker-compose build prediction-service

# Build only UI gateway
docker-compose build ui-gateway-service
```

### Viewing Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs model-service
docker-compose logs prediction-service
docker-compose logs ui-gateway-service

# Follow logs in real-time
docker-compose logs -f
```

### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart model-service
```

## 🧪 Testing

### Health Checks

```bash
# Check model service
curl http://localhost:5001/health

# Check prediction service
curl http://localhost:5002/health

# Check UI gateway
curl http://localhost:5000/
```

### Training a Model

1. Navigate to http://localhost:5000
2. Go to "Model Training"
3. Upload the `enron_spam_data.csv` file
4. Configure training parameters
5. Click "Train Model"

## 📊 Monitoring

All services include health checks that run every 30 seconds. You can check service status:

```bash
docker-compose ps
```

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs for errors
docker-compose logs

# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

### Port conflicts
If ports 5000, 5001, or 5002 are already in use, modify the port mappings in `docker-compose.yml`:

```yaml
ports:
  - "5010:5000"  # Map to different host port
```

### Out of disk space
```bash
# Clean up unused Docker resources
docker system prune -a

# Remove old volumes
docker volume prune
```

## 📚 Tech Stack

- **Framework**: Flask
- **ML Libraries**: scikit-learn, stable-baselines3, gymnasium
- **Data Processing**: pandas, numpy
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Python**: 3.11

## 🔄 CI/CD

This project includes comprehensive CI/CD pipelines using GitHub Actions:

- **Continuous Integration**: Automated testing, linting, and Docker builds on every push/PR
- **Docker Publishing**: Automatic image builds and publishing to GitHub Container Registry
- **Code Quality**: Security scanning, dependency checks, and code quality analysis
- **Deployment**: Template for automated deployments (requires configuration)

For detailed information, see [CI/CD Documentation](CI_CD.md).

### Quick CI/CD Commands

```bash
# Run linting locally
pip install flake8
flake8 .

# Test Docker builds locally
docker-compose build
docker-compose up
```

## 🔐 Security Notes

- Change the `SECRET_KEY` in production
- Consider adding authentication for API endpoints
- Use environment variables for sensitive data
- Run services as non-root user in production

## 📄 License

This project is for educational purposes.

