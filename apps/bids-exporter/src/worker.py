import os
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timezone
import numpy as np
import zstandard
import mne
from mne_bids import BIDSPath, write_raw_bids
from . import config, storage

# Sensor data format, matching the firmware and processor
SENSOR_DATA_DTYPE = np.dtype(
    [
        ("eeg", "<u2", (8,)),
        ("accel", "<f4", (3,)),
        ("gyro", "<f4", (3,)),
        ("trig", "u1"),
        ("imp", "i1", (8,)),
        ("esp_time", "<u4"),
    ]
)
HEADER_SIZE = 18

def parse_raw_data(decompressed_data: bytes):
    """Parses decompressed binary data into a structured numpy array."""
    if len(decompressed_data) <= HEADER_SIZE:
        return None, np.array([])

    device_id_bytes = decompressed_data[:17]
    device_id = device_id_bytes.decode("utf-8").strip("\x00")
    
    sensor_bytes = decompressed_data[HEADER_SIZE:]
    num_samples = len(sensor_bytes) // SENSOR_DATA_DTYPE.itemsize
    
    if num_samples == 0:
        return device_id, np.array([])
        
    structured_array = np.frombuffer(sensor_bytes, dtype=SENSOR_DATA_DTYPE, count=num_samples)
    return device_id, structured_array

def run_bids_export_task(task_id: str, experiment_id: str, task_registry: dict):
    """
    Main function for the background BIDS export task.
    """
    bids_root_path = os.path.join(config.BIDS_OUTPUT_DIR, task_id)
    zip_filename = f"experiment_{experiment_id}_{task_id}.zip"
    zip_filepath = os.path.join(config.BIDS_OUTPUT_DIR, zip_filename)

    try:
        task_registry[task_id] = {"status": "running", "progress": 0, "message": "Initializing..."}

        minio_client = storage.get_minio_client()
        with storage.get_db_connection() as conn:
            # 1. Get all sessions for the experiment
            sessions = storage.get_session_info_for_experiment(conn, experiment_id)
            if not sessions:
                raise ValueError(f"No sessions found for experiment ID: {experiment_id}")

            total_sessions = len(sessions)
            for i, session in enumerate(sessions):
                progress = int((i / total_sessions) * 100)
                session_id = session["session_id"]
                task_registry[task_id].update({
                    "progress": progress,
                    "message": f"Processing session {i+1}/{total_sessions}: {session_id}",
                })

                # 2. Get all object metadata for the current session
                objects_meta = storage.get_object_metadata_for_session(conn, session_id)
                if not objects_meta:
                    print(f"Warning: No data objects found for session {session_id}. Skipping.")
                    continue

                # 3. Download all objects in parallel
                object_keys = [meta["object_id"] for meta in objects_meta]
                with ThreadPoolExecutor() as executor:
                    compressed_chunks = list(executor.map(
                        lambda key: storage.download_object_from_minio(minio_client, key),
                        object_keys
                    ))
                
                # 4. Stitch, decompress, and parse
                full_compressed_data = b"".join(compressed_chunks)
                dctx = zstandard.ZstdDecompressor()
                decompressed_data = dctx.decompress(full_compressed_data)
                device_id, parsed_data = parse_raw_data(decompressed_data)

                if parsed_data.size == 0:
                    print(f"Warning: Parsed data is empty for session {session_id}. Skipping.")
                    continue
                
                # 5. Create MNE Raw object
                # Assuming a fixed sample rate. In a real scenario, this might come from metadata.
                sfreq = 256.0
                ch_names = ["Fp1", "Fp2", "F7", "F8", "T7", "T8", "P7", "P8"]
                ch_types = ["eeg"] * 8
                
                # Convert ADC values to Volts
                eeg_data_volts = (parsed_data["eeg"].astype(np.float64) - 2048.0) * (4.5 / 4096.0) * 1e-6
                
                info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
                info.set_montage("standard_1020", on_missing="warn")
                raw = mne.io.RawArray(eeg_data_volts.T, info)

                # Use the session start time as the measurement date
                meas_date = session["start_time"].replace(tzinfo=timezone.utc)
                raw.set_meas_date(meas_date)

                # 6. Get and add events as annotations
                events = storage.get_events_for_session(conn, session_id)
                if events:
                    annotations = mne.Annotations(
                        onset=[e["onset_s"] for e in events],
                        duration=[e["duration_s"] for e in events],
                        description=[e["description"] for e in events]
                    )
                    raw.set_annotations(annotations)
                
                # 7. Write to BIDS format
                bids_path = BIDSPath(
                    subject=session["user_id"],
                    session=meas_date.strftime("%Y%m%d"),
                    task=session["session_type"],
                    root=bids_root_path
                )
                write_raw_bids(raw, bids_path, overwrite=True, verbose=False)

        # 8. Zip the output directory
        task_registry[task_id].update({"progress": 95, "message": "Compressing dataset..."})
        shutil.make_archive(
            base_name=os.path.join(config.BIDS_OUTPUT_DIR, f"experiment_{experiment_id}_{task_id}"),
            format='zip',
            root_dir=bids_root_path
        )
        shutil.rmtree(bids_root_path) # Clean up the uncompressed directory

        task_registry[task_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Export completed successfully.",
            "result_file": zip_filename,
        }

    except Exception as e:
        print(f"Error in BIDS export task {task_id}: {e}")
        task_registry[task_id] = {"status": "failed", "message": str(e)}
        if os.path.exists(bids_root_path):
            shutil.rmtree(bids_root_path)