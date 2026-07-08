"""H-reflex amplitude label — the Phase-2 target.

Definition (per Dr. Carp, 2026-07-01 meeting):
    Label = MEAN RECTIFIED AMPLITUDE inside a fixed window that encompasses the
    H-reflex. NOT peak-to-peak.

Why not peak-to-peak: a single peak is easily corrupted by ongoing background
activity riding on the response. Rectifying and averaging over a window
integrates the whole burst, so a stray excursion can't dominate, and zero-mean
background largely cancels.

Two rules that come with it:
  1. WINDOWS MUST BE MATCHED. The same latency bounds are applied to every trial
     and every conditioning phase, or cross-phase comparison is meaningless.
  2. SET THE WINDOW FROM THE TRIAL-AVERAGED WAVEFORM. Average all trials, look at
     where the H-reflex bump actually sits (~8-10 ms), and set the window edges
     around it. Defaults below are a starting point — refine from the grand
     average before the real run.

This is the single canonical label function. The synthetic generator and Tarun's
DB->Zarr converter BOTH call it, so the label is computed identically on fake and
real data.
"""
from __future__ import annotations

import numpy as np

from src.utils.config import SignalConfig


def _ms_to_samples(ms: float, sample_rate_hz: int) -> int:
    return int(round(ms / 1000.0 * sample_rate_hz))


def compute_hreflex_label(
    emg: np.ndarray,
    cfg: SignalConfig,
    hreflex_window_ms: tuple[float, float] | None = None,
    baseline_window_ms: tuple[float, float] | None = None,
) -> np.ndarray:
    """Mean rectified H-reflex amplitude per trial.

    Args:
        emg: (N, T) or (T,) EMG window(s), stimulus-aligned, in microvolts.
        cfg: SignalConfig (for sample_rate_hz and the default window bounds).
        hreflex_window_ms: (start, end) in ms. Defaults to cfg.hreflex_ms, but
            you should WIDEN this to encompass the full burst once you've looked
            at the trial average (e.g. ~7-12 ms rather than exactly 8-10).
        baseline_window_ms: (start, end) in ms for baseline correction. Defaults
            to the quiet pre-response window (0 -> M-wave onset).

    Returns:
        (N,) or scalar array of mean rectified amplitudes (microvolts).
    """
    single = emg.ndim == 1
    x = emg[None, :] if single else emg
    sr = cfg.sample_rate_hz

    hw = hreflex_window_ms or cfg.hreflex_ms
    h0, h1 = _ms_to_samples(hw[0], sr), _ms_to_samples(hw[1], sr)

    # baseline: default to the pre-response quiet period (0 -> M-wave start)
    bw = baseline_window_ms or (0.0, cfg.mwave_ms[0])
    b0, b1 = _ms_to_samples(bw[0], sr), _ms_to_samples(bw[1], sr)
    b1 = max(b1, b0 + 1)

    T = x.shape[1]
    h0, h1 = max(0, h0), min(T, h1)
    if h1 <= h0:
        raise ValueError(f"empty H-reflex window: {hw} ms -> samples [{h0},{h1})")

    baseline = x[:, b0:b1].mean(axis=1, keepdims=True)     # per-trial DC offset
    corrected = x[:, h0:h1] - baseline                     # baseline-correct
    label = np.abs(corrected).mean(axis=1)                 # rectify -> mean

    return label[0] if single else label.astype(np.float32)


def suggest_window_from_average(
    emg: np.ndarray,
    cfg: SignalConfig,
    search_ms: tuple[float, float] = (5.0, 14.0),
    frac_of_peak: float = 0.3,
) -> tuple[float, float]:
    """Helper: propose an H-reflex window from the trial-averaged waveform.

    Averages all trials, rectifies, finds the H-reflex peak inside `search_ms`,
    and returns the ms bounds where the rectified average exceeds `frac_of_peak`
    of that peak. Use this to DATA-DRIVE the matched window, then eyeball it
    against the grand average before committing. Not called automatically.
    """
    sr = cfg.sample_rate_hz
    avg = np.abs(emg.mean(axis=0))
    s0, s1 = _ms_to_samples(search_ms[0], sr), _ms_to_samples(search_ms[1], sr)
    seg = avg[s0:s1]
    peak_rel = int(np.argmax(seg))
    thr = seg[peak_rel] * frac_of_peak
    above = np.where(seg >= thr)[0]
    lo, hi = above.min(), above.max()
    to_ms = lambda samp: (s0 + samp) / sr * 1000.0
    return round(to_ms(lo), 2), round(to_ms(hi), 2)
