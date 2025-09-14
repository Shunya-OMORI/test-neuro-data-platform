import dotenv from 'dotenv';

dotenv.config();

export const config = {
  db: {
    connectionString: process.env.DATABASE_URL!,
  },
  rabbitmq: {
    url: process.env.RABBITMQ_URL!,
    queueName: process.env.MEDIA_QUEUE_NAME || 'media_processing_queue',
  },
  minio: {
    endPoint: process.env.MINIO_ENDPOINT!,
    port: parseInt(process.env.MINIO_PORT!, 10),
    useSSL: process.env.MINIO_USE_SSL === 'true',
    accessKey: process.env.MINIO_ACCESS_KEY!,
    secretKey: process.env.MINIO_SECRET_KEY!,
    bucketName: process.env.MINIO_BUCKET!,
  },
};