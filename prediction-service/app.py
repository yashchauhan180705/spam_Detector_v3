import os
import sys
import io

# Configure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import joblib
import numpy as np
from flask import Flask, request, jsonify
from stable_baselines3 import DQN
import re
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Use shared models directory - can be overridden via environment variable
MODEL_DIR = os.getenv('MODEL_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models'))

# Cache loaded models
loaded_models = {}

# LLM API configuration - only Gemini for quick verification
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
LLM_ENABLED = bool(GEMINI_API_KEY)

# Simple spam detection prompt for quick verification
QUICK_SPAM_PROMPT = """Is this email SPAM or HAM (legitimate)? Respond with ONLY one word: SPAM or HAM

Email:
{email_content}

Answer (one word only):"""


def clean_text(text):
    """Clean email text for better processing"""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = ' '.join(text.split())
    return text


def quick_llm_verify(email_content):
    """Quick LLM verification using Gemini (10 second timeout)"""
    if not LLM_ENABLED:
        return None

    try:
        # Truncate very long emails to 500 chars for faster processing
        if len(email_content) > 500:
            email_content = email_content[:500] + "..."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "parts": [{
                    "text": QUICK_SPAM_PROMPT.format(email_content=email_content)
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 10  # Very short response
            }
        }

        # Increased timeout to 10 seconds
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text'].strip().upper()

            # Parse response
            if 'SPAM' in text:
                return 'Spam'
            elif 'HAM' in text:
                return 'Ham'

        return None

    except requests.Timeout:
        print(f"LLM verification timeout after 10 seconds")
        return None
    except Exception as e:
        print(f"LLM verification error: {type(e).__name__}: {e}")
        return None


def load_model(model_name):
    """Load model if not already cached"""
    if model_name in loaded_models:
        return loaded_models[model_name]
    
    try:
        model_path = os.path.join(MODEL_DIR, f"{model_name}.zip")
        vectorizer_path = os.path.join(MODEL_DIR, f"{model_name}_vectorizer.pkl")
        scaler_path = os.path.join(MODEL_DIR, f"{model_name}_scaler.pkl")

        if not all(os.path.exists(p) for p in [model_path, vectorizer_path, scaler_path]):
            return None

        model = DQN.load(model_path)
        vectorizer = joblib.load(vectorizer_path)
        scaler = joblib.load(scaler_path)

        loaded_models[model_name] = {
            'model': model,
            'vectorizer': vectorizer,
            'scaler': scaler
        }

        return loaded_models[model_name]
    except Exception as e:
        print(f"Error loading model: {e}")
        return None


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        content = data.get('content', '')
        model_name = data.get('model_name', 'spam_model')
        use_llm = data.get('use_llm', False)  # Optional LLM verification

        if not content:
            return jsonify({"error": "No content provided"}), 400

        # Load model
        model_data = load_model(model_name)
        if not model_data:
            return jsonify({"error": "Model not found"}), 404

        # Clean and predict with DQN
        cleaned_content = clean_text(content)
        content_vector = model_data['vectorizer'].transform([cleaned_content]).toarray()
        content_vector = model_data['scaler'].transform(content_vector)
        action, _ = model_data['model'].predict(content_vector, deterministic=True)

        dqn_result = "Spam" if action == 1 else "Ham"

        response = {
            "prediction": dqn_result,
            "model_used": model_name
        }

        # Optional: Add LLM verification
        if use_llm and LLM_ENABLED:
            llm_result = quick_llm_verify(content)
            if llm_result:
                response["llm_verification"] = llm_result
                response["agreement"] = (dqn_result == llm_result)
                # If they disagree, note it
                if dqn_result != llm_result:
                    response["warning"] = "DQN and LLM predictions disagree"

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    try:
        data = request.json
        contents = data.get('contents', [])
        model_name = data.get('model_name', 'spam_model')

        if not contents:
            return jsonify({"error": "No contents provided"}), 400

        # Load model
        model_data = load_model(model_name)
        if not model_data:
            return jsonify({"error": "Model not found"}), 404

        predictions = []
        for content in contents:
            try:
                cleaned_content = clean_text(content)
                content_vector = model_data['vectorizer'].transform([cleaned_content]).toarray()
                content_vector = model_data['scaler'].transform(content_vector)
                action, _ = model_data['model'].predict(content_vector, deterministic=True)
                result = "Spam" if action == 1 else "Ham"
                predictions.append(result)
            except:
                predictions.append("Error")

        return jsonify({
            "predictions": predictions,
            "model_used": model_name
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Clear loaded models from cache"""
    global loaded_models
    loaded_models = {}
    return jsonify({"status": "Cache cleared"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)
