import asyncio
import pandas as pd
import io
from typing import List, Dict
from src.config import FRAME_SIZE  # Number of rows per frame

class DataProcessor:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.buffer: List[Dict] = []

    def process_data(self, data: str):
        """Parse CSV string to DataFrame, clean, buffer, and queue frames."""
        try:
            df_chunk = pd.read_csv(io.StringIO(data), header=0 if not self.buffer else None)

            # Rename raw_voltage -> photodiode_value for consistency
            if 'raw_voltage' in df_chunk.columns:
                df_chunk.rename(columns={'raw_voltage': 'photodiode_value'}, inplace=True)

            df_chunk = df_chunk.dropna()  # Basic cleansing

            for _, row in df_chunk.iterrows():
                self.buffer.append(row.to_dict())

            while len(self.buffer) >= FRAME_SIZE:
                frame_df = pd.DataFrame(self.buffer[:FRAME_SIZE])
                self.buffer = self.buffer[FRAME_SIZE:]
                asyncio.create_task(self._queue_frame(frame_df))
        except Exception as e:
            print(f"DataProcessor error: {e}")

    async def _queue_frame(self, frame_df: pd.DataFrame):
        await self.queue.put(frame_df)
