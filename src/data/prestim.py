"""Pre-stimulus ECoG preprocessing shared by the encoder sweep, coupling and maps.

The 1-s pre-stimulus window carries a strong 120 Hz mains harmonic (about 55x the
neighbouring spectrum in animal 9). It is notched out, together with 60 and 180 Hz,
before anything is learned from the signal.

Two input forms are offered:
  clean_wave    the waveform itself (phase-specific)
  log_spectrum  log power at 1-Hz resolution (phase-invariant); slow rhythms fall at
                a random phase on every trial, so this form represents theta and beta
                power directly rather than asking the model to reconstruct their phase.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import filtfilt, iirnotch

FS = 1000.0
AD2UV = 2.441406
LINE_HZ = (60.0, 120.0, 180.0)
_NOTCH = [iirnotch(f, 30.0, FS) for f in LINE_HZ]
SPEC_HZ = (1.0, 200.0)


def clean_wave(raw: np.ndarray) -> np.ndarray:
    """(n, 1000) int16 -> float32 microvolts, per-trial mean removed, mains notched."""
    x = raw.astype(np.float64) * AD2UV
    x -= x.mean(axis=1, keepdims=True)
    for b, a in _NOTCH:
        x = filtfilt(b, a, x, axis=1, padlen=300)
    return x.astype(np.float32)


def log_spectrum(x: np.ndarray) -> np.ndarray:
    """(n, 1000) cleaned microvolts -> (n, 199) log10 power, 1-Hz bins from 1 to 199 Hz."""
    w = np.hanning(x.shape[1]).astype(np.float32)
    P = np.abs(np.fft.rfft(x * w, axis=1)) ** 2
    f = np.fft.rfftfreq(x.shape[1], 1.0 / FS)
    keep = (f >= SPEC_HZ[0]) & (f < SPEC_HZ[1])
    return np.log10(P[:, keep] + 1e-6).astype(np.float32)
