"""Neuroscience result figures \u2014 the things Dr. Carp actually wants to see.

The pipeline's UMAP + centroid-drift show the *cortical* representation moving.
But the neuro story needs the *behavioral* side too: did conditioning actually
change the H-reflex, and does the cortical drift track that change? This module
produces the figures that tell that story:

  1. hreflex_by_phase.png  \u2014 mean H-reflex amplitude per phase (the conditioning
                             'learning curve': down-cond lower, up-cond higher).
  2. waveform_by_phase.png \u2014 trial-averaged EMG per phase, overlaid. Shows the
                             physiological change directly in the raw signal.
  3. cortex_vs_behavior.png\u2014 cortical latent drift and H-reflex change on one
                             plot: does the brain move when the reflex moves?

All are watermarked SYNTHETIC when run on fake data.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.utils.config import Config, PHASES, SignalConfig

PHASE_COLORS = ["#334155", "#2563eb", "#dc2626", "#16a34a", "#7c3aed", "#ea580c"]


def _sem(x):
    return x.std(ddof=1) / np.sqrt(max(len(x), 1))


def hreflex_by_phase(hreflex, phase, out_path, synthetic=True):
    """The conditioning learning curve: mean H-reflex per phase +/- SEM."""
    means = [hreflex[phase == i].mean() for i in range(len(PHASES))]
    sems = [_sem(hreflex[phase == i]) for i in range(len(PHASES))]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(range(len(PHASES)), means, yerr=sems, fmt="-o", color="#0d9488",
                linewidth=2, capsize=4, markersize=7)
    ax.set_xticks(range(len(PHASES)))
    ax.set_xticklabels(PHASES, rotation=20, ha="right")
    ax.set_ylabel("Mean H-reflex amplitude (rectified)")
    ax.set_title("Did conditioning change the H-reflex?")
    ax.axhline(means[0], color="#94a3b8", ls="--", lw=1, alpha=0.7)
    if synthetic:
        ax.text(0.99, 0.02, "SYNTHETIC DATA", transform=ax.transAxes, ha="right",
                va="bottom", fontsize=8, color="#94a3b8")
    fig.tight_layout(); fig.savefig(out_path, dpi=150); plt.close(fig)
    return means


def waveform_by_phase(emg, phase, cfg_signal: SignalConfig, out_path, synthetic=True):
    """Trial-averaged EMG waveform per phase, overlaid on a ms axis."""
    # Map the (possibly resampled) window back onto the native duration in ms,
    # so the M/H bands sit at the right latencies. Resampling preserves relative
    # position, so linspace over native duration is correct for a single animal
    # and a good approximation when pooling similar formats.
    native_ms = cfg_signal.window_samples / cfg_signal.sample_rate_hz * 1000.0
    t_ms = np.linspace(0, native_ms, emg.shape[1])
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, name in enumerate(PHASES):
        avg = emg[phase == i].mean(axis=0)
        ax.plot(t_ms, avg, color=PHASE_COLORS[i], label=name, linewidth=1.6)
    # mark the reflex windows
    ax.axvspan(cfg_signal.mwave_ms[0], cfg_signal.mwave_ms[1], color="#fde68a", alpha=0.3)
    ax.axvspan(cfg_signal.hreflex_ms[0], cfg_signal.hreflex_ms[1], color="#bbf7d0", alpha=0.4)
    ax.text(np.mean(cfg_signal.mwave_ms), ax.get_ylim()[1]*0.92, "M", ha="center", fontsize=9, color="#92400e")
    ax.text(np.mean(cfg_signal.hreflex_ms), ax.get_ylim()[1]*0.92, "H", ha="center", fontsize=9, color="#166534")
    ax.set_xlabel("Time (ms)"); ax.set_ylabel("EMG (avg)")
    ax.set_title("Averaged EMG by conditioning phase")
    ax.legend(fontsize=8, ncol=2)
    if synthetic:
        ax.text(0.99, 0.02, "SYNTHETIC DATA", transform=ax.transAxes, ha="right",
                va="bottom", fontsize=8, color="#94a3b8")
    fig.tight_layout(); fig.savefig(out_path, dpi=150); plt.close(fig)


def cortex_vs_behavior(latents, hreflex, phase, out_path, synthetic=True):
    """Overlay cortical latent drift and H-reflex change across phases."""
    centroids = np.stack([latents[phase == i].mean(0) for i in range(len(PHASES))])
    drift = np.linalg.norm(centroids - centroids[0], axis=1)
    hmeans = np.array([hreflex[phase == i].mean() for i in range(len(PHASES))])

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(range(len(PHASES)), drift, "-o", color="#7c3aed", lw=2, label="Cortical drift")
    ax1.set_ylabel("Cortical latent drift from Baseline", color="#7c3aed")
    ax1.tick_params(axis="y", labelcolor="#7c3aed")
    ax2 = ax1.twinx()
    ax2.plot(range(len(PHASES)), hmeans, "-s", color="#0d9488", lw=2, label="H-reflex")
    ax2.set_ylabel("Mean H-reflex amplitude", color="#0d9488")
    ax2.tick_params(axis="y", labelcolor="#0d9488")
    ax1.set_xticks(range(len(PHASES)))
    ax1.set_xticklabels(PHASES, rotation=20, ha="right")
    ax1.set_title("Does the cortex move when the reflex moves?")
    if synthetic:
        ax1.text(0.99, 0.02, "SYNTHETIC DATA", transform=ax1.transAxes, ha="right",
                 va="bottom", fontsize=8, color="#94a3b8")
    fig.tight_layout(); fig.savefig(out_path, dpi=150); plt.close(fig)


def make_all(cfg: Config, latents, phase, hreflex, emg=None):
    """Produce every neuro figure available given what's in hand."""
    out = Path(cfg.train.out_dir)
    syn = cfg.data.use_synthetic
    hreflex_by_phase(hreflex, phase, out / "hreflex_by_phase.png", syn)
    cortex_vs_behavior(latents, hreflex, phase, out / "cortex_vs_behavior.png", syn)
    if emg is not None:
        waveform_by_phase(emg, phase, cfg.signal, out / "waveform_by_phase.png", syn)
    print(f"[neuro] wrote H-reflex curve, cortex-vs-behavior"
          + (", waveforms" if emg is not None else "") + f" to {out}/")
