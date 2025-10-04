import asyncio
import pandas as pd
import numpy as np
from src.bluetooth.ble_handler import BLEHandler
from src.data_cleansing.data_processor import DataProcessor
from src.feature_extraction.feature_vector import FeatureExtractor

# Test DataProcessor
async def test_data_processor():
    print("Testing DataProcessor...")
    queue = asyncio.Queue()
    processor = DataProcessor(queue)

    # Mock CSV data (simulate BLE input)
    mock_csv = "photodiode_value,ay,gz\n1000,0.1,0.0\n999,0.2,0.1\n"

    # Process the data
    processor.process_data(mock_csv)

    # Check buffer
    assert len(processor.buffer) == 2, f"Expected 2 rows in buffer, got {len(processor.buffer)}"
    assert processor.buffer[0]['photodiode_value'] == 1000, "First row photodiode_value mismatch"

    # Simulate more data to fill frame (FRAME_SIZE=1000, so add 998 more rows)
    for i in range(998):
        processor.process_data("1000,0.1,0.0\n")

    # Check if frame was queued (buffer should be empty after queueing)
    frame = await queue.get()
    assert isinstance(frame, pd.DataFrame), "Queued item should be a DataFrame"
    assert len(frame) == 1000, f"Frame should have 1000 rows, got {len(frame)}"
    assert len(processor.buffer) == 0, "Buffer should be empty after queueing"

    print("DataProcessor test passed!")

# Test FeatureExtractor
def test_feature_extractor():
    print("Testing FeatureExtractor...")
    extractor = FeatureExtractor(sample_rate=100, blink_threshold=1000, nod_threshold=0.5)

    # Create mock DataFrame (from feature_vector.py simulation)
    mock_data = pd.DataFrame({
        'photodiode_value': np.random.randint(900, 1100, 1000),
        'ay': np.random.rand(1000) * 0.5,
        'gz': np.zeros(1000)
    })

    # Simulate blinks (drops in photodiode value)
    mock_data.loc[100:105, 'photodiode_value'] = np.random.randint(50, 150, 6)
    mock_data.loc[500:510, 'photodiode_value'] = np.random.randint(50, 150, 11)

    # Simulate nodding (spikes in gz)
    mock_data.loc[250:270, 'gz'] = np.sin(np.linspace(0, np.pi * 5, 21)) * 5

    # Test methods
    avg_blink = extractor.getBlinkScalar(mock_data)
    nod_freq = extractor.getNodFreqScalar(mock_data)
    avg_accel = extractor.getAvgAccelScalar(mock_data)

    # Assertions (basic checks)
    assert isinstance(avg_blink, float), "getBlinkScalar should return float"
    assert avg_blink > 0, "Blink duration should be positive with simulated blinks"
    assert isinstance(nod_freq, float), "getNodFreqScalar should return float"
    assert nod_freq >= 0, "Nod frequency should be non-negative"
    assert isinstance(avg_accel, float), "getAvgAccelScalar should return float"
    assert -1 <= avg_accel <= 1, "Average accel should be in expected range"

    print(f"Average Blink Duration: {avg_blink:.2f} ms")
    print(f"Nodding Frequency: {nod_freq:.2f} Hz")
    print(f"Average Acceleration (ay): {avg_accel:.2f}")
    print("FeatureExtractor test passed!")

# Test BLEHandler (mocked, since real BLE needs hardware)
async def test_ble_handler():
    print("Testing BLEHandler (mocked)...")
    queue = asyncio.Queue()
    processor = DataProcessor(queue)

    # Mock callback
    def mock_callback(data: str):
        processor.process_data(data)

    handler = BLEHandler(data_callback=mock_callback)

    # Simulate data reception (normally done by BLE notifications)
    mock_data = "photodiode_value,ay,gz\n1000,0.1,0.0\n"
    handler._handle_tx_data(None, bytearray(mock_data.encode('utf-8')))  # Simulate BLE event

    # Check if data was processed
    assert len(processor.buffer) == 1, "Buffer should have 1 row after mock callback"

    print("BLEHandler test passed!")

# Integration test (simulate controller flow)
async def test_integration():
    print("Testing integration (controller simulation)...")
    queue = asyncio.Queue()
    processor = DataProcessor(queue)
    extractor = FeatureExtractor(sample_rate=100, blink_threshold=1000, nod_threshold=0.5)

    # Simulate BLE data
    mock_csv = "photodiode_value,ay,gz\n1000,0.1,0.0\n999,0.2,0.1\n"
    processor.process_data(mock_csv)

    # Add more data to fill frame
    for i in range(999):
        processor.process_data("photodiode_value,ay,gz\n1000,0.1,0.0\n")

    # Get frame and extract features
    frame = await queue.get()
    avg_accel = extractor.getAvgAccelScalar(frame)
    blink_scalar = extractor.getBlinkScalar(frame)
    nod_freq = extractor.getNodFreqScalar(frame)

    # Basic checks
    assert isinstance(frame, pd.DataFrame), "Frame should be DataFrame"
    assert len(frame) == 1000, "Frame should have 1000 rows"
    assert isinstance(avg_accel, float), "Features should be floats"

    print(f"Integration test: Frame processed, features extracted (avg_accel: {avg_accel:.2f})")
    print("Integration test passed!")

# Run all tests
async def main():
    await test_data_processor()
    test_feature_extractor()
    await test_ble_handler()
    await test_integration()
    print("All tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
