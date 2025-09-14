import struct
from datetime import datetime, timedelta, timezone
import numpy as np
import zstandard

# マイコン側の SensorData 構造体に対応
ESP32_SENSOR_DATA_DTYPE = np.dtype(
    [
        ("eeg", "<u2", (8,)),
        ("accel", "<f4", (3,)),
        ("gyro", "<f4", (3,)),
        ("trig", "u1"),
        ("imp", "i1", (8,)),
        ("esp_micros", "<u4"),
    ]
)
ESP32_SENSOR_SIZE = ESP32_SENSOR_DATA_DTYPE.itemsize

# マイコン側の PacketHeader 構造体に対応
PACKET_HEADER_SIZE = 18

DEVICE_BOOT_TIME_ESTIMATES: dict[str, datetime] = {}

def parse_raw_data(raw_bytes: bytes, server_received_time: datetime) -> tuple[str, np.ndarray, list[datetime]]:
    if len(raw_bytes) < PACKET_HEADER_SIZE:
        return "unknown_device", np.array([]), []

    header_bytes = raw_bytes[:PACKET_HEADER_SIZE]
    device_id = header_bytes.split(b'\x00', 1)[0].decode('utf-8', 'ignore')

    payload_bytes = raw_bytes[PACKET_HEADER_SIZE:]
    num_samples = len(payload_bytes) // ESP32_SENSOR_SIZE
    if num_samples == 0:
        return device_id, np.array([]), []

    structured_array = np.frombuffer(payload_bytes, dtype=ESP32_SENSOR_DATA_DTYPE, count=num_samples)
    
    esp_micros_arr = structured_array["esp_micros"]
    latest_esp_micros = int(esp_micros_arr[-1])
    esp_boot_time_server = server_received_time - timedelta(microseconds=latest_esp_micros)
    
    timestamps = [
        esp_boot_time_server + timedelta(microseconds=int(us))
        for us in esp_micros_arr.tolist()
    ]
    return device_id, structured_array, timestamps

def decompress_and_parse(compressed_body: bytes, server_received_time: datetime) -> tuple[str, np.ndarray, list[datetime]]:
    try:
        raw_bytes = zstandard.ZstdDecompressor().decompress(compressed_body)
        return parse_raw_data(raw_bytes, server_received_time)
    except zstandard.ZstdError as e:
        print(f"Error: Zstd decompression failed: {e}")
        return "unknown_device", np.array([]), []
    except Exception as e:
        print(f"Error: Failed to parse raw data: {e}")
        return "unknown_device", np.array([]), []

