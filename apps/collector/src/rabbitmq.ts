import amqp, { Channel, Connection } from 'amqplib';
import { EventEmitter } from 'events';

const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://guest:guest@localhost:5672';
const RAW_DATA_EXCHANGE = process.env.RAW_DATA_EXCHANGE || 'raw_data_exchange';
const MEDIA_PROCESSING_QUEUE = process.env.MEDIA_PROCESSING_QUEUE || 'media_processing_queue';

let connection: Connection | null = null;
let channel: Channel | null = null;
const connectionEmitter = new EventEmitter();

/**
 * Connects to RabbitMQ with an exponential backoff retry mechanism.
 */
export async function connectRabbitMQ() {
  let attempts = 0;
  while (true) {
    try {
      console.log(`[RabbitMQ] Attempting to connect... (Attempt ${attempts + 1})`);
      connection = await amqp.connect(RABBITMQ_URL);

      connection.on('close', () => {
        console.error('[RabbitMQ] Connection closed. Reconnecting in 5 seconds...');
        channel = null;
        connection = null;
        setTimeout(connectRabbitMQ, 5000);
      });
      connection.on('error', (err) => {
        console.error('[RabbitMQ] Connection error:', err.message);
      });

      console.log('[RabbitMQ] ✅ Connection successful.');
      channel = await connection.createChannel();
      console.log('[RabbitMQ] ✅ Channel created.');

      // Assert exchanges and queues to ensure they exist
      await channel.assertExchange(RAW_DATA_EXCHANGE, 'fanout', { durable: true });
      await channel.assertQueue(MEDIA_PROCESSING_QUEUE, { durable: true });

      console.log(`[RabbitMQ] ✅ Exchange "${RAW_DATA_EXCHANGE}" and Queue "${MEDIA_PROCESSING_QUEUE}" are ready.`);
      connectionEmitter.emit('ready');
      break;
    } catch (err: any) {
      console.error(`[RabbitMQ] ❌ Connection failed: ${err.message}`);
      attempts++;
      const delay = Math.min(30000, 2 ** attempts * 1000);
      console.log(`[RabbitMQ] Retrying in ${delay / 1000} seconds...`);
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }
}

/**
 * Checks if the RabbitMQ channel is available.
 * @returns {boolean} True if the channel is ready, false otherwise.
 */
export const isReady = () => !!channel;

/**
 * Publishes a message to the raw data fanout exchange.
 * @param {Buffer} payload - The binary payload.
 * @param {object} headers - AMQP message headers, e.g., { user_id }.
 */
export function publishSensorData(payload: Buffer, headers: Record<string, any>) {
  if (!channel) {
    console.warn('[RabbitMQ] Cannot publish sensor data: channel is not available.');
    return;
  }
  channel.publish(RAW_DATA_EXCHANGE, '', payload, {
    persistent: true,
    headers,
  });
}

/**
 * Sends a message directly to the media processing queue.
 * @param {Buffer} payload - The binary payload of the media file.
 * @param {object} headers - AMQP message headers, e.g., { user_id, session_id, mimetype }.
 */
export function publishMediaData(payload: Buffer, headers: Record<string, any>) {
  if (!channel) {
    console.warn('[RabbitMQ] Cannot publish media data: channel is not available.');
    return;
  }
  channel.sendToQueue(MEDIA_PROCESSING_QUEUE, payload, {
    persistent: true,
    headers,
  });
}
