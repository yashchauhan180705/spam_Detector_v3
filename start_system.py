"""
Quick Start Script for Spam Detection System
Starts UI Gateway which auto-starts Model and Prediction services.
Waits for all services to become healthy before opening browser.
"""
import subprocess
import sys
import time
import requests
import webbrowser
import os

def check_service_health(url, max_retries=30, name="Service"):
    """Wait for a service to become healthy."""
    print(f"⏳ Waiting for {name} to start...")
    for i in range(max_retries):
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                print(f"✅ {name} is healthy!")
                return True
        except:
            if i % 5 == 0 and i > 0:
                print(f"   Still waiting... ({i}/{max_retries}s)")
            time.sleep(1)

    print(f"❌ {name} failed to start after {max_retries} seconds")
    return False

def main():
    """Start all services and wait for them to be ready."""
    print("=" * 70)
    print("🚀 SPAM DETECTION SYSTEM - QUICK START")
    print("=" * 70)
    print()

    # Change to ui-gateway-service directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ui_gateway_dir = os.path.join(base_dir, 'ui-gateway-service')

    if not os.path.exists(ui_gateway_dir):
        print(f"❌ Cannot find ui-gateway-service directory at: {ui_gateway_dir}")
        return 1

    print("Starting UI Gateway (this will auto-start backend services)...")
    print()

    # Start UI Gateway
    process = None
    try:
        process = subprocess.Popen(
            [sys.executable, 'app.py'],
            cwd=ui_gateway_dir
        )

        print("⏳ Waiting for services to start (this may take 30-60 seconds)...")
        print()

        # Wait for UI Gateway
        if not check_service_health('http://localhost:5000/health', max_retries=40, name="UI Gateway"):
            print("\n❌ Failed to start services. Check the output above for errors.")
            print("\nYou can also check logs in:")
            print("  - model-service/logs/")
            print("  - prediction-service/logs/")
            process.terminate()
            return 1

        # Check Model Service
        if not check_service_health('http://localhost:5001/health', max_retries=5, name="Model Service"):
            print("\n⚠️  Model Service is not healthy. Training may not work.")
            print("   Check: model-service/logs/model_service_stderr.log")

        # Check Prediction Service
        if not check_service_health('http://localhost:5002/health', max_retries=5, name="Prediction Service"):
            print("\n⚠️  Prediction Service is not healthy. Predictions may not work.")
            print("   Check: prediction-service/logs/prediction_service_stderr.log")

        print()
        print("=" * 70)
        print("✅ SYSTEM READY!")
        print("=" * 70)
        print()
        print("📱 Application URL: http://localhost:5000")
        print("🤖 Model Service API: http://localhost:5001")
        print("🔮 Prediction Service API: http://localhost:5002")
        print()
        print("Press Ctrl+C to stop all services")
        print("=" * 70)
        print()

        # Open browser
        try:
            webbrowser.open('http://localhost:5000')
        except:
            pass

        # Keep running
        process.wait()

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        if process:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        print("✅ All services stopped")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

