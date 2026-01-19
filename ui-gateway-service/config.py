"""
Configuration settings for UI Gateway Service.
Uses environment variables for Docker/production readiness.
"""
import os
# Service URLs - configurable via environment variables
MODEL_SERVICE_URL = os.getenv('MODEL_SERVICE_URL', 'http://localhost:5001')
PREDICTION_SERVICE_URL = os.getenv('PREDICTION_SERVICE_URL', 'http://localhost:5002')

# Application settings
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
# Cache settings
MODEL_CACHE_TTL = int(os.getenv('MODEL_CACHE_TTL', '60'))  # seconds
# Server settings
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
