import asyncio
import pandas as pd
import io
from typing import List, Dict

FRAME_SIZE = 1000  # Rows per frame

class DataProcessor:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.buffer: List[Dict] = []  # Accumulate rows

    def process_data(self, data: bytearray):
        """Deserialize and cleanse data, then queue frames."""
        try:
            # Decode and parse CSV string to DataFrame
            csv_string = data.decode('utf-8')
            df_chunk = pd.read_csv(io.StringIO(csv_string), header=0 if not self.buffer else None)
            
            # Basic cleansing: Drop rows with NaN or invalid values (customize as needed)
            df_chunk = df_chunk.dropna()
            
            # Accumulate rows
            for _, row in df_chunk.iterrows():
                self.buffer.append(row.to_dict())
            
            # Queue complete frames
            while len(self.buffer) >= FRAME_SIZE:
                frame_df = pd.DataFrame(self.buffer[:FRAME_SIZE])
                self.buffer = self.buffer[FRAME_SIZE:]
                asyncio.create_task(self._queue_frame(frame_df))
        except Exception as e:
            pass  # Silent error handling

    async def _queue_frame(self, frame_df: pd.DataFrame):
        """Queue the DataFrame frame."""
        await self.queue.put(frame_df)

# Example integration
async def example():
    queue = asyncio.Queue()
    processor = DataProcessor(queue)
    
    # Simulate BLE handler callback
    def mock_callback(data):
        processor.process_data(data)
    
    # Mock data (replace with real BLE)
    mock_data = b"photodiode_value,ay,gz\n1000,0.1,0.0\n999,0.2,0.1\n"
    mock_callback(mock_data)
    
    # Consume
    frame = await queue.get()
    print(f"Processed frame: {frame.shape}")
    # Integrate with FeatureExtractor here

if __name__ == "__main__":
    asyncio.run(example())