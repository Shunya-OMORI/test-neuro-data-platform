import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# RabbitMQ Configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
PROCESSING_QUEUE = os.getenv("PROCESSING_QUEUE", "processing_queue")

# PostgreSQL Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://admin:password@localhost:5432/neuro_data")

# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "raw-data")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"
