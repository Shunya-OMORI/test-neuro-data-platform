from contextlib import contextmanager
import psycopg
from minio import Minio
from . import config

# --- Database Connection ---
@contextmanager
def get_db_connection():
    """Provides a transactional database connection."""
    conn = psycopg.connect(config.DATABASE_URL, row_factory=psycopg.rows.dict_row)
    try:
        yield conn
    finally:
        conn.close()

# --- MinIO Connection ---
def get_minio_client():
    """Initializes and returns a MinIO client instance."""
    return Minio(
        config.MINIO_ENDPOINT,
        access_key=config.MINIO_ACCESS_KEY,
        secret_key=config.MINIO_SECRET_KEY,
        secure=config.MINIO_SECURE
    )

# --- Data Fetching Functions ---
def get_session_info_for_experiment(conn: psycopg.Connection, experiment_id: str):
    """Fetches all session details for a given experiment."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM sessions WHERE experiment_id = %s ORDER BY start_time ASC",
            (experiment_id,)
        )
        return cur.fetchall()

def get_object_metadata_for_session(conn: psycopg.Connection, session_id: str):
    """Fetches all raw data object metadata for a session, ordered by time."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT o.*
            FROM raw_data_objects o
            JOIN session_object_links l ON o.object_id = l.object_id
            WHERE l.session_id = %s
            ORDER BY o.start_time ASC
            """,
            (session_id,)
        )
        return cur.fetchall()

def download_object_from_minio(minio_client: Minio, object_key: str):
    """Downloads a single object from MinIO and returns its content as bytes."""
    response = minio_client.get_object(config.MINIO_BUCKET, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()

def get_events_for_session(conn: psycopg.Connection, session_id: str):
    """Fetches event data for a given session, ordered by onset time."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM events WHERE session_id = %s ORDER BY onset_s ASC",
            (session_id,)
        )
        return cur.fetchall()
