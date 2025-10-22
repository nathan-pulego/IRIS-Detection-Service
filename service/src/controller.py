import asyncio
import time
import logging
from pathlib import Path
from .data_cleansing.data_processor import DataProcessor
from .bluetooth.ble_handler import BLEHandler
from .feature_extraction.feature_vector import FeatureExtractor
from .algorithm.baseline import load_baseline, define_and_save_drowsiness_baseline
from .algorithm.ml_models import load_models, predict_state
from .config import SAMPLE_RATE, BLINK_THRESHOLD, NOD_THRESHOLD
from .network.ws_server import WebSocketServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths for data storage (using Path instead of string concat)
RAW_DIR = Path("./data/raw")
PREPROCESSED_DIR = Path("./data/preprocessed")
RAW_DIR.mkdir(parents=True, exist_ok=True)
PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)

async def main():
    queue = asyncio.Queue()
    
    # Initialize processor with raw CSV path for streaming BLE payloads
    raw_csv_file = RAW_DIR / "live_payloads.csv"
    processor = DataProcessor(queue, raw_csv_path=str(raw_csv_file))
    
    handler = BLEHandler(data_callback=processor.process_data)
    extractor = FeatureExtractor(sample_rate=SAMPLE_RATE, blink_threshold=BLINK_THRESHOLD, nod_threshold=NOD_THRESHOLD)

    # Load baseline
    baseline = load_baseline()
    if baseline is None:
        raise RuntimeError("Baseline not found. Please create it before starting.")

    # Load or train HMM models
    alert_model, drowsy_model = load_models()

    start_time = time.time()

    # State dict for dashboard
    state = {
        "connected": False,
        "duration": 0.0,
        "status": "Unknown",
        "metrics": {"avg_accel": 0.0, "blink_duration": 0.0, "nod_freq": 0.0}
    }

    # Start BLE listener
    bluetooth_task = asyncio.create_task(handler.connect_and_subscribe())

    # Start WebSocket server (Using 0.0.0.0 for broader network compatibility)
    ws_server = WebSocketServer(host="0.0.0.0") 
    ws_task = asyncio.create_task(ws_server.start())

    # Periodically broadcast state to dashboards
    async def broadcast_state():
        while True:
            try:
                await ws_server.broadcast(state)
            except Exception as e:
                logger.debug(f"Broadcast error: {e}")
            await asyncio.sleep(1)
    
    broadcast_task = asyncio.create_task(broadcast_state())

    try:
        while True:
            frame = await queue.get()

            # Feature extraction
            avg_accel = extractor.getAvgAccelScalar(frame)
            blink_duration = extractor.getBlinkScalar(frame)
            nod_freq = extractor.getNodFreqScalar(frame)

            # Include nod frequency for HMM prediction
            features = {
                "avg_blink_duration_ms": blink_duration,
                "avg_accel_ay": avg_accel,
                "nod_freq_hz": nod_freq
            }

            # HMM prediction: pass [blink_duration, nod_freq, avg_accel] (3-element vector)
            state_prediction = predict_state([blink_duration, nod_freq, avg_accel], alert_model, drowsy_model)

            # Determine driver state
            if state_prediction == "Drowsy":
                driver_status = "Danger"
            elif blink_duration < 300 or avg_accel > 0.3:
                driver_status = "Be careful"
            else:
                driver_status = "Looking good"

            # Update dashboard state (connected status visible here)
            state.update({
                "connected": handler.client.is_connected if handler.client else False,
                "duration": round(time.time() - start_time, 1),
                "status": driver_status,
                "metrics": {"avg_accel": avg_accel, "blink_duration": blink_duration, "nod_freq": nod_freq}
            })

            logger.info(f"State: {state}")

            queue.task_done()

    except asyncio.CancelledError:
        logger.info("Controller cancelled.")
    finally:
        await handler.stop()
        broadcast_task.cancel()
        ws_task.cancel()
        bluetooth_task.cancel()
        try:
            await broadcast_task
        except asyncio.CancelledError:
            pass
        try:
            await ws_task
        except asyncio.CancelledError:
            pass
        try:
            await bluetooth_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())