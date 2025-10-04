# mock baseline for drowsiness detection in drivers

import json

def define_and_save_drowsiness_baseline(path="drowsiness_baseline.json"):
    """
    Defines a baseline for an alert driver and saves it to a JSON file.

    Rationale for Driving Context:
    - avg_blink_duration_ms: Kept at 250.0 ms. Longer durations are a key sign of microsleeps.
    - nod_freq_hz: An alert driver has minimal head bobbing. A baseline of 0.2 Hz 
      accounts for normal movements like checking mirrors. A significant increase
      suggests drowsiness.
    - avg_accel_ay: In normal driving, lateral acceleration should average near zero.
    """
    baseline_features = {
        "avg_blink_duration_ms": 250.0,
        "nod_freq_hz": 0.2,
        "avg_accel_ay": 0.0
    }

    with open(path, "w") as f:
        json.dump(baseline_features, f, indent=4)

    print(f"Drowsiness detection baseline saved to {path}")

if __name__ == '__main__':
    define_and_save_drowsiness_baseline()