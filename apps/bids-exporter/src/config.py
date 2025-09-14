import os
from dotenv import load_dotenv

load_dotenv()

# Server Configuration
PORT = int(os.getenv("PORT", "5004"))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# BIDS Exporter Configuration
BIDS_OUTPUT_DIR = os.getenv("BIDS_OUTPUT_DIR", "/bids_output")

# Validate that essential variables are set
if not all([DATABASE_URL, MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET]):
    raise ValueError("One or more essential environment variables are not set.")