"""Latent-space analysis — the scientific payoff.

Given a trained encoder, embed every trial into the latent space and ask the
central HROC question: does the representation shift across the six conditioning
phases? We produce three artifacts:

  1. umap_by_phase.png       -- 2-D UMAP scatter, colored by conditioning phase.
  2. centroid_drift.png      -- each phase's latent centroid distance from the
                                Baseline centroid, i.e. how far the brain's
                                representation has moved.
  3. phase_separation.txt    -- silhouette score in latent space (a single number
                                quantifying how cleanly phases separate).

On real data, clean separation + a coherent centroid trajectory would be the
never-before-published evidence of cortical correlates of HROC. On synthetic data
it confirms the analysis can DETECT such structure when present.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score

from src.utils.config import Config, PHASES
from src.utils.seed import get_device

# a fixed, readable palette for the six phases
PHASE_COLORS = ["#334155", "#2563eb", "#dc2626", "#16a34a", "#7c3aed", "#ea580c"]


@torch.no_grad()
def extract_latents(cfg: Config, encoder, loader):
    device = get_device()
    encoder = encoder.to(device).eval()
    Z, P, H = [], [], []
    for batch in loader:
        x = batch["ecog"].to(device)
        Z.append(encoder.encode(x).cpu().numpy())
        P.append(batch["phase"].numpy())
        H.append(batch["hreflex"].numpy())
    return np.concatenate(Z), np.concatenate(P), np.concatenate(H)


def run_umap(latents: np.ndarray, seed: int = 42) -> np.ndarray:
    import umap
    reducer = umap.UMAP(n_neighbors=25, min_dist=0.1, random_state=seed)
    return reducer.fit_transform(latents)


def plot_umap_by_phase(emb2d, phases, out_path, synthetic=True):
    fig, ax = plt.subplots(figsize=(8, 6.5))
    for i, name in enumerate(PHASES):
        m = phases == i
        ax.scatter(emb2d[m, 0], emb2d[m, 1], s=6, alpha=0.55,
                   color=PHASE_COLORS[i], label=name)
    ax.set_title("Autoencoder latent space (UMAP) by conditioning phase")
    ax.set_xlabel("UMAP-1"); ax.set_ylabel("UMAP-2")
    ax.legend(markerscale=2, fontsize=9, loc="best")
    if synthetic:
        ax.text(0.99, 0.01, "SYNTHETIC DATA — pipeline validation only",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=8, color="#94a3b8")
    fig.tight_layout(); fig.savefig(out_path, dpi=150); plt.close(fig)


def plot_centroid_drift(latents, phases, out_path, synthetic=True):
    """Distance of each phase's latent centroid from the Baseline centroid."""
    centroids = np.stack([latents[phases == i].mean(0) for i in range(len(PHASES))])
    baseline = centroids[0]
    drift = np.linalg.norm(centroids - baseline, axis=1)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(len(PHASES)), drift, "-o", color="#7c3aed", linewidth=2)
    for i, d in enumerate(drift):
        ax.annotate(f"{d:.2f}", (i, d), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=9)
    ax.set_xticks(range(len(PHASES)))
    ax.set_xticklabels(PHASES, rotation=20, ha="right")
    ax.set_ylabel("Latent centroid distance from Baseline")
    ax.set_title("Does the representation drift across conditioning?")
    if synthetic:
        ax.text(0.99, 0.01, "SYNTHETIC DATA — pipeline validation only",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=8, color="#94a3b8")
    fig.tight_layout(); fig.savefig(out_path, dpi=150); plt.close(fig)
    return drift


def phase_separation_score(latents, phases) -> float:
    """Silhouette score using phase as the label. Higher = phases separate more."""
    # subsample for speed if huge
    n = latents.shape[0]
    if n > 5000:
        idx = np.random.default_rng(0).choice(n, 5000, replace=False)
        latents, phases = latents[idx], phases[idx]
    try:
        return float(silhouette_score(latents, phases))
    except Exception:
        return float("nan")


def analyze(cfg: Config, encoder, loader) -> dict:
    out = Path(cfg.train.out_dir)
    synthetic = cfg.data.use_synthetic
    latents, phases, _ = extract_latents(cfg, encoder, loader)

    emb2d = run_umap(latents, seed=cfg.train.seed)
    plot_umap_by_phase(emb2d, phases, out / "umap_by_phase.png", synthetic)
    drift = plot_centroid_drift(latents, phases, out / "centroid_drift.png", synthetic)
    sil = phase_separation_score(latents, phases)

    (out / "phase_separation.txt").write_text(
        f"Phase silhouette score (latent space): {sil:.4f}\n"
        f"Centroid drift from Baseline per phase:\n"
        + "\n".join(f"  {PHASES[i]:15s} {d:.4f}" for i, d in enumerate(drift))
        + ("\n\nNOTE: SYNTHETIC data — validates the analysis, not a result.\n"
           if synthetic else "\n")
    )
    print(f"[analysis] phase silhouette = {sil:.4f}  "
          f"(figures + report in {out}/)")
    return {"silhouette": sil, "drift": drift.tolist()}
