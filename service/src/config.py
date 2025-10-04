# BLE Configuration
DEVICE_NAME = "AntiSleepGlasses"  # Replace with the actual advertised BLE device name (e.g., from NimBLE transmitter)
TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # TX characteristic UUID for subscribing to notifications (from transmitter code)

FRAME_SIZE = 1000  # Number of rows per frame
SAMPLE_RATE = 100  # Hz, assumed constant sampling rate from device

# -----------Feature Extraction Parameters ----------- #

BLINK_THRESHOLD = 1000  # ms, threshold to detect blinks
NOD_THRESHOLD = 0.5    # g, threshold to detect nodding frequency
