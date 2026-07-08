"""Synthetic HROC data generator.

Purpose
-------
The real .MYD / Zarr data lives on the lab Google Drive and is large. To let us
build and validate the ENTIRE training machine before touching real data, this
module fabricates trials whose statistics mimic the decoded Animal-9 signals:

  * 150-sample, 5 kHz ERP windows (30 ms)
  * an EMG-like channel with an M-wave (~2-4 ms) and H-reflex (~8-10 ms) bump
  * an ECoG-like cortical channel driven by a small set of latent factors
  * a per-trial H-reflex amplitude label
  * a conditioning-phase label (0..5)

Crucially, the latent factors DRIFT across the six phases. That is the whole
scientific bet: if the brain changes as the spinal cord is conditioned, a good
autoencoder latent space should separate the phases. We bake that structure in
here so we can confirm the UMAP analysis would *detect* it on real data. On real
data the drift is the open question; here it is ground truth, used only to prove
the pipeline works end to end.

NOTHING here is a scientific result. It is a test harness. Every figure produced
from synthetic data is watermarked SYNTHETIC downstream.
"""
from __future__ import annotations

import numpy as np

from src.utils.config import SignalConfig, PHASES

N_LATENT = 5  # number of hidden generative factors


def _phase_latent_means(rng: np.random.Generator) -> np.ndarray:
    """A (6, N_LATENT) matrix of latent-factor means, one row per phase.

    We model conditioning as a smooth-ish trajectory through latent space with a
    partial reset at 'Freely Running'. Down-cond pushes one axis down, up-cond
    pushes it back up — echoing the real H-reflex amplitude story.
    """
    base = rng.normal(0, 0.3, size=(len(PHASES), N_LATENT))
    # Axis 0 = "conditioning axis": tracks the intended H-reflex change.
    conditioning_axis = np.array([0.0, -1.2, +0.9, +0.1, -1.6, +1.3])
    base[:, 0] = conditioning_axis
    # Axis 1 = slow drift across the whole timeline (cumulative cortical change).
    base[:, 1] = np.linspace(0, 1.0, len(PHASES))
    return base


def _make_mixing(rng: np.random.Generator, window: int) -> np.ndarray:
    """Fixed random smooth basis mapping latent factors -> a 150-sample signal."""
    t = np.linspace(0, 1, window)
    basis = []
    for k in range(N_LATENT):
        freq = rng.uniform(1.5, 6.0)
        phase = rng.uniform(0, 2 * np.pi)
        env = np.exp(-((t - rng.uniform(0.2, 0.8)) ** 2) / (2 * rng.uniform(0.02, 0.08) ** 2))
        basis.append(np.sin(2 * np.pi * freq * t + phase) * env)
    return np.stack(basis, axis=0)  # (N_LATENT, window)


def _emg_template(cfg: SignalConfig) -> np.ndarray:
    """An EMG-like trace: M-wave bump then H-reflex bump at the right latencies."""
    n = cfg.window_samples
    t_ms = np.arange(n) / cfg.sample_rate_hz * 1000.0

    def bump(center, width, amp):
        return amp * np.exp(-((t_ms - center) ** 2) / (2 * width ** 2))

    m_center = np.mean(cfg.mwave_ms)
    h_center = np.mean(cfg.hreflex_ms)
    return bump(m_center, 0.4, 1.0) + bump(h_center, 0.6, 0.55)


def generate(
    cfg_signal: SignalConfig,
    n_trials: int = 12000,
    seed: int = 7,
) -> dict[str, np.ndarray]:
    """Generate a synthetic Animal-9-like dataset.

    Returns a dict of numpy arrays:
        ecog:      (N, window)  float32 -- the signal the autoencoder sees
        emg:       (N, window)  float32 -- EMG channel (for validation figures)
        hreflex:   (N,)         float32 -- per-trial H-reflex amplitude (label)
        phase:     (N,)         int64   -- conditioning phase index 0..5
    """
    rng = np.random.default_rng(seed)
    window = cfg_signal.window_samples

    phase_means = _phase_latent_means(rng)       # (6, N_LATENT)
    mixing = _make_mixing(rng, window)           # (N_LATENT, window)
    emg_base = _emg_template(cfg_signal)         # (window,)

    # Roughly balanced trials per phase.
    phase = rng.integers(0, len(PHASES), size=n_trials)

    # Draw latent factors per trial around that trial's phase mean.
    latents = phase_means[phase] + rng.normal(0, 0.35, size=(n_trials, N_LATENT))

    # ECoG = latent factors mixed through the fixed basis + pink-ish noise.
    ecog = latents @ mixing
    noise = rng.normal(0, 0.25, size=ecog.shape)
    # light temporal smoothing of noise to look more physiological
    kernel = np.array([0.25, 0.5, 0.25])
    noise = np.apply_along_axis(lambda r: np.convolve(r, kernel, mode="same"), 1, noise)
    ecog = (ecog + noise).astype(np.float32)

    # EMG channel: base template scaled by an underlying drive + noise.
    # The drive is latent-linked so the label stays predictable from the ECoG.
    drive = (
        0.6 * latents[:, 0]
        + 0.2 * latents[:, 1]
        + rng.normal(0, 0.15, size=n_trials)
    )
    drive = (drive - drive.min()) / (np.ptp(drive) + 1e-8)
    emg = (
        emg_base[None, :] * (0.5 + drive[:, None])
        + rng.normal(0, 0.05, size=(n_trials, window))
    ).astype(np.float32)

    # H-reflex label is computed from the EMG the SAME WAY it will be on real
    # data: mean rectified amplitude in the matched window (Carp's spec). This
    # exercises the real label function on synthetic data too.
    from src.data.hreflex_label import compute_hreflex_label
    hreflex = compute_hreflex_label(
        emg, cfg_signal,
        hreflex_window_ms=cfg_signal.hreflex_window_ms,
        baseline_window_ms=cfg_signal.baseline_window_ms,
    ).astype(np.float32)

    return {
        "ecog": ecog,
        "emg": emg,
        "hreflex": hreflex,
        "phase": phase.astype(np.int64),
    }


def generate_multi(cfg_signal, n_animals: int = 3, n_trials: int = 12000, seed: int = 42):
    """Fabricate several fake 'animals' with DIFFERENT window lengths.

    Purpose: exercise the multi-animal pooling + resampling path end to end
    without real data. Each animal gets its own window length (mimicking the
    2006 150-sample vs 2013 250-sample format split) and a slightly different
    signal character, but the same 6-phase conditioning structure.

    Returns a list of (animal_id, data_dict) matching the shape _load_zarr gives,
    so the pooling loader treats synthetic and real identically.
    """
    from dataclasses import replace
    windows = [150, 250, 200, 175, 225, 160]  # cycle through plausible lengths
    per = max(n_trials // n_animals, 500)
    stores = []
    for a in range(n_animals):
        win = windows[a % len(windows)]
        sig = replace(cfg_signal, window_samples=win)
        d = generate(sig, n_trials=per, seed=seed + 100 * a)
        # drop the extra 'emg' key? keep it — pooling handles emg if present
        stores.append((f"synth{a}_w{win}", d))
    return stores
