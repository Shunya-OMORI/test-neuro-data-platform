import pika
import zstandard
import numpy as np
from .data_store import user_data_store
from . import config

# Sensor data format, matching the firmware and processor
SENSOR_DATA_DTYPE = np.dtype([("eeg", "<u2", (config.NUM_EEG_CHANNELS,)), ("rest", "V45")])
HEADER_SIZE = 18

def start_consumer_thread():
    """
    Connects to RabbitMQ and consumes messages, adding data to the UserDataStore.
    """
    print("🐇 RabbitMQ consumer thread started.")
    connection = pika.BlockingConnection(pika.URLParameters(config.RABBITMQ_URL))
    channel = connection.channel()

    # Declare fanout exchange
    channel.exchange_declare(exchange=config.RAW_DATA_EXCHANGE, exchange_type='fanout', durable=True)
    
    # Create an exclusive, non-durable queue for this instance
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    # Bind the queue to the exchange
    channel.queue_bind(exchange=config.RAW_DATA_EXCHANGE, queue=queue_name)

    def callback(ch, method, properties, body):
        try:
            user_id = properties.headers.get("user_id")
            if not user_id:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            dctx = zstandard.ZstdDecompressor()
            decompressed_data = dctx.decompress(body)
            
            if len(decompressed_data) <= HEADER_SIZE:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            sensor_bytes = decompressed_data[HEADER_SIZE:]
            num_samples = len(sensor_bytes) // SENSOR_DATA_DTYPE.itemsize
            
            if num_samples > 0:
                structured_array = np.frombuffer(sensor_bytes, dtype=SENSOR_DATA_DTYPE, count=num_samples)
                eeg_samples = structured_array["eeg"]
                user_data_store.add_samples(user_id, eeg_samples)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"❌ Error in RabbitMQ callback: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()