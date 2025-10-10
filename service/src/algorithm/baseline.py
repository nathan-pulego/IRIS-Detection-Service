import json
import os

BASELINE_PATH = "drowsiness_baseline.json"

def define_and_save_drowsiness_baseline(path=BASELINE_PATH):
    baseline_features = {
        "avg_blink_duration_ms": 250.0,
        "nod_freq_hz": 0.2,
        "avg_accel_ay": 0.0
    }
    with open(path, "w") as f:
        json.dump(baseline_features, f, indent=4)
    print(f"Drowsiness detection baseline saved to {path}")

def load_baseline(path=BASELINE_PATH):
    """Load the baseline JSON, returns dict or None if missing."""
    if not os.path.exists(path):
        print(f"Baseline file not found at {path}. Run define_and_save_drowsiness_baseline() first.")
        return None
    with open(path, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    define_and_save_drowsiness_baseline()
