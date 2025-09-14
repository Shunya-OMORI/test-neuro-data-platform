import { Router } from 'express';
import multer from 'multer';
import { parse } from 'csv-parse';
import db from './db';
import { enqueueDataLinkJob } from './rabbitmq';

const upload = multer({ storage: multer.memoryStorage() });
const router = Router();

// --- Experiment Management ---
router.post('/experiments', async (req, res) => {
  // ... (Implementation for creating experiments)
  res.status(501).send('Not Implemented');
});

router.get('/experiments', async (req, res) => {
  // ... (Implementation for listing experiments)
  res.status(501).send('Not Implemented');
});


// --- Session Finalization ---
const sessionUpload = upload.fields([
  { name: 'metadata', maxCount: 1 },
  { name: 'events_file', maxCount: 1 },
]);

router.post('/sessions/end', sessionUpload, async (req, res) => {
  const files = req.files as { [fieldname: string]: Express.Multer.File[] };
  const metadataFile = files?.['metadata']?.[0];
  const eventsFile = files?.['events_file']?.[0];

  if (!metadataFile) {
    return res.status(400).json({ error: 'Metadata part is missing.' });
  }

  const client = await db.connect();
  try {
    const sessionData = JSON.parse(metadataFile.buffer.toString('utf-8'));

    await client.query('BEGIN');

    // 1. Insert session metadata
    const sessionInsertQuery = `
      INSERT INTO sessions (session_id, user_id, experiment_id, device_id, start_time, end_time, session_type)
      VALUES ($1, $2, $3, $4, $5, $6, $7)
    `;
    await client.query(sessionInsertQuery, [
      sessionData.session_id,
      sessionData.user_id,
      sessionData.experiment_id,
      sessionData.device_id,
      sessionData.start_time,
      sessionData.end_time,
      sessionData.session_type,
    ]);

    // 2. Parse and insert events if the file exists
    if (eventsFile) {
      const eventInsertQuery = `
        INSERT INTO events (session_id, onset_s, duration_s, description, value)
        VALUES ($1, $2, $3, $4, $5)
      `;
      const parser = parse(eventsFile.buffer, {
        columns: true,
        skip_empty_lines: true,
      });
      for await (const record of parser) {
        await client.query(eventInsertQuery, [
          sessionData.session_id,
          parseFloat(record.onset),
          parseFloat(record.duration),
          record.description,
          record.value,
        ]);
      }
    }
    
    // 3. Enqueue job for DataLinker
    const jobEnqueued = enqueueDataLinkJob(sessionData);
    if (!jobEnqueued) {
      throw new Error('Failed to enqueue DataLinker job.');
    }

    await client.query('COMMIT');
    res.status(200).json({ status: 'Session finalized and linking job enqueued.' });

  } catch (error: any) {
    await client.query('ROLLBACK');
    console.error('❌ Failed to process session finalization:', error);
    res.status(500).json({ error: 'Failed to process session.', details: error.message });
  } finally {
    client.release();
  }
});

export default router;
