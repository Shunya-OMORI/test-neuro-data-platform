import threading
from collections import deque
import numpy as np
from . import config

class UserDataStore:
    """
    Manages in-memory data buffers and analysis results for all users
    in a thread-safe manner.
    """
    def __init__(self):
        self._data_buffers = {}
        self._latest_results = {}
        self._lock = threading.Lock()

    def _get_user_buffer(self, user_id: str) -> deque:
        """Initializes a buffer for a user if it doesn't exist."""
        if user_id not in self._data_buffers:
            max_len = int(config.SAMPLE_RATE * config.BUFFER_MAX_SEC)
            self._data_buffers[user_id] = deque(maxlen=max_len)
        return self._data_buffers[user_id]

    def add_samples(self, user_id: str, eeg_samples: np.ndarray):
        """Adds new EEG samples to a user's buffer."""
        with self._lock:
            buffer = self._get_user_buffer(user_id)
            for sample in eeg_samples:
                buffer.append(sample)

    def get_analysis_chunk(self, user_id: str) -> np.ndarray | None:
        """Gets the most recent chunk of data for analysis."""
        with self._lock:
            buffer = self._get_user_buffer(user_id)
            required_samples = int(config.SAMPLE_RATE * config.ANALYSIS_WINDOW_SEC)
            if len(buffer) < required_samples:
                return None
            
            # Return a copy of the most recent data
            return np.array(list(buffer)[-required_samples:])

    def get_all_user_ids(self) -> list[str]:
        """Returns a list of all user IDs currently in the store."""
        with self._lock:
            return list(self._data_buffers.keys())

    def update_analysis_result(self, user_id: str, result: dict):
        """Stores the latest analysis result for a user."""
        with self._lock:
            self._latest_results[user_id] = result

    def get_analysis_result(self, user_id: str) -> dict | None:
        """Retrieves the latest analysis result for a user."""
        with self._lock:
            return self._latest_results.get(user_id)

# Create a global instance to be shared across the application
user_data_store = UserDataStore()