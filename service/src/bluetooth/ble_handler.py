import asyncio
from bleak import BleakScanner, BleakClient
from typing import Optional, Callable
from config import DEVICE_NAME, TX_CHAR_UUID

class BLEHandler:
    def __init__(self, data_callback: Callable[[bytearray], None]):
        self.data_callback = data_callback  # Callback to pass raw data to processor
        self.client: Optional[BleakClient] = None

    async def connect_and_subscribe(self):
        """Connect to BLE device and subscribe to TX."""
        while True:  # Reconnection loop
            try:
                # Scan for device by name
                devices = await BleakScanner.discover()
                device = next((d for d in devices if d.name == DEVICE_NAME), None)
                if not device:
                    await asyncio.sleep(5)
                    continue

                self.client = BleakClient(device.address)
                await self.client.connect()

                # Subscribe to TX for notifications
                await self.client.start_notify(TX_CHAR_UUID, self._handle_tx_data)

                # Keep alive by polling connection status
                while self.client.is_connected:
                    await asyncio.sleep(1)  # Check every second
            except Exception as e:
                await asyncio.sleep(5)
            finally:
                if self.client:
                    await self.client.disconnect()

    def _handle_tx_data(self, sender, data: bytearray):
        """Pass raw data to the processor callback."""
        self.data_callback(data)