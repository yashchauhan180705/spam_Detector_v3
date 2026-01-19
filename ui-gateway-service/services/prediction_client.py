"""
Prediction Service Client - Handles communication with the Prediction Service.
"""
import requests
from config import PREDICTION_SERVICE_URL


def predict_single(content, model_name, use_llm=False):
    """Get prediction for a single email with optional LLM verification."""
    try:
        payload = {
            'content': content,
            'model_name': model_name,
            'use_llm': use_llm
        }

        # Increase timeout if using LLM (needs more time for API call)
        timeout = 20 if use_llm else 10

        response = requests.post(
            f"{PREDICTION_SERVICE_URL}/predict",
            json=payload,
            timeout=timeout
        )

        if response.status_code == 200:
            return response.json()
        return {'prediction': 'Error', 'error': response.json().get('error', 'Unknown')}
    except requests.Timeout:
        return {'prediction': 'Error', 'error': 'Request timeout'}
    except requests.RequestException as e:
        return {'prediction': 'Error', 'error': str(e)}


def predict_batch(contents, model_name):
    """Get predictions for multiple emails."""
    try:
        payload = {
            'contents': contents,
            'model_name': model_name
        }

        # Increase timeout for large batches: base 60s + 0.5s per email
        timeout = int(max(60, 60 + len(contents) * 0.5))

        response = requests.post(
            f"{PREDICTION_SERVICE_URL}/predict/batch",
            json=payload,
            timeout=timeout
        )

        if response.status_code == 200:
            return response.json()
        return {
            'predictions': ['Error'] * len(contents),
            'error': response.json().get('error', 'Unknown')
        }
    except requests.RequestException as e:
        return {'predictions': ['Error'] * len(contents), 'error': str(e)}


def clear_prediction_cache():
    """Clear the prediction service cache."""
    try:
        response = requests.post(
            f"{PREDICTION_SERVICE_URL}/clear-cache",
            timeout=5
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def check_health():
    """Check prediction service health."""
    try:
        response = requests.get(f"{PREDICTION_SERVICE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

