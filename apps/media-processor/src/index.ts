import amqp from 'amqplib';
import { config } from './config';
import { processMediaMessage } from './processor';

async function main() {
  console.log('🚀 Starting Media Processor Service...');
  try {
    const connection = await amqp.connect(config.rabbitmq.url);
    const channel = await connection.createChannel();
    
    await channel.assertQueue(config.rabbitmq.queueName, { durable: true });
    channel.prefetch(5); // 5件まで同時に処理
    
    console.log(`✅ Connected to RabbitMQ, waiting for jobs in '${config.rabbitmq.queueName}'.`);

    channel.consume(config.rabbitmq.queueName, async (msg) => {
      if (msg !== null) {
        const success = await processMediaMessage(msg);
        if (success) {
          channel.ack(msg);
        } else {
          // 再試行すべきエラーの場合、requeue=trueも検討
          channel.nack(msg, false, false); 
        }
      }
    });
  } catch (error) {
    console.error('❌ Failed to start Media Processor service:', error);
    process.exit(1);
  }
}

main();