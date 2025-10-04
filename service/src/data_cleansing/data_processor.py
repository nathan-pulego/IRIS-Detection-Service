import asyncio
import pandas as pd
import io
from typing import List, Dict
from config import FRAME_SIZE  # Number of rows per frame

class DataProcessor:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.buffer: List[Dict] = []  # Accumulate rows

    def process_data(self, data: str):
        """Parse str into DataFrame, buffer rows, and queue complete frames"""
        try:
            # Parse CSV string to DataFrame
            df_chunk = pd.read_csv(io.StringIO(data), header=0 if not self.buffer else None)
            
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

