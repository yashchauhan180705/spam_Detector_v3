import os
import pandas as pd
import numpy as np
import joblib
from flask import Flask, request, jsonify
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from stable_baselines3 import DQN
from stable_baselines3.common.env_util import make_vec_env
import gymnasium as gym
from gymnasium import spaces
import json
import datetime
from collections import deque
import random
import threading

app = Flask(__name__)

# Use shared models directory - can be overridden via environment variable
MODEL_DIR = os.getenv('MODEL_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models'))
os.makedirs(MODEL_DIR, exist_ok=True)

# Feedback Replay Buffer for DQN-style reinforcement learning
FEEDBACK_BUFFER_FILE = os.path.join(MODEL_DIR, 'feedback_buffer.json')
buffer_lock = threading.Lock()


class FeedbackReplayBuffer:
    """
    Replay buffer for storing feedback experiences.
    Stores: (content, state_vector, predicted_action, corrected_action, reward)
    """

    def __init__(self, max_size=10000):
        self.buffer = deque(maxlen=max_size)
        self.max_size = max_size
        self._load_from_file()

    def _load_from_file(self):
        """Load existing buffer from file."""
        try:
            if os.path.exists(FEEDBACK_BUFFER_FILE):
                with open(FEEDBACK_BUFFER_FILE, 'r') as f:
                    data = json.load(f)
                    self.buffer = deque(data.get('experiences', []), maxlen=self.max_size)
                    print(f"📦 Loaded {len(self.buffer)} experiences from replay buffer")
        except Exception as e:
            print(f"⚠️ Could not load replay buffer: {e}")
            self.buffer = deque(maxlen=self.max_size)

    def _save_to_file(self):
        """Persist buffer to file."""
        try:
            with open(FEEDBACK_BUFFER_FILE, 'w') as f:
                json.dump({
                    'experiences': list(self.buffer),
                    'last_updated': datetime.datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save replay buffer: {e}")

    def add(self, content, predicted, corrected, model_name):
        """Add a feedback experience to the buffer."""
        reward = 1.0 if predicted == corrected else -1.0
        experience = {
            'content': content,
            'predicted': predicted,
            'corrected': corrected,
            'reward': reward,
            'model_name': model_name,
            'timestamp': datetime.datetime.now().isoformat()
        }
        with buffer_lock:
            self.buffer.append(experience)
            self._save_to_file()
        return experience

    def sample(self, batch_size, model_name=None):
        """Sample a batch of experiences for training."""
        with buffer_lock:
            if model_name:
                filtered = [e for e in self.buffer if e.get('model_name') == model_name]
            else:
                filtered = list(self.buffer)

            if len(filtered) == 0:
                return []

            batch_size = min(batch_size, len(filtered))
            return random.sample(filtered, batch_size)

    def get_all(self, model_name=None):
        """Get all experiences, optionally filtered by model."""
        with buffer_lock:
            if model_name:
                return [e for e in self.buffer if e.get('model_name') == model_name]
            return list(self.buffer)

    def clear(self, model_name=None):
        """Clear buffer, optionally only for a specific model."""
        with buffer_lock:
            if model_name:
                self.buffer = deque(
                    [e for e in self.buffer if e.get('model_name') != model_name],
                    maxlen=self.max_size
                )
            else:
                self.buffer.clear()
            self._save_to_file()

    def size(self, model_name=None):
        """Get buffer size."""
        with buffer_lock:
            if model_name:
                return len([e for e in self.buffer if e.get('model_name') == model_name])
            return len(self.buffer)


# Global replay buffer instance
replay_buffer = FeedbackReplayBuffer()


class SpamEnv(gym.Env):
    def __init__(self, X, y):
        super(SpamEnv, self).__init__()
        self.X = X.astype(np.float32)
        self.y = y
        self.current_index = 0
        self.max_steps = len(X)
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(X.shape[1],), dtype=np.float32)
        self.action_space = spaces.Discrete(2)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_index = 0
        obs = self.X[self.current_index]
        return obs, {}

    def step(self, action):
        true_label = self.y[self.current_index]
        reward = 1.0 if action == true_label else -1.0
        self.current_index += 1
        terminated = self.current_index >= self.max_steps
        next_obs = self.X[self.current_index] if not terminated else np.zeros(self.X.shape[1], dtype=np.float32)
        return next_obs, reward, terminated, False, {}


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route('/train', methods=['POST'])
def train_model():
    try:
        data = request.json
        df_data = data['dataset']
        text_column = data['text_column']
        label_column = data['label_column']
        model_name = data['model_name']
        timesteps = data.get('timesteps', 50000)

        # Convert to DataFrame
        df = pd.DataFrame(df_data)

        # Replace empty strings with NaN, then drop NaN values
        df[text_column] = df[text_column].replace('', np.nan)
        df[label_column] = df[label_column].replace('', np.nan)
        df_clean = df[[text_column, label_column]].dropna()

        # Additional validation
        if len(df_clean) < 10:
            return jsonify({"error": "Dataset too small after cleaning. Need at least 10 valid samples."}), 400

        # Map labels to 0 and 1
        unique_labels = df_clean[label_column].unique()
        if len(unique_labels) != 2:
            return jsonify({"error": "Dataset must have exactly 2 classes"}), 400

        label_map = {unique_labels[0]: 0, unique_labels[1]: 1}
        df_clean['label'] = df_clean[label_column].map(label_map)

        X_text = df_clean[text_column].astype(str)
        y = df_clean['label'].values

        # TF-IDF and Scaling
        vectorizer = TfidfVectorizer(stop_words='english', max_features=500)
        X = vectorizer.fit_transform(X_text).toarray()
        scaler = MinMaxScaler()
        X = scaler.fit_transform(X)

        # Train/Test Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Create environment
        def make_env():
            return SpamEnv(X_train, y_train)

        env = make_vec_env(make_env, n_envs=1)

        # Create and train model
        model = DQN(
            "MlpPolicy",
            env,
            verbose=1,
            learning_rate=0.0001,
            buffer_size=10000,
            learning_starts=1000,
            batch_size=32,
            gamma=0.99,
            exploration_fraction=0.1,
            exploration_initial_eps=1.0,
            exploration_final_eps=0.02,
            train_freq=4,
            target_update_interval=1000
        )

        # Train the model
        model.learn(total_timesteps=timesteps)

        # Evaluate on test set
        test_env = SpamEnv(X_test, y_test)
        obs, _ = test_env.reset()
        correct = 0
        total = len(X_test)

        for i in range(total):
            action, _ = model.predict(obs, deterministic=True)
            if int(action) == y_test[i]:
                correct += 1
            obs, _, terminated, _, _ = test_env.step(int(action))
            if terminated:
                break

        accuracy = correct / total if total > 0 else 0.0
        
        # Handle NaN values
        if np.isnan(accuracy) or np.isinf(accuracy):
            accuracy = 0.0

        # Save model, vectorizer, and scaler
        model_path = os.path.join(MODEL_DIR, f"{model_name}")
        vectorizer_path = os.path.join(MODEL_DIR, f"{model_name}_vectorizer.pkl")
        scaler_path = os.path.join(MODEL_DIR, f"{model_name}_scaler.pkl")
        metadata_path = os.path.join(MODEL_DIR, f"{model_name}_metadata.json")

        model.save(model_path)
        joblib.dump(vectorizer, vectorizer_path)
        joblib.dump(scaler, scaler_path)

        # Save metadata - ensure all values are JSON serializable
        metadata = {
            'model_name': model_name,
            'accuracy': float(accuracy),
            'training_samples': int(len(df_clean)),
            'timesteps': int(timesteps),
            'timestamp': datetime.datetime.now().isoformat(),
            'label_map': {str(k): int(v) for k, v in label_map.items()}
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return jsonify({
            "status": "success",
            "model_name": model_name,
            "accuracy": float(accuracy),
            "training_samples": int(len(df_clean)),
            "timesteps": int(timesteps)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/models', methods=['GET'])
def list_models():
    try:
        models = []
        for file in os.listdir(MODEL_DIR):
            if file.endswith('.zip'):
                model_name = file.replace('.zip', '')
                metadata_path = os.path.join(MODEL_DIR, f"{model_name}_metadata.json")
                
                metadata = {}
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                
                models.append({
                    'name': model_name,
                    'metadata': metadata
                })
        
        return jsonify({"models": models}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/model/<model_name>/metadata', methods=['GET'])
def get_model_metadata(model_name):
    try:
        metadata_path = os.path.join(MODEL_DIR, f"{model_name}_metadata.json")
        
        if not os.path.exists(metadata_path):
            return jsonify({"error": "Model not found"}), 404
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return jsonify(metadata), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/model/<model_name>', methods=['DELETE'])
def delete_model(model_name):
    try:
        # Define all possible files for this model
        files_to_delete = [
            os.path.join(MODEL_DIR, f"{model_name}.zip"),
            os.path.join(MODEL_DIR, f"{model_name}_vectorizer.pkl"),
            os.path.join(MODEL_DIR, f"{model_name}_scaler.pkl"),
            os.path.join(MODEL_DIR, f"{model_name}_metadata.json")
        ]
        
        deleted_files = []
        for file_path in files_to_delete:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(os.path.basename(file_path))
        
        if deleted_files:
            return jsonify({
                "status": "success",
                "message": f"Model '{model_name}' deleted successfully",
                "deleted_files": deleted_files
            }), 200
        else:
            return jsonify({"error": "Model not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# FEEDBACK REPLAY BUFFER ENDPOINTS
# ============================================================================

@app.route('/feedback/store', methods=['POST'])
def store_feedback():
    """
    Store feedback in replay buffer for later RL update.
    This is the first step of the two-step feedback learning process.
    """
    try:
        data = request.json
        model_name = data.get('model_name')
        feedback_list = data.get('feedback', [])

        if not model_name:
            return jsonify({"error": "Model name required"}), 400

        if not feedback_list:
            return jsonify({"error": "No feedback provided"}), 400

        stored_count = 0
        corrections_count = 0

        for item in feedback_list:
            content = item.get('content', '')
            predicted = item.get('predicted', '')
            corrected = item.get('corrected', '')

            if content and predicted and corrected:
                replay_buffer.add(content, predicted, corrected, model_name)
                stored_count += 1
                if predicted != corrected:
                    corrections_count += 1

        return jsonify({
            "status": "success",
            "stored": stored_count,
            "corrections": corrections_count,
            "buffer_size": replay_buffer.size(model_name),
            "message": f"Stored {stored_count} experiences ({corrections_count} corrections)"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/feedback/buffer', methods=['GET'])
def get_buffer_status():
    """Get the current status of the feedback replay buffer."""
    try:
        model_name = request.args.get('model_name')

        total_size = replay_buffer.size()
        model_size = replay_buffer.size(model_name) if model_name else total_size

        # Get correction stats
        experiences = replay_buffer.get_all(model_name)
        corrections = sum(1 for e in experiences if e.get('reward', 0) < 0)

        return jsonify({
            "total_buffer_size": total_size,
            "model_buffer_size": model_size,
            "corrections_count": corrections,
            "reinforcements_count": model_size - corrections
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/feedback/clear', methods=['POST'])
def clear_buffer():
    """Clear the feedback replay buffer."""
    try:
        data = request.json or {}
        model_name = data.get('model_name')

        replay_buffer.clear(model_name)

        return jsonify({
            "status": "success",
            "message": f"Buffer cleared" + (f" for model '{model_name}'" if model_name else "")
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/rl-update', methods=['POST'])
def rl_update():
    """
    Perform DQN-style reinforcement learning update using replay buffer.
    This uses experiences stored via /feedback/store endpoint.

    Key differences from old /retrain:
    - Uses replay buffer experiences (not direct supervised learning)
    - Computes reward signal from feedback (+1 correct, -1 correction)
    - Updates model incrementally without overwriting during runtime
    - Safer and more aligned with RL principles
    """
    try:
        data = request.json
        model_name = data.get('model_name')
        batch_size = data.get('batch_size', 32)
        use_all = data.get('use_all', True)  # Use all experiences or sample
        clear_after = data.get('clear_after', False)  # Clear buffer after update

        if not model_name:
            return jsonify({"error": "Model name required"}), 400

        # Check buffer has experiences
        buffer_size = replay_buffer.size(model_name)
        if buffer_size == 0:
            return jsonify({
                "error": "No feedback experiences in buffer. Use /feedback/store first.",
                "buffer_size": 0
            }), 400

        # Load existing model components
        model_path = os.path.join(MODEL_DIR, f"{model_name}.zip")
        vectorizer_path = os.path.join(MODEL_DIR, f"{model_name}_vectorizer.pkl")
        scaler_path = os.path.join(MODEL_DIR, f"{model_name}_scaler.pkl")
        metadata_path = os.path.join(MODEL_DIR, f"{model_name}_metadata.json")

        if not all(os.path.exists(p) for p in [model_path, vectorizer_path, scaler_path]):
            return jsonify({"error": "Model not found"}), 404

        # Load model components
        vectorizer = joblib.load(vectorizer_path)
        scaler = joblib.load(scaler_path)
        model = DQN.load(model_path)

        # Get experiences from buffer
        if use_all:
            experiences = replay_buffer.get_all(model_name)
        else:
            experiences = replay_buffer.sample(batch_size, model_name)

        if len(experiences) == 0:
            return jsonify({"error": "No valid experiences to learn from"}), 400

        # Prepare training data from experiences
        contents = [e['content'] for e in experiences]
        # Use CORRECTED labels (the human feedback) - this is what we want to learn
        labels = [1 if e['corrected'] == 'Spam' else 0 for e in experiences]
        rewards = [e['reward'] for e in experiences]

        # Transform using existing vectorizer and scaler
        X = vectorizer.transform(contents).toarray()
        X = scaler.transform(X)
        y = np.array(labels)

        # Create weighted environment based on rewards
        # Higher weight for corrections (negative rewards become positive learning signal)
        class WeightedSpamEnv(gym.Env):
            def __init__(self, X_data, y_data, reward_weights):
                super().__init__()
                self.X = X_data.astype(np.float32)
                self.y = y_data
                self.weights = reward_weights
                self.current_index = 0
                self.max_steps = len(X_data)
                self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(X_data.shape[1],), dtype=np.float32)
                self.action_space = spaces.Discrete(2)

            def reset(self, seed=None, options=None):
                super().reset(seed=seed)
                self.current_index = 0
                return self.X[self.current_index], {}

            def step(self, action):
                true_label = self.y[self.current_index]
                # Amplify reward for corrections (originally wrong predictions)
                base_reward = 1.0 if action == true_label else -1.0
                weight = abs(self.weights[self.current_index])
                # If this was a correction, double the learning signal
                if self.weights[self.current_index] < 0:
                    weight = 2.0

                reward = base_reward * weight
                self.current_index += 1
                terminated = self.current_index >= self.max_steps
                next_obs = self.X[self.current_index] if not terminated else np.zeros(self.X.shape[1], dtype=np.float32)
                return next_obs, reward, terminated, False, {}

        # Create weighted environment
        def make_weighted_env():
            return WeightedSpamEnv(X, y, rewards)

        env = make_vec_env(make_weighted_env, n_envs=1)
        model.set_env(env)

        # Calculate timesteps - more for corrections
        corrections_count = sum(1 for r in rewards if r < 0)
        base_timesteps = len(experiences) * 50
        correction_bonus = corrections_count * 100
        timesteps = min(max(base_timesteps + correction_bonus, 1000), 15000)

        # Perform RL update (continue training, don't reset)
        model.learn(total_timesteps=timesteps, reset_num_timesteps=False)

        # Evaluate on the feedback data
        test_env = SpamEnv(X, y)
        obs, _ = test_env.reset()
        correct = 0
        total = len(X)

        for i in range(total):
            action, _ = model.predict(obs, deterministic=True)
            if int(action) == y[i]:
                correct += 1
            obs, _, terminated, _, _ = test_env.step(int(action))
            if terminated:
                break

        accuracy = correct / total if total > 0 else 0.0
        if np.isnan(accuracy) or np.isinf(accuracy):
            accuracy = 0.0

        # Save updated model (create backup first)
        backup_path = os.path.join(MODEL_DIR, f"{model_name}_backup.zip")
        if os.path.exists(model_path):
            import shutil
            shutil.copy(model_path, backup_path)

        model.save(model_path.replace('.zip', ''))

        # Update metadata
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

        rl_updates = metadata.get('rl_updates', 0) + 1
        metadata['rl_update_accuracy'] = float(accuracy)
        metadata['rl_update_samples'] = len(experiences)
        metadata['rl_update_corrections'] = corrections_count
        metadata['rl_update_timesteps'] = timesteps
        metadata['rl_update_timestamp'] = datetime.datetime.now().isoformat()
        metadata['rl_updates'] = rl_updates
        metadata['total_feedback_samples'] = metadata.get('total_feedback_samples', 0) + len(experiences)

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Optionally clear buffer after successful update
        if clear_after:
            replay_buffer.clear(model_name)

        return jsonify({
            "status": "success",
            "model_name": model_name,
            "accuracy": float(accuracy),
            "experiences_used": len(experiences),
            "corrections_applied": corrections_count,
            "timesteps": timesteps,
            "rl_updates_total": rl_updates,
            "buffer_cleared": clear_after,
            "message": f"RL update complete! Used {len(experiences)} experiences ({corrections_count} corrections)"
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# Legacy retrain endpoint - redirects to RL update
@app.route('/retrain', methods=['POST'])
def retrain_model():
    """
    Legacy retrain endpoint - now uses replay buffer approach.
    Accepts old-style feedback_data and converts to buffer experiences.
    """
    try:
        data = request.json
        model_name = data.get('model_name')
        feedback_data = data.get('feedback_data', [])

        if not model_name:
            return jsonify({"error": "Model name required"}), 400

        if not feedback_data:
            return jsonify({"error": "No feedback data provided"}), 400

        # Convert old format to new format and store in buffer
        for item in feedback_data:
            content = item.get('content', '')
            label = item.get('label', '')
            # In old format, 'label' is the corrected label
            # We need to infer predicted from the original if available
            predicted = item.get('original_prediction', label)
            replay_buffer.add(content, predicted, label, model_name)

        # Now perform RL update
        # Load model and perform update
        model_path = os.path.join(MODEL_DIR, f"{model_name}.zip")
        vectorizer_path = os.path.join(MODEL_DIR, f"{model_name}_vectorizer.pkl")
        scaler_path = os.path.join(MODEL_DIR, f"{model_name}_scaler.pkl")
        metadata_path = os.path.join(MODEL_DIR, f"{model_name}_metadata.json")

        if not all(os.path.exists(p) for p in [model_path, vectorizer_path, scaler_path]):
            return jsonify({"error": "Model not found"}), 404

        vectorizer = joblib.load(vectorizer_path)
        scaler = joblib.load(scaler_path)
        model = DQN.load(model_path)

        # Prepare data
        contents = [item['content'] for item in feedback_data]
        labels = [1 if item['label'] == 'Spam' else 0 for item in feedback_data]

        X = vectorizer.transform(contents).toarray()
        X = scaler.transform(X)
        y = np.array(labels)

        # Create environment
        def make_env():
            return SpamEnv(X, y)

        env = make_vec_env(make_env, n_envs=1)
        model.set_env(env)

        timesteps = min(max(len(feedback_data) * 100, 1000), 10000)
        model.learn(total_timesteps=timesteps, reset_num_timesteps=False)

        # Evaluate
        test_env = SpamEnv(X, y)
        obs, _ = test_env.reset()
        correct = 0
        total = len(X)

        for i in range(total):
            action, _ = model.predict(obs, deterministic=True)
            if int(action) == y[i]:
                correct += 1
            obs, _, terminated, _, _ = test_env.step(int(action))
            if terminated:
                break

        accuracy = correct / total if total > 0 else 0.0
        if np.isnan(accuracy) or np.isinf(accuracy):
            accuracy = 0.0

        model.save(model_path.replace('.zip', ''))

        # Update metadata
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

        metadata['retrain_accuracy'] = float(accuracy)
        metadata['retrain_samples'] = len(feedback_data)
        metadata['retrain_timestamp'] = datetime.datetime.now().isoformat()
        metadata['total_training_samples'] = metadata.get('training_samples', 0) + len(feedback_data)

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return jsonify({
            "status": "success",
            "model_name": model_name,
            "retrain_accuracy": float(accuracy),
            "samples_used": len(feedback_data),
            "timesteps": timesteps
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
