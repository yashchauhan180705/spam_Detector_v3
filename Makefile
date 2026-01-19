.PHONY: help build up down restart logs clean test

help:
	@echo "Spam Detection System - Docker Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make build       - Build all Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make clean       - Remove all containers, images, and volumes"
	@echo "  make test        - Test all service endpoints"
	@echo "  make ps          - Show running containers"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services starting... waiting 10 seconds"
	@timeout /t 10 /nobreak > nul
	@echo "Services should be ready at:"
	@echo "  UI Gateway:         http://localhost:5000"
	@echo "  Model Service:      http://localhost:5001"
	@echo "  Prediction Service: http://localhost:5002"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

test:
	@echo "Testing Model Service..."
	@curl -s http://localhost:5001/health || echo "Model Service not responding"
	@echo ""
	@echo "Testing Prediction Service..."
	@curl -s http://localhost:5002/health || echo "Prediction Service not responding"
	@echo ""
	@echo "Testing UI Gateway..."
	@curl -s http://localhost:5000/ > nul || echo "UI Gateway not responding"

ps:
	docker-compose ps

