import asyncio
import time
import os
from src.data_cleansing.data_processor import DataProcessor
from src.bluetooth.ble_handler import BLEHandler
from src.feature_extraction.feature_vector import FeatureExtractor
from src.algorithm.baseline import load_baseline, define_and_save_drowsiness_baseline
from src.algorithm.ml_models import load_models, predict_state
from src.config import SAMPLE_RATE, BLINK_THRESHOLD, NOD_THRESHOLD, FRAME_SIZE
from src.network.ws_server import WebSocketServer

# Paths for session storage
RAW_DIR = "./data/raw"
PREPROCESSED_DIR = "./data/preprocessed"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PREPROCESSED_DIR, exist_ok=True)

async def main():
    queue = asyncio.Queue()
    processor = DataProcessor(queue)
    handler = BLEHandler(data_callback=processor.process_data)
    extractor = FeatureExtractor(sample_rate=SAMPLE_RATE, blink_threshold=BLINK_THRESHOLD, nod_threshold=NOD_THRESHOLD)

    # Load baseline
    baseline = load_baseline()
    if baseline is None:
        raise RuntimeError("Baseline not found. Please create it before starting.")

    # Load or train HMM models
    alert_model, drowsy_model = load_models()

    # Create session
    session_id = f"S{int(time.time())}"
    start_time = time.time()
    raw_file_path = os.path.join(RAW_DIR, f"{session_id}.csv")
    preprocessed_file_path = os.path.join(PREPROCESSED_DIR, f"{session_id}.csv")

    # State dict for dashboard
    state = {
        "connected": False,
        "session_id": session_id,
        "duration": 0.0,
        "status": "Unknown",
        "metrics": {"avg_accel": 0.0, "blink_duration": 0.0, "nod_freq": 0.0}
    }

    # Start BLE listener
    bluetooth_task = asyncio.create_task(handler.connect_and_subscribe())

    # Start WebSocket server
    ws_server = WebSocketServer()
    asyncio.create_task(ws_server.start())

    # Periodically broadcast state to dashboards
    async def broadcast_state():
        while True:
            await ws_server.broadcast(state)
            await asyncio.sleep(1)

    try:
        while True:
            frame = await queue.get()

            # Save preprocessed frame
            frame.to_csv(preprocessed_file_path, mode="a", header=not os.path.exists(preprocessed_file_path), index=False)

            # Feature extraction
            avg_accel = extractor.getAvgAccelScalar(frame)
            blink_duration = extractor.getBlinkScalar(frame)
            nod_freq = extractor.getNodFreqScalar(frame)

            features = {"avg_blink_duration_ms": blink_duration, "avg_accel_ay": avg_accel}

            # Baseline deviation check
            deviations, deviation_flag = extractor.check_for_deviations(features, baseline) if hasattr(extractor, "check_for_deviations") else ({}, False)

            # HMM prediction
            state_prediction = predict_state([blink_duration, avg_accel], alert_model, drowsy_model)

            # Determine driver state
            if deviation_flag or state_prediction == "Drowsy":
                driver_status = "Danger"
            elif blink_duration < 300 or avg_accel > 0.3:
                driver_status = "Be careful"
            else:
                driver_status = "Looking good"

            # Update dashboard state
            state.update({
                "connected": handler.client.is_connected if handler.client else False,
                "duration": round(time.time() - start_time, 1),
                "status": driver_status,
                "metrics": {"avg_accel": avg_accel, "blink_duration": blink_duration, "nod_freq": nod_freq}
            })

            print(state)  # Replace with dashboard update logic

            # Save raw data for the session
            frame.to_csv(raw_file_path, mode="a", header=not os.path.exists(raw_file_path), index=False)

            queue.task_done()

    except asyncio.CancelledError:
        await handler.stop()
        bluetooth_task.cancel()
        try:
            await bluetooth_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())
