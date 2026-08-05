"""
decoder_2006.py
---------------
Decoder for Animal 9 (2006 format) Elizan III MyISAM .MYD binary files.

This format differs from the 2013 format in THREE ways (all undocumented,
discovered via hex inspection):
  1. BIG-endian (not little-endian)
  2. 8,536 bytes per record (not 1,444)
  3. ONE fragment per record (not three)

Format confirmed parameters:
  - int16 signed, BIG-endian
  - 8,536 bytes per record
  - 1 fragment per record (frag1 only, 150 samples @ 5kHz)
  - Channel layout: BLOCK (ch1 = first half, ch2 = second half) — same as 2013
  - ad2uV = 2.441406 — same as 2013
  - Ch1 = SOLR (soleus EMG, rectified)
  - Ch2 = ECoG (cortical surface) — this is the paired brain signal!

KNOWN BUG:
  Baseline subtraction requires frag0 from the PRECEDING record.
  The current implementation reads frag0 from within the current record,
  which is incorrect for this format. Fix pending.
"""

import numpy as np
import struct
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

RECORD_SIZE     = 8536       # bytes per record
FRAG1_SAMPLES   = 150        # samples in frag1 (30ms @ 5kHz)
SAMPLE_RATE     = 5000       # Hz
AD2UV           = 2.441406   # raw int16 → microvolts
N_CHANNELS      = 2          # ch1 = SOLR EMG, ch2 = ECoG cortical surface
ENDIAN          = ">"        # BIG-endian (key difference from 2013!)


def decode_frag1(myd_path: str, fix_baseline: bool = False) -> np.ndarray:
    """
    Read all trials from a 2006-format .MYD file.

    Parameters
    ----------
    myd_path : str
        Path to the .MYD file.
    fix_baseline : bool
        If True, subtract frag0 baseline using the PRECEDING record's frag0.
        This is the correct approach but requires careful indexing.
        Default False until fully validated.

    Returns
    -------
    signals : np.ndarray, shape (n_trials, n_channels, frag1_samples)
        In microvolts. ch0 = SOLR EMG, ch1 = ECoG.
    """
    data = Path(myd_path).read_bytes()
    n_records = len(data) // RECORD_SIZE
    print(f"Found {n_records} records in {Path(myd_path).name}")

    signals = []
    for i in range(n_records):
        start = i * RECORD_SIZE
        # frag1 offset within the 8536-byte record — found via hex inspection
        frag1_start = start + 4000  # TODO: confirm exact offset per animal

        raw = struct.unpack_from(f"{ENDIAN}{FRAG1_SAMPLES * N_CHANNELS}h", data, frag1_start)
        arr = np.array(raw, dtype=np.float32) * AD2UV

        # Block layout: first half = ch1 (SOLR EMG), second half = ch2 (ECoG)
        ch1 = arr[:FRAG1_SAMPLES]
        ch2 = arr[FRAG1_SAMPLES:]

        signals.append([ch1, ch2])

    signals = np.array(signals)  # (n_trials, 2, 150)

    if fix_baseline:
        # TODO: implement proper baseline fix
        # Correct approach: for each record i, read frag0 from record i-1
        # and use it to subtract the pre-stimulus baseline.
        # Currently a known bug — leaving as placeholder.
        raise NotImplementedError(
            "Baseline fix not yet implemented. "
            "Requires reading frag0 from the preceding record. "
            "See GitHub issue #1."
        )

    return signals


def get_time_axis(n_samples: int = FRAG1_SAMPLES, rate: int = SAMPLE_RATE) -> np.ndarray:
    """Return time axis in milliseconds for frag1 (stimulus at t=0)."""
    return np.linspace(0, n_samples / rate * 1000, n_samples)


if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt

    path = sys.argv[1] if len(sys.argv) > 1 else "channel_data.MYD"
    signals = decode_frag1(path, fix_baseline=False)
    t = get_time_axis()

    avg = signals.mean(axis=0)  # (2, 150)

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(t, avg[0], color="teal", linewidth=1.5)
    axes[0].set_title("Ch1 — SOLR (soleus EMG)")
    axes[0].set_ylabel("µV")
    axes[1].plot(t, avg[1], color="green", linewidth=1.5)
    axes[1].set_title("Ch2 — ECoG (cortical surface)  ← PAIRED BRAIN SIGNAL")
    axes[1].set_ylabel("µV")
    axes[1].set_xlabel("Time (ms)")
    plt.tight_layout()
    plt.savefig("erp_animal9.png", dpi=150)
    print(f"Decoded {len(signals)} trials. Saved erp_animal9.png")
