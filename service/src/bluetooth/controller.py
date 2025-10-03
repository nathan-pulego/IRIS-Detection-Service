import asyncio
from ble_handler import BLEHandler
from service.src.data_cleansing.data_processor import DataProcessor

async def main():
    """Coordinate BLE handling, data processing, and feature extraction."""
    queue = asyncio.Queue()
    
    # Initialize processor and handler
    processor = DataProcessor(queue)
    handler = BLEHandler(processor.process_data)
    
    # Start BLE handler
    handler_task = asyncio.create_task(handler.connect_and_subscribe())
    
    # Consume and process frames (e.g., for feature extraction)
    async def consume_frames():
        while True:
            frame = await queue.get()
            # Add FeatureExtractor logic here, e.g.:
            # extractor = FeatureExtractor(sample_rate=100)
            # features = extractor.extract(frame)
            # Process or output features
            queue.task_done()
    
    consumer_task = asyncio.create_task(consume_frames())
    
    # Run both tasks
    await asyncio.gather(handler_task, consumer_task)

if __name__ == "__main__":
    asyncio.run(main())