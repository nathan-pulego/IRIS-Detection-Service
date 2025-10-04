# train hmm models for alert and drowsy states
# using synthetic data for demonstration purposes

import numpy as np
from hmmlearn import hmm
import joblib
import os

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'saved_models')
ALERT_MODEL_PATH = os.path.join(MODEL_DIR, 'alert_hmm.pkl')
DROWSY_MODEL_PATH = os.path.join(MODEL_DIR, 'drowsy_hmm.pkl')

def train_and_save_hmms():
    """
    Trains two separate Hidden Markov Models for 'Alert' and 'Drowsy' states
    and saves them to files. This is for demonstration.
    """
    # Create directory if it doesn't exist
    os.makedirs(MODEL_DIR, exist_ok=True)

    # --- Synthetic Alert Data ---
    # Represents stable driving: low nod frequency, short blinks.
    alert_features = np.array([[0.1, 100], [0.0, 110], [0.2, 90], [0.1, 120]])

    # --- Synthetic Drowsy Data ---
    # Represents unstable driving: higher nod frequency, long blinks/eye closure.
    drowsy_features = np.array([[0.8, 500], [1.2, 700], [0.9, 600], [1.5, 800]])

    # --- Train Alert HMM ---
    alert_model = hmm.GaussianHMM(n_components=2, covariance_type="diag", n_iter=100)
    alert_model.fit(alert_features)
    joblib.dump(alert_model, ALERT_MODEL_PATH)
    print(f"Alert model trained and saved to {ALERT_MODEL_PATH}")

    # --- Train Drowsy HMM ---
    drowsy_model = hmm.GaussianHMM(n_components=2, covariance_type="diag", n_iter=100)
    drowsy_model.fit(drowsy_features)
    joblib.dump(drowsy_model, DROWSY_MODEL_PATH)
    print(f"Drowsy model trained and saved to {DROWSY_MODEL_PATH}")

def load_models():
    """Loads the pre-trained HMM models from disk."""
    if not os.path.exists(ALERT_MODEL_PATH) or not os.path.exists(DROWSY_MODEL_PATH):
        print("Models not found, training new ones...")
        train_and_save_hmms()
    
    alert_model = joblib.load(ALERT_MODEL_PATH)
    drowsy_model = joblib.load(DROWSY_MODEL_PATH)
    return alert_model, drowsy_model

def predict_state(feature_vector, alert_model, drowsy_model):
    """
    Calculates the likelihood of the feature vector belonging to each model
    and returns the most likely state.
    """
    # Reshape for HMM: (n_samples, n_features)
    X = np.array(feature_vector).reshape(1, -1)
    
    alert_score = alert_model.score(X)
    drowsy_score = drowsy_model.score(X)
    
    print(f"Alert Score: {alert_score:.2f}, Drowsy Score: {drowsy_score:.2f}")
    
    if alert_score > drowsy_score:
        return "Alert"
    else:
        return "Drowsy"

if __name__ == '__main__':
    # This allows you to run `python ml_models.py` to pre-train the models
    train_and_save_hmms()