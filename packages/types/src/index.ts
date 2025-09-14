// --- Enums for specific, controlled vocabularies ---

/**
 * Defines the type of a measurement session.
 */
export enum SessionType {
  Calibration = 'calibration',
  Main = 'main',
}

/**
 * Tracks the status of the DataLinker background job for a session.
 */
export enum LinkStatus {
  Pending = 'pending',
  Processing = 'processing',
  Completed = 'completed',
  Failed = 'failed',
}

// --- Type definitions for core data structures ---

/**
 * Represents the metadata for a single experiment.
 */
export type Experiment = {
  experiment_id: string; // UUID
  name: string;
  description: string | null;
  created_at: Date;
};

/**
 * Represents the metadata for a single recording session.
 * This is the primary payload sent from the Session Manager to the DataLinker.
 */
export type Session = {
  session_id: string;
  user_id: string;
  experiment_id: string; // UUID
  device_id: string | null;
  start_time: Date;
  end_time: Date | null;
  session_type: SessionType;
  link_status: LinkStatus;
};

/**
 * Represents a single event marker within a session (e.g., from a CSV file).
 */
export type Event = {
  session_id: string;
  onset_s: number;      // Onset time in seconds from session start
  duration_s: number;   // Duration of the event in seconds
  description: string | null;
  value: string | null;   // e.g., 'target', 'nontarget'
};

/**
 * Represents the metadata for a raw data object stored in MinIO.
 */
export type RawDataObject = {
  object_id: string;
  user_id: string;
  device_id: string | null;
  start_time: Date;
  end_time: Date;
  data_type: 'eeg' | 'imu' | string; // Allows for future expansion
};

/**
 * Represents the metadata for an image file stored in MinIO.
 */
export type ImageObject = {
  object_id: string;
  user_id: string;
  session_id: string;
  experiment_id: string | null;
  timestamp_utc: Date;
};

/**
 * Represents the metadata for an audio clip file stored in MinIO.
 */
export type AudioClipObject = {
  object_id: string;
  user_id: string;
  session_id: string;
  experiment_id: string | null;
  start_time: Date;
  end_time: Date;
};