import pika
import time
import uuid
from datetime import datetime, timezone
from . import config, parser, storage

def main():
    print("🚀 Starting Processor Service...")
    storage.ensure_minio_bucket_exists()
    db_conn = storage.get_db_connection()
    print("✅ Connected to PostgreSQL.")

    connection = pika.BlockingConnection(pika.URLParameters(config.RABBITMQ_URL))
    channel = connection.channel()

    # Fanout Exchangeにバインドするための専用キューを作成
    queue_result = channel.queue_declare(queue='', exclusive=True)
    queue_name = queue_result.method.queue
    channel.queue_bind(exchange='raw_data_exchange', queue=queue_name)
    channel.basic_qos(prefetch_count=1)
    print(f"✅ Bound to 'raw_data_exchange', waiting for messages.")

    def callback(ch, method, properties, body):
        server_received_time = datetime.now(timezone.utc)
        print(f"[{server_received_time.isoformat()}] Received message.")
        try:
            user_id = properties.headers.get("user_id", "unknown_user")
            
            # データをパースしてタイムスタンプとデバイスIDを抽出
            device_id, _, timestamps = parser.decompress_and_parse(body, server_received_time)
            if not timestamps:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            start_time = timestamps[0]
            end_time = timestamps[-1]

            # MinIOオブジェクトキーを生成
            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)
            unique_id = uuid.uuid4().hex[:8]
            object_id = f"eeg/{user_id}/{start_ms}-{end_ms}_{device_id.replace(':', '')}_{unique_id}.zst"

            # MinIOに圧縮済みデータをアップロード
            storage.upload_to_minio(object_id, body)
            
            # PostgreSQLにメタデータを挿入
            metadata = {
                "object_id": object_id, "user_id": user_id, "device_id": device_id,
                "start_time": start_time, "end_time": end_time, "data_type": "eeg",
            }
            storage.insert_raw_data_metadata_to_db(db_conn, metadata)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"  - Successfully processed message for device {device_id}.")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            time.sleep(5)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()
        db_conn.close()

if __name__ == "__main__":
    main()

