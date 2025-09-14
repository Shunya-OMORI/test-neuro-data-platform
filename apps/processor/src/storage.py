import io
import psycopg
from minio import Minio
from . import config

minio_client = Minio(
    config.MINIO_ENDPOINT,
    access_key=config.MINIO_ACCESS_KEY,
    secret_key=config.MINIO_SECRET_KEY,
    secure=config.MINIO_SECURE,
)

def ensure_minio_bucket_exists():
    if not minio_client.bucket_exists(config.MINIO_BUCKET_NAME):
        minio_client.make_bucket(config.MINIO_BUCKET_NAME)
        print(f"Bucket '{config.MINIO_BUCKET_NAME}' created.")

def upload_to_minio(object_name: str, data: bytes) -> str:
    result = minio_client.put_object(
        config.MINIO_BUCKET_NAME,
        object_name,
        io.BytesIO(data),
        len(data),
        content_type="application/zstd", # 圧縮データを格納
    )
    return result.etag

def get_db_connection():
    return psycopg.connect(config.DATABASE_URL)

def insert_raw_data_metadata_to_db(db_conn, metadata: dict):
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_data_objects (
                object_id, user_id, device_id, start_time, end_time, data_type, created_at
            ) VALUES (
                %(object_id)s, %(user_id)s, %(device_id)s, %(start_time)s, %(end_time)s, %(data_type)s, NOW()
            )
            """,
            metadata,
        )
    db_conn.commit()

