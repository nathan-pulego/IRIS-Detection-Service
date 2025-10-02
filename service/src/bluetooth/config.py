# BLE Configuration
DEVICE_NAME = "AntiSleepGlasses"  # Replace with the actual advertised BLE device name (e.g., from NimBLE transmitter)
TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # TX characteristic UUID for subscribing to notifications (from transmitter code)

# Data Processing Configuration
FRAME_SIZE = 1000  # Number of rows per DataFrame frame (adjust based on sample rate, e.g., 10s at 100Hz)
SAMPLE_RATE = 100  # Hz, for feature extraction (if needed)

"""bleak>=0.21.0
pandas>=1.5.0
numpy>=1.21.0
scipy>=1.7.0"""