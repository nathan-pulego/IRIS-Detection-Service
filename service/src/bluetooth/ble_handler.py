import asyncio
import logging
from bleak import BleakScanner, BleakClient
from typing import Optional, Callable
from src.config import DEVICE_NAME, TX_CHAR_UUID

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class BLEHandler:
    def __init__(
        self,
        data_callback: Callable[[str], None],
        device_name: str = DEVICE_NAME,
        tx_uuid: str = TX_CHAR_UUID
    ):
        self.data_callback = data_callback
        self.device_name = device_name
        self.tx_uuid = tx_uuid
        self.client: Optional[BleakClient] = None
        self._running = True

    async def connect_and_subscribe(self):
        """Connect to BLE device and subscribe to TX notifications."""
        backoff = 2  # seconds, for reconnection delay

        while self._running:
            try:
                logging.info(f"Scanning for BLE device '{self.device_name}'...")
                devices = await BleakScanner.discover()
                device = next((d for d in devices if d.name == self.device_name), None)

                if not device:
                    logging.warning("Device not found. Retrying...")
                    await asyncio.sleep(backoff)
                    continue

                self.client = BleakClient(device.address)
                await self.client.connect()
                logging.info(f"Connected to {self.device_name} ({device.address})")

                await self.client.start_notify(self.tx_uuid, self._handle_tx_data)
                backoff = 2  # reset backoff on success

                # Keep connection alive
                while self._running and self.client.is_connected:
                    await asyncio.sleep(5)

            except Exception as e:
                logging.error(f"BLE error: {e}")
                backoff = min(backoff * 2, 10)
                await asyncio.sleep(backoff)

            finally:
                if self.client:
                    try:
                        await self.client.disconnect()
                        logging.info("BLE disconnected.")
                    except Exception as e:
                        logging.warning(f"Error during disconnect: {e}")
                    self.client = None

        logging.info("BLE handler stopped.")

    async def stop(self):
        """Stop BLE handler and disconnect gracefully."""
        logging.info("Stopping BLE handler...")
        self._running = False
        if self.client and self.client.is_connected:
            try:
                await self.client.disconnect()
                logging.info("Disconnected cleanly.")
            except Exception as e:
                logging.warning(f"Error while stopping: {e}")

    def _handle_tx_data(self, sender, data: bytearray):
        """Handle incoming BLE TX notifications."""
        try:
            decoded = data.decode("utf-8", errors="ignore")
            self.data_callback(decoded)
        except Exception as e:
            logging.debug(f"Decode error: {e}")
