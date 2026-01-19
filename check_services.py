"""
Service Health Check Utility
Verifies all microservices are running and healthy before training.
"""
import requests
import sys

SERVICES = {
    'Model Service': 'http://localhost:5001/health',
    'Prediction Service': 'http://localhost:5002/health',
    'UI Gateway': 'http://localhost:5000/health'
}

def check_service(name, url, timeout=2):
    """Check if a service is responding to health checks."""
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            print(f"✅ {name}: HEALTHY ({url})")
            return True
        else:
            print(f"⚠️  {name}: HTTP {resp.status_code} ({url})")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: NOT RUNNING - Connection refused ({url})")
        return False
    except requests.exceptions.Timeout:
        print(f"⏱️  {name}: TIMEOUT ({url})")
        return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False

def main():
    """Check all services and report status."""
    print("=" * 70)
    print("🔍 CHECKING SERVICE HEALTH")
    print("=" * 70)
    print()

    all_healthy = True
    results = {}

    for service_name, service_url in SERVICES.items():
        results[service_name] = check_service(service_name, service_url)
        all_healthy = all_healthy and results[service_name]

    print()
    print("=" * 70)

    if all_healthy:
        print("✅ ALL SERVICES ARE HEALTHY - Ready to train models!")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME SERVICES ARE NOT HEALTHY")
        print("=" * 70)
        print("\n📋 TROUBLESHOOTING STEPS:")
        print()

        if not results.get('UI Gateway', False):
            print("1. Start the UI Gateway:")
            print("   cd ui-gateway-service")
            print("   python app.py")
            print()

        if not results.get('Model Service', False):
            print("2. Model Service is required for training. The UI Gateway should")
            print("   auto-start it. If not, start manually:")
            print("   cd model-service")
            print("   python app.py")
            print()

        if not results.get('Prediction Service', False):
            print("3. Prediction Service is required for predictions. Start it with:")
            print("   cd prediction-service")
            print("   python app.py")
            print()

        print("4. Check service logs in:")
        print("   - model-service/logs/")
        print("   - prediction-service/logs/")
        print()

        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

