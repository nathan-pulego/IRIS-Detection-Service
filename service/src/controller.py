import asyncio
from data_cleansing.data_processor import DataProcessor
from bluetooth.ble_handler import BLEHandler
from feature_extraction.feature_vector import FeatureExtractor

async def main():
    queue = asyncio.Queue()
    processor = DataProcessor(queue)
    handler = BLEHandler(data_callback=processor.process_data)

    # Start BLE task in background
    bluetooth_task = asyncio.create_task(handler.connect_and_subscribe())
    extractor = FeatureExtractor(sample_rate=100, blink_threshold=1000, nod_threshold=0.5)

    try:
        while True:
            frame = await queue.get()
            avg_accel = extractor.getAvgAccelScalar(frame)
            blink_scalar = extractor.getBlinkScalar(frame)
            nod_freq = extractor.getNodFreqScalar(frame)
            print(f"Average Acceleration (ay): {avg_accel:.2f}")
            print(f"Average Blink Duration: {blink_scalar:.2f} ms")
            print(f"Nodding Frequency: {nod_freq:.2f} Hz")
            queue.task_done()
    except asyncio.CancelledError:
        # Cancel BLE task on shutdown
        bluetooth_task.cancel()
        try:
            await bluetooth_task  # Wait for clean shutdown
        except asyncio.CancelledError:
            pass
    
if __name__ == "__main__":
    asyncio.run(main())