import base64
import io
import time
import threading
from datetime import datetime, timezone
import matplotlib
import numpy as np
import mne
from mne_connectivity import spectral_connectivity_epochs
from .data_store import user_data_store
from . import config

# Set Matplotlib backend to Agg for non-GUI environments
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def fig_to_base64(fig) -> str:
    """Converts a Matplotlib figure to a base64 encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=90)
    plt.close(fig) # Prevent memory leaks
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def perform_analysis(eeg_chunk_adc: np.ndarray) -> dict | None:
    """
    Performs PSD and coherence analysis on a chunk of EEG data.
    """
    try:
        # 1. Pre-process: Convert ADC values to Volts
        data_in_volts = (eeg_chunk_adc.T.astype(np.float64) - 2048.0) * (4.5 / 4096.0) * 1e-6
        
        info = mne.create_info(ch_names=config.CHANNEL_NAMES, sfreq=config.SAMPLE_RATE, ch_types="eeg")
        info.set_montage("standard_1020", on_missing="warn")
        raw = mne.io.RawArray(data_in_volts, info, verbose=False)

        # 2. Power Spectral Density (PSD) plot
        fig_psd = raw.compute_psd(fmin=1.0, fmax=40.0, n_fft=config.SAMPLE_RATE, verbose=False).plot(show=False)
        psd_b64 = fig_to_base64(fig_psd)

        # 3. Coherence plot (alpha band)
        epochs = mne.make_fixed_length_epochs(raw, duration=2.5, preload=True, verbose=False)
        con = spectral_connectivity_epochs(
            epochs, method="coh", sfreq=config.SAMPLE_RATE, fmin=8.0, fmax=13.0, faverage=True, verbose=False
        )
        fig_coh, _ = mne.viz.plot_connectivity_circle(
            con.get_data(output="dense")[..., 0], config.CHANNEL_NAMES, show=False, vmin=0.2
        )
        coh_b64 = fig_to_base64(fig_coh)

        return {
            "psd_image": psd_b64,
            "coherence_image": coh_b64,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        print(f"❌ Error during MNE analysis: {e}")
        return None

def analysis_worker_thread():
    """
    Background thread that periodically runs analysis for all active users.
    """
    print("🧠 Analysis worker thread started.")
    while True:
        time.sleep(config.ANALYSIS_INTERVAL_SEC)
        
        user_ids = user_data_store.get_all_user_ids()
        if not user_ids:
            continue
            
        print(f"Running analysis for {len(user_ids)} active users...")
        for user_id in user_ids:
            chunk = user_data_store.get_analysis_chunk(user_id)
            if chunk is not None:
                result = perform_analysis(chunk)
                if result:
                    user_data_store.update_analysis_result(user_id, result)
                    print(f"  - ✅ Analysis updated for user: {user_id}")