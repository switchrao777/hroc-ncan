"""
decoder_2013.py
---------------
Decoder for Animal 16/17 (2013 format) Elizan III MyISAM .MYD binary files.

Format confirmed via hex inspection + Elizan III manual §4.5.3:
  - int16 signed, LITTLE-endian
  - 1,444 bytes per record
  - 3 fragments per record (frag0, frag1, frag2)
  - frag1 starts at byte offset 204 within each record (the ERP window)
  - Channel layout: BLOCK (ch1 = first half of samples, ch2 = second half)
  - ad2uV = 2.441406
  - frag0: 25 samples @ 500Hz
  - frag1: 250 samples @ 5kHz  <-- this is what you want for ERP analysis
  - frag2: 50 samples @ 1kHz
"""

import numpy as np
import struct
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

RECORD_SIZE     = 1444       # bytes per record
FRAG1_OFFSET    = 204        # byte offset of frag1 within each record
FRAG1_SAMPLES   = 250        # samples in frag1 (50ms @ 5kHz)
FRAG0_SAMPLES   = 25         # samples in frag0
FRAG2_SAMPLES   = 50         # samples in frag2
SAMPLE_RATE     = 5000       # Hz for frag1
AD2UV           = 2.441406   # raw int16 → microvolts
N_CHANNELS      = 2          # ch1 = SOLR (soleus), ch2 = QDR (quadriceps)
ENDIAN          = "<"        # little-endian


def decode_frag1(myd_path: str) -> np.ndarray:
    """
    Read all trials from a .MYD file and return the frag1 (ERP window) data.

    Returns
    -------
    signals : np.ndarray, shape (n_trials, n_channels, frag1_samples)
        In microvolts. ch0 = SOLR (soleus), ch1 = QDR (quadriceps).
    """
    data = Path(myd_path).read_bytes()
    n_records = len(data) // RECORD_SIZE

    signals = []
    for i in range(n_records):
        start = i * RECORD_SIZE + FRAG1_OFFSET
        end   = start + FRAG1_SAMPLES * N_CHANNELS * 2  # 2 bytes per int16

        raw = struct.unpack_from(f"{ENDIAN}{FRAG1_SAMPLES * N_CHANNELS}h", data, start)
        arr = np.array(raw, dtype=np.float32) * AD2UV  # convert to µV

        # Block channel layout: first half = ch1, second half = ch2
        ch1 = arr[:FRAG1_SAMPLES]
        ch2 = arr[FRAG1_SAMPLES:]

        signals.append([ch1, ch2])

    return np.array(signals)  # (n_trials, 2, 250)


def decode_all_fragments(myd_path: str) -> dict:
    """
    Decode all three fragments from every record.

    Returns
    -------
    dict with keys: frag0, frag1, frag2
    Each is np.ndarray of shape (n_trials, n_channels, n_samples).
    """
    data = Path(myd_path).read_bytes()
    n_records = len(data) // RECORD_SIZE

    frag_config = [
        ("frag0", 0,    FRAG0_SAMPLES),
        ("frag1", 204,  FRAG1_SAMPLES),
        ("frag2", 1244, FRAG2_SAMPLES),  # offset after frag0+frag1
    ]

    results = {k: [] for k, _, _ in frag_config}

    for i in range(n_records):
        rec_start = i * RECORD_SIZE
        for key, offset, n_samples in frag_config:
            start = rec_start + offset
            raw = struct.unpack_from(f"{ENDIAN}{n_samples * N_CHANNELS}h", data, start)
            arr = np.array(raw, dtype=np.float32) * AD2UV
            ch1 = arr[:n_samples]
            ch2 = arr[n_samples:]
            results[key].append([ch1, ch2])

    return {k: np.array(v) for k, v in results.items()}


def get_time_axis(n_samples: int = FRAG1_SAMPLES, rate: int = SAMPLE_RATE) -> np.ndarray:
    """Return time axis in milliseconds for frag1 (stimulus at t=0)."""
    return np.linspace(0, n_samples / rate * 1000, n_samples)


if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt

    path = sys.argv[1] if len(sys.argv) > 1 else "channel_data.MYD"
    signals = decode_frag1(path)
    t = get_time_axis()

    avg = signals.mean(axis=0)  # (2, 250)

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(t, avg[0], color="teal", linewidth=1.5)
    axes[0].set_title("Ch1 — SOLR (soleus)")
    axes[0].set_ylabel("µV")
    axes[1].plot(t, avg[1], color="purple", linewidth=1.5)
    axes[1].set_title("Ch2 — QDR (quadriceps)")
    axes[1].set_ylabel("µV")
    axes[1].set_xlabel("Time (ms)")
    plt.tight_layout()
    plt.savefig("erp_2013.png", dpi=150)
    print(f"Decoded {len(signals)} trials. Saved erp_2013.png")
