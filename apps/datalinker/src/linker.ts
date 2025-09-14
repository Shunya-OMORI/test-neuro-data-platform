import db from './db';

// This function contains the core business logic for a single linking job.
export async function processLinkJob(sessionData: any) {
  const { session_id, user_id, experiment_id, start_time, end_time } = sessionData;
  const client = await db.connect();

  try {
    await client.query('BEGIN');
    
    // 1. Mark session as 'processing'
    await client.query(
      `UPDATE sessions SET link_status = 'processing' WHERE session_id = $1`,
      [session_id]
    );

    // 2. Find overlapping raw_data_objects
    const findObjectsQuery = `
      SELECT object_id FROM raw_data_objects
      WHERE user_id = $1
      AND start_time < $2 -- Object starts before session ends
      AND end_time > $3   -- Object ends after session starts
    `;
    const res = await client.query(findObjectsQuery, [user_id, end_time, start_time]);
    const objectIds = res.rows.map(row => row.object_id);

    // 3. Insert links into the junction table
    const insertLinkQuery = `
      INSERT INTO session_object_links (session_id, object_id) VALUES ($1, $2)
      ON CONFLICT (session_id, object_id) DO NOTHING
    `;
    for (const objectId of objectIds) {
      await client.query(insertLinkQuery, [session_id, objectId]);
    }
    console.log(`  - Linked ${objectIds.length} sensor data objects to session ${session_id}.`);

    // 4. Update experiment_id for media files within the session
    const updateImagesQuery = `UPDATE images SET experiment_id = $1 WHERE session_id = $2`;
    const imgRes = await client.query(updateImagesQuery, [experiment_id, session_id]);
    console.log(`  - Updated experiment_id for ${imgRes.rowCount} images.`);

    const updateAudioQuery = `UPDATE audio_clips SET experiment_id = $1 WHERE session_id = $2`;
    const audRes = await client.query(updateAudioQuery, [experiment_id, session_id]);
    console.log(`  - Updated experiment_id for ${audRes.rowCount} audio clips.`);
    
    // 5. Mark session as 'completed'
    await client.query(
      `UPDATE sessions SET link_status = 'completed' WHERE session_id = $1`,
      [session_id]
    );

    await client.query('COMMIT');
    console.log(`✅ Successfully processed linking job for session ${session_id}.`);

  } catch (error) {
    await client.query('ROLLBACK');
    console.error(`❌ Error processing job for session ${session_id}:`, error);
    // Mark as failed to prevent retries on permanent errors
    await client.query(
      `UPDATE sessions SET link_status = 'failed' WHERE session_id = $1`,
      [session_id]
    );
    // Re-throw to signal the main consumer to nack the message
    throw error; 
  } finally {
    client.release();
  }
}