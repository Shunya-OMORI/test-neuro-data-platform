import { Router } from 'express';
import multer from 'multer';
import { getRabbitMQChannel } from './rabbitmq';

const upload = multer({ storage: multer.memoryStorage() });
const router = Router();

// センサーデータ受信用エンドポイント (/api/v1/data)
router.post('/data', (req, res) => {
  const channel = getRabbitMQChannel();
  if (!channel) {
    return res.status(503).json({ error: 'Message broker not available' });
  }

  const { user_id, payload_base64 } = req.body;
  if (typeof user_id !== 'string' || typeof payload_base64 !== 'string') {
    return res.status(400).json({ error: 'user_id and payload_base64 are required' });
  }

  try {
    const payloadBuffer = Buffer.from(payload_base64, 'base64');
    const headers = { user_id };

    // Fanout Exchangeに発行 (ルーティングキーは不要)
    channel.publish('raw_data_exchange', '', payloadBuffer, { persistent: true, headers });
    
    res.status(202).json({ status: 'accepted' });
  } catch (error) {
    console.error('Error processing sensor data:', error);
    res.status(500).json({ error: 'Failed to process sensor data' });
  }
});

// メディアデータ受信用エンドポイント (/api/v1/media)
// 'file' という名前の単一ファイルを受け付ける
router.post('/media', upload.single('file'), (req, res) => {
  const channel = getRabbitMQChannel();
  if (!channel) {
    return res.status(503).json({ error: 'Message broker not available' });
  }

  const {
    user_id,
    session_id,
    original_filename,
    mimetype,
    timestamp_utc,   // for images
    start_time_utc,  // for audio
    end_time_utc,    // for audio
  } = req.body;
  
  const file = req.file;

  if (!file || !user_id || !session_id || !original_filename || !mimetype) {
    return res.status(400).json({ error: 'Missing required fields or file for media upload.' });
  }

  try {
    const headers = {
      user_id,
      session_id,
      original_filename,
      mimetype,
      // タイムスタンプが存在する場合のみヘッダーに含める
      ...(timestamp_utc && { timestamp_utc }),
      ...(start_time_utc && { start_time_utc }),
      ...(end_time_utc && { end_time_utc }),
    };

    // media_processing_queueに直接送信
    channel.sendToQueue('media_processing_queue', file.buffer, { persistent: true, headers });

    res.status(202).json({ status: 'accepted' });
  } catch (error) {
    console.error('Error processing media data:', error);
    res.status(500).json({ error: 'Failed to process media data' });
  }
});

export default router;

