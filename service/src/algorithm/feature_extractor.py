# drowsiness checker for drivers using baseline comparison

import json
import pandas as pd
import numpy as np
import itertools
from scipy.signal import find_peaks

def load_baseline(path="drowsiness_baseline.json"):
    """Loads the drowsiness baseline from the specified JSON file."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Baseline file not found at {path}. Please run create_drowsiness_baseline.py first.")
        return None

def check_for_deviations(live_feature_vector, baseline):
    """
    Compares a live feature vector to the drowsiness baseline with specific tolerances.
    This provides a fast, initial warning system.
    """
    # Tolerances tuned for drowsiness detection
    tolerances = {
        "avg_blink_duration_ms": 0.4,  # 40% increase is a significant warning sign
        "nod_freq_hz": 1.0,            # 100% increase (doubling) indicates head bobbing
        "avg_accel_ay": 0.3            # Absolute threshold for lateral movement
    }
    
    results = {}
    deviations = {}

    for key, baseline_value in baseline.items():
        if key not in live_feature_vector:
            continue

        live_value = live_feature_vector[key]
        tolerance = tolerances[key]
        
        if key == 'avg_accel_ay': # Use absolute check for acceleration
            diff = abs(live_value)
        else: # Use relative check for other features
            diff = abs(live_value - baseline_value) / baseline_value if baseline_value != 0 else 0

        if diff > tolerance:
            results[key] = f"Deviation (Value: {live_value:.2f})"
            deviations[key] = live_value
        else:
            results[key] = "OK"
            
    return results, bool(deviations)

class FeatureExtractor:
    """
    Extracts key features from a pandas DataFrame of time-series sensor data.
    """
    def __init__(self, sample_rate, blink_threshold=1500, nod_threshold=0.5):
        self.sample_rate = sample_rate
        self.blink_threshold = blink_threshold
        self.nod_threshold = nod_threshold

    def getBlinkScalar(self, data: pd.DataFrame) -> float:
        """
        Calculates the average blink duration within a time window.
        Returns the average duration in milliseconds.
        This version is robust and does not depend on a 'time' column.
        """
        if data.empty or 'raw_voltage' not in data.columns:
            return 0.0

        # Create a boolean series where True indicates the value is below the blink threshold
        is_blinking = data['raw_voltage'] < self.blink_threshold
        blink_durations = []

        # Use groupby to find consecutive blocks of True values (blinks)
        for key, group in itertools.groupby(is_blinking):
            if key:
                # Calculate the duration by counting points and using the sample rate
                duration_in_points = len(list(group))
                duration_ms = (duration_in_points / self.sample_rate) * 1000
                blink_durations.append(duration_ms)

        if not blink_durations:
            return 0.0
        
        return float(np.mean(blink_durations))

    def getNodFreqScalar(self, data: pd.DataFrame) -> float:
        """
        Calculates the nodding frequency from gyroscope data (az axis).
        Returns the frequency in Hz.
        """
        if data.empty or 'az' not in data.columns:
            return 0.0
        
        # Use find_peaks to identify nodding events from the z-axis gyroscope data
        peaks, _ = find_peaks(data['az'].abs(), height=self.nod_threshold, distance=self.sample_rate / 10)
        
        if len(peaks) < 2:
            return 0.0

        # Calculate the differences between consecutive peaks
        peak_intervals = np.diff(peaks) / self.sample_rate

        # Calculate the average frequency in Hz
        return 1 / np.mean(peak_intervals) if len(peak_intervals) > 0 else 0.0

    # ... existing methods for other features ...