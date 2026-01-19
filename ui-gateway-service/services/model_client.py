"""
Model Service Client - Handles communication with the Model Training Service.
Includes caching for improved performance.
"""
import requests
import time
from config import MODEL_SERVICE_URL, MODEL_CACHE_TTL


class ModelCache:
    """Simple TTL-based cache for model metadata."""

    def __init__(self, ttl=MODEL_CACHE_TTL):
        self.cache = {}
        self.ttl = ttl

    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            del self.cache[key]
        return None

    def set(self, key, value):
        self.cache[key] = (value, time.time())

    def invalidate(self, key=None):
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()


# Global cache instance
_model_cache = ModelCache()


def get_models(force_refresh=False):
    """Fetch all available models from model service."""
    if not force_refresh:
        cached = _model_cache.get('models')
        if cached is not None:
            return cached

    try:
        response = requests.get(f"{MODEL_SERVICE_URL}/models", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            _model_cache.set('models', models)
            return models
        return []
    except requests.RequestException:
        return []


def get_model_metadata(model_name):
    """Get metadata for a specific model."""
    cache_key = f'metadata_{model_name}'
    cached = _model_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        response = requests.get(
            f"{MODEL_SERVICE_URL}/model/{model_name}/metadata",
            timeout=5
        )
        if response.status_code == 200:
            metadata = response.json()
            _model_cache.set(cache_key, metadata)
            return metadata
        return None
    except requests.RequestException:
        return None


def train_model(dataset, text_column, label_column, model_name, timesteps=50000):
    """Send training request to model service."""
    try:
        payload = {
            'dataset': dataset,
            'text_column': text_column,
            'label_column': label_column,
            'model_name': model_name,
            'timesteps': timesteps
        }

        # Dynamic timeout based on timesteps
        # For 50k steps: 600s (10 min)
        # For 500k steps: 3600s (60 min)
        # For 1M steps: 3600s (max 60 min)
        timeout = min(max(600, (timesteps // 100) + 100), 3600)

        response = requests.post(
            f"{MODEL_SERVICE_URL}/train",
            json=payload,
            timeout=timeout
        )

        _model_cache.invalidate()  # Clear cache after training

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get('error', 'Training failed')
    except requests.Timeout:
        return False, f'Training timeout after {timeout}s. Try reducing timesteps or train in smaller batches.'
    except requests.RequestException as e:
        return False, str(e)


def delete_model(model_name):
    """Delete a model from the model service."""
    try:
        response = requests.delete(
            f"{MODEL_SERVICE_URL}/model/{model_name}",
            timeout=10
        )

        _model_cache.invalidate()  # Clear cache after deletion

        if response.status_code == 200:
            return True, response.json().get('message', 'Model deleted')
        else:
            return False, response.json().get('error', 'Delete failed')
    except requests.RequestException as e:
        return False, str(e)


def retrain_model(model_name, feedback_data):
    """Retrain model with feedback data (legacy method)."""
    try:
        payload = {
            'model_name': model_name,
            'feedback_data': feedback_data
        }

        # Dynamic timeout: base 120s + 1s per feedback sample
        timeout = max(120, 120 + len(feedback_data))

        response = requests.post(
            f"{MODEL_SERVICE_URL}/retrain",
            json=payload,
            timeout=timeout
        )

        _model_cache.invalidate()  # Clear cache after retraining

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get('error', 'Retrain failed')
    except requests.Timeout:
        return False, f'Retraining timeout after {timeout}s. The model may still be training in the background.'
    except requests.RequestException as e:
        return False, str(e)


def store_feedback(model_name, feedback_list):
    """
    Store feedback in replay buffer for later RL update.

    Args:
        model_name: Name of the model
        feedback_list: List of dicts with 'content', 'predicted', 'corrected'
    """
    try:
        payload = {
            'model_name': model_name,
            'feedback': feedback_list
        }

        response = requests.post(
            f"{MODEL_SERVICE_URL}/feedback/store",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get('error', 'Failed to store feedback')
    except requests.RequestException as e:
        return False, str(e)


def rl_update(model_name, batch_size=32, use_all=True, clear_after=False):
    """
    Perform DQN-style RL update using stored feedback experiences.

    Args:
        model_name: Name of the model to update
        batch_size: Number of experiences to sample (if not using all)
        use_all: Whether to use all experiences or sample
        clear_after: Whether to clear buffer after update
    """
    try:
        payload = {
            'model_name': model_name,
            'batch_size': batch_size,
            'use_all': use_all,
            'clear_after': clear_after
        }

        # RL updates can take time
        timeout = 180

        response = requests.post(
            f"{MODEL_SERVICE_URL}/rl-update",
            json=payload,
            timeout=timeout
        )

        _model_cache.invalidate()  # Clear cache after update

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get('error', 'RL update failed')
    except requests.Timeout:
        return False, 'RL update timeout. The model may still be updating in the background.'
    except requests.RequestException as e:
        return False, str(e)


def get_buffer_status(model_name=None):
    """Get the current status of the feedback replay buffer."""
    try:
        params = {'model_name': model_name} if model_name else {}

        response = requests.get(
            f"{MODEL_SERVICE_URL}/feedback/buffer",
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


def clear_feedback_buffer(model_name=None):
    """Clear the feedback replay buffer."""
    try:
        payload = {'model_name': model_name} if model_name else {}

        response = requests.post(
            f"{MODEL_SERVICE_URL}/feedback/clear",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            return True, response.json().get('message', 'Buffer cleared')
        return False, response.json().get('error', 'Failed to clear buffer')
    except requests.RequestException as e:
        return False, str(e)


def check_health():
    """Check model service health."""
    try:
        response = requests.get(f"{MODEL_SERVICE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def invalidate_cache():
    """Invalidate the model cache."""
    _model_cache.invalidate()

