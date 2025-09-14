import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", "5002"))
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
RAW_DATA_EXCHANGE = os.getenv("RAW_DATA_EXCHANGE", "raw_data_exchange")

# --- Analysis Parameters ---
SAMPLE_RATE = 256
NUM_EEG_CHANNELS = 8
ANALYSIS_WINDOW_SEC = 5.0 # 解析に使うデータの時間窓（秒）
ANALYSIS_INTERVAL_SEC = 5 # 解析を実行する間隔（秒）
BUFFER_MAX_SEC = 60 # 各ユーザーが保持する最大データ時間（秒）
CHANNEL_NAMES = ["Fp1", "Fp2", "F7", "F8", "T7", "T8", "P7", "P8"]