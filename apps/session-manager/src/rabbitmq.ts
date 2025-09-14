import amqp from 'amqplib';
import dotenv from 'dotenv';

dotenv.config();

const RABBITMQ_URL = process.env.RABBITMQ_URL!;
const DATALINKER_QUEUE = process.env.DATALINKER_QUEUE!;

let channel: amqp.Channel | null = null;

export async function connectRabbitMQ() {
  try {
    const connection = await amqp.connect(RABBITMQ_URL);
    channel = await connection.createChannel();
    await channel.assertQueue(DATALINKER_QUEUE, { durable: true });
    console.log('✅ RabbitMQ connected and queue asserted:', DATALINKER_QUEUE);
  } catch (error) {
    console.error('❌ Failed to connect to RabbitMQ:', error);
    process.exit(1);
  }
}

export function enqueueDataLinkJob(sessionData: any): boolean {
  if (!channel) {
    console.error('❌ Cannot enqueue job: RabbitMQ channel is not available.');
    return false;
  }
  const message = Buffer.from(JSON.stringify(sessionData));
  return channel.sendToQueue(DATALINKER_QUEUE, message, { persistent: true });
}
