import path from 'path';
import { dbPool, minioClient } from './services';
import { config } from './config';
import type { Message } from 'amqplib';

/**
 * メッセージヘッダーから必須のメタデータを検証し、抽出します。
 * @param msg RabbitMQからのメッセージ
 * @returns 抽出されたメタデータ、または不正な場合はnull
 */
function validateAndExtractMetadata(msg: Message) {
  const headers = msg.properties.headers;
  const required = ['user_id', 'session_id', 'mimetype', 'original_filename'];
  
  for (const key of required) {
    if (!headers[key]) {
      console.error(`❌ Validation failed: Missing header '${key}' for message.`);
      return null;
    }
  }

  // タイムスタンプは種類によって必須項目が異なる
  const isImage = headers.mimetype.startsWith('image/');
  if (isImage && !headers.timestamp_utc) {
    console.error(`❌ Validation failed: Missing 'timestamp_utc' for image.`);
    return null;
  }
  const isAudio = headers.mimetype.startsWith('audio/');
  if (isAudio && (!headers.start_time_utc || !headers.end_time_utc)) {
    console.error(`❌ Validation failed: Missing 'start_time_utc' or 'end_time_utc' for audio.`);
    return null;
  }

  return {
    userId: headers.user_id,
    sessionId: headers.session_id,
    mimetype: headers.mimetype,
    originalFilename: headers.original_filename,
    timestamp: headers.timestamp_utc ? new Date(headers.timestamp_utc) : null,
    startTime: headers.start_time_utc ? new Date(headers.start_time_utc) : null,
    endTime: headers.end_time_utc ? new Date(headers.end_time_utc) : null,
  };
}

/**
 * メディアメッセージを処理し、MinIOとPostgreSQLに永続化します。
 * @param msg RabbitMQからのメッセージ
 * @returns 処理が成功し、ACKしてよい場合はtrue、それ以外はfalse
 */
export async function processMediaMessage(msg: Message): Promise<boolean> {
  const metadata = validateAndExtractMetadata(msg);
  if (!metadata) {
    return true; // 不正なメッセージはACKして破棄し、キューをブロックしない
  }

  const { userId, sessionId, mimetype, originalFilename, timestamp, startTime, endTime } = metadata;
  const compressedData = msg.content;
  
  // 1. MinIOのオブジェクトキーを生成
  const fileExtension = path.extname(originalFilename);
  const timestampForPath = (timestamp || startTime || new Date()).getTime();
  const objectId = `media/${userId}/${sessionId}/${timestampForPath}_${path.basename(originalFilename, fileExtension)}${fileExtension}.zst`;

  // 2. MinIOに圧縮データをアップロード
  try {
    await minioClient.putObject(config.minio.bucketName, objectId, compressedData, {
      'Content-Type': 'application/zstd',
      'X-Original-Mimetype': mimetype,
    });
  } catch (error) {
    console.error(`❌ Failed to upload object ${objectId} to MinIO:`, error);
    return false; // MinIOエラーは再試行の価値があるためNACKする
  }

  // 3. PostgreSQLにメタデータを書き込み
  const client = await dbPool.connect();
  try {
    if (mimetype.startsWith('image/') && timestamp) {
      const query = 'INSERT INTO images (object_id, user_id, session_id, timestamp_utc) VALUES ($1, $2, $3, $4)';
      await client.query(query, [objectId, userId, sessionId, timestamp]);
    } else if (mimetype.startsWith('audio/') && startTime && endTime) {
      const query = 'INSERT INTO audio_clips (object_id, user_id, session_id, start_time, end_time) VALUES ($1, $2, $3, $4, $5)';
      await client.query(query, [objectId, userId, sessionId, startTime, endTime]);
    } else {
      console.warn(`⚠️ Unhandled mimetype '${mimetype}' for object ${objectId}. Skipping DB insert.`);
    }
  } catch (error) {
    console.error(`❌ Failed to insert metadata for ${objectId} into PostgreSQL:`, error);
    // DBエラーも再試行の価値があるためNACKする
    // TODO: ここでMinIOにアップロードしたオブジェクトを削除する補償トランザクションを検討
    return false;
  } finally {
    client.release();
  }

  console.log(`✅ Successfully processed media object: ${objectId}`);
  return true; // 全て成功したのでACK
}