# BLE Configuration
DEVICE_NAME = "AntiSleep-Glasses-ESP32"  # Must match Arduino BLE_NAME exactly (transmitter_doc.ino line 23)
SERVICE_UUID = "b86f0001-3e1d-4ad6-98ef-6b93f33e5a4a"  # NimBLE transmitter service UUID
TX_CHAR_UUID = "b86f0002-3e1d-4ad6-98ef-6b93f33e5a4a"  # TX characteristic UUID for subscribing to notifications (from transmitter code)

FRAME_SIZE = 1000  # Number of rows per frame
SAMPLE_RATE = 10   # Hz, ACTUAL sampling rate from device (ESP32 delay=100ms → 10 Hz, NOT 100 Hz)

# -----------Feature Extraction Parameters ----------- #

# Blink threshold: ESP32 sends IR in mV (0-3300 mV range)
# Normal eye open: ~300-500 mV
# Eye closed (blink): ~50-200 mV
# Using 250 mV as threshold to detect blinks (when IR drops below this)
BLINK_THRESHOLD = 250  # mV (was 1000, now corrected for your sensor range)

NOD_THRESHOLD = 0.5    # g, threshold to detect nodding frequency
