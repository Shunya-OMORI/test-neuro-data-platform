import { Pool } from 'pg';
import * as Minio from 'minio';
import { config } from './config';

// PostgreSQL接続プール
export const dbPool = new Pool({
  connectionString: config.db.connectionString,
});

dbPool.on('error', (err) => {
  console.error('Unexpected error on idle PostgreSQL client', err);
  process.exit(-1);
});

// MinIOクライアント
export const minioClient = new Minio.Client({
  endPoint: config.minio.endPoint,
  port: config.minio.port,
  useSSL: config.minio.useSSL,
  accessKey: config.minio.accessKey,
  secretKey: config.minio.secretKey,
});