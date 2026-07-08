"""Preprocessing transforms.

Two paths:
  * conv_ae  -> operates on the raw 1-D window, so we just z-score per trial.
  * brainbert -> operates on a spectrogram (BrainBERT is a masked-spectrogram
    transformer), so we provide an STFT transform matching that expectation.
"""
from __future__ import annotations

import numpy as np
import torch


def zscore_per_trial(x: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """Z-score each trial independently. Removes per-trial DC + gain differences
    which otherwise dominate the latent space and hide phase structure."""
    mu = x.mean(axis=-1, keepdims=True)
    sd = x.std(axis=-1, keepdims=True)
    return (x - mu) / (sd + eps)


def stft_spectrogram(
    x: torch.Tensor,
    n_fft: int = 32,
    hop: int = 8,
) -> torch.Tensor:
    """Log-magnitude STFT for the BrainBERT-style encoder.

    Args:
        x: (B, T) waveform batch.
    Returns:
        (B, F, N) log-magnitude spectrogram, F = n_fft//2 + 1 freq bins,
        N = number of time frames.
    """
    window = torch.hann_window(n_fft, device=x.device)
    spec = torch.stft(
        x,
        n_fft=n_fft,
        hop_length=hop,
        window=window,
        return_complex=True,
        center=True,
    )
    mag = spec.abs()
    return torch.log1p(mag)  # (B, F, N)
