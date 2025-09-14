import amqp from 'amqplib';
import dotenv from 'dotenv';
import { processLinkJob } from './linker';

dotenv.config();

const RABBITMQ_URL = process.env.RABBITMQ_URL!;
const DATALINKER_QUEUE = process.env.DATALINKER_QUEUE!;

async function main() {
  console.log('🚀 Starting DataLinker Service...');
  try {
    const connection = await amqp.connect(RABBITMQ_URL);
    const channel = await connection.createChannel();
    
    await channel.assertQueue(DATALINKER_QUEUE, { durable: true });
    channel.prefetch(1); // Process one message at a time
    
    console.log(`✅ Connected to RabbitMQ, waiting for jobs in '${DATALINKER_QUEUE}'.`);

    channel.consume(DATALINKER_QUEUE, async (msg) => {
      if (msg !== null) {
        const jobPayload = JSON.parse(msg.content.toString());
        console.log(`\n[${new Date().toISOString()}] Received linking job for session: ${jobPayload.session_id}`);
        try {
          await processLinkJob(jobPayload);
          channel.ack(msg);
        } catch (error) {
          console.error('  - Job failed. Message will be requeued or dead-lettered.');
          // Nack the message; requeue=false to avoid infinite loops for poison pills
          // For production, a dead-letter exchange is recommended.
          channel.nack(msg, false, false); 
        }
      }
    });

  } catch (error) {
    console.error('❌ Failed to start DataLinker service:', error);
    process.exit(1);
  }
}

main();