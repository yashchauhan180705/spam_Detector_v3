"""
UI Gateway Service - Flask-based API Gateway and UI Server.
Acts as the frontend for the Spam Detection microservices architecture.
Auto-starts model and prediction services.
"""
import sys
import io

# Configure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import flask
import subprocess
import time
import atexit
import os
from threading import Thread
from config import SECRET_KEY, DEBUG, HOST, PORT
import requests

# Create Flask app
app = flask.Flask(__name__)
app.secret_key = SECRET_KEY

# Session configuration - ensure sessions persist
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Store service processes
service_processes = []

def start_backend_service(name, directory, port):
    """Start a backend service in a subprocess."""
    try:
        print(f"🚀 Starting {name} on port {port}...")

        # Create log files for debugging
        log_dir = os.path.join(directory, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        stdout_log = os.path.join(log_dir, f'{name.replace(" ", "_").lower()}_stdout.log')
        stderr_log = os.path.join(log_dir, f'{name.replace(" ", "_").lower()}_stderr.log')

        # Start process with log files
        with open(stdout_log, 'w') as out, open(stderr_log, 'w') as err:
            process = subprocess.Popen(
                [sys.executable, 'app.py'],
                cwd=directory,
                stdout=out,
                stderr=err
            )
        service_processes.append(process)

        # Poll the service health endpoint until it responds or timeout
        health_url = f"http://127.0.0.1:{port}/health"
        max_retries = 30  # Increased to 30 seconds

        for attempt in range(max_retries):
            # Check if process crashed
            if process.poll() is not None:
                print(f"❌ {name} process terminated unexpectedly!")
                print(f"   Check logs: {stderr_log}")
                return None

            try:
                resp = requests.get(health_url, timeout=1)
                if resp.status_code == 200:
                    print(f"✅ {name} started and healthy ({health_url})")
                    print(f"   Logs: {stdout_log}")
                    return process
            except requests.exceptions.RequestException:
                # service not ready yet
                if attempt % 5 == 0 and attempt > 0:
                    print(f"   ⏳ Waiting for {name}... ({attempt}/{max_retries}s)")
                time.sleep(1)

        print(f"❌ {name} did not become healthy after {max_retries} seconds")
        print(f"   Check logs: {stdout_log} and {stderr_log}")
        return process
    except Exception as e:
        print(f"❌ Error starting {name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def cleanup_services():
    """Terminate all backend services on shutdown."""
    print("\n🛑 Shutting down backend services...")
    for process in service_processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    print("✅ All services stopped")

# Register cleanup on exit
atexit.register(cleanup_services)

# Start backend services in background
def init_services():
    """Initialize backend services."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Start Model Service
    model_service_dir = os.path.join(base_dir, 'model-service')
    start_backend_service("Model Service", model_service_dir, 5001)

    # Start Prediction Service
    prediction_service_dir = os.path.join(base_dir, 'prediction-service')
    start_backend_service("Prediction Service", prediction_service_dir, 5002)

    print("\n" + "="*70)
    print("✅ All services are ready!")
    print("="*70)
    print(f"\n📱 Access the application at: http://{HOST}:{PORT}")
    print(f"🤖 Model Service API: http://localhost:5001")
    print(f"🔮 Prediction Service API: http://localhost:5002")
    print("="*70 + "\n")

# Start services in a background thread
print("\n" + "="*70)
print("🚀 SPAM DETECTION SYSTEM - UI GATEWAY")
print("="*70)
Thread(target=init_services, daemon=True).start()
time.sleep(4)  # Give services time to start before registering blueprints

# Register blueprints
from blueprints.home import home_bp
from blueprints.models import models_bp
from blueprints.emails import emails_bp

app.register_blueprint(home_bp)
app.register_blueprint(models_bp)
app.register_blueprint(emails_bp)


@app.route('/health')
def health():
    """Health check endpoint."""
    from services import model_client, prediction_client
    return {
        'status': 'healthy',
        'services': {
            'model_service': model_client.check_health(),
            'prediction_service': prediction_client.check_health()
        }
    }


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
