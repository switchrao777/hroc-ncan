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
    Z, P, H, A = [], [], [], []
    for batch in loader:
        x = batch["ecog"].to(device)
        Z.append(encoder.encode(x).cpu().numpy())
        P.append(batch["phase"].numpy())
        H.append(batch["hreflex"].numpy())
        if "animal" in batch:
            A.append(batch["animal"].numpy())
    animal = np.concatenate(A) if A else None
    return np.concatenate(Z), np.concatenate(P), np.concatenate(H), animal


def run_umap(latents: np.ndarray, seed: int = 42) -> np.ndarray:
    import umap
    reducer = umap.UMAP(n_neighbors=25, min_dist=0.1, random_state=seed)
    return reducer.fit_transform(latents)


def plot_umap_by_phase(emb2d, phases, out_path, synthetic=True):
    fig, ax = plt.subplots(figsize=(8, 6.5))
    for i, name in enumerate(PHASES):
        m = phases == i
        if not np.any(m):          # skip phases this animal didn't run
            continue
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
    """Distance of each phase's latent centroid from the Baseline centroid.

    Only phases actually present are plotted (many animals ran a partial protocol,
    e.g. Animal 9 = Baseline/HRdown/Post), so absent phases are left as NaN rather
    than producing empty-slice NaNs on the axis.
    """
    present = [i for i in range(len(PHASES)) if np.any(phases == i)]
    drift = np.full(len(PHASES), np.nan)
    baseline = latents[phases == present[0]].mean(0)   # phase 0 = Baseline
    for i in present:
        drift[i] = np.linalg.norm(latents[phases == i].mean(0) - baseline)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(present, drift[present], "-o", color="#7c3aed", linewidth=2)
    for i in present:
        ax.annotate(f"{drift[i]:.2f}", (i, drift[i]), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=9)
    ax.set_xticks(present)
    ax.set_xticklabels([PHASES[i] for i in present], rotation=20, ha="right")
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


def plot_umap_by_animal(emb2d, animal, names, out_path, synthetic=True):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 6.5))
    palette = plt.cm.tab10(np.linspace(0, 1, max(len(names), 1)))
    for i, name in enumerate(names):
        m = animal == i
        ax.scatter(emb2d[m, 0], emb2d[m, 1], s=6, alpha=0.55,
                   color=palette[i], label=name)
    ax.set_title("Latent space (UMAP) by animal — batch-effect check")
    ax.set_xlabel("UMAP-1"); ax.set_ylabel("UMAP-2")
    ax.legend(markerscale=2, fontsize=8, loc="best")
    if synthetic:
        ax.text(0.99, 0.01, "SYNTHETIC DATA", transform=ax.transAxes, ha="right",
                va="bottom", fontsize=8, color="#94a3b8")
    fig.tight_layout(); fig.savefig(out_path, dpi=150); plt.close(fig)


def analyze(cfg: Config, encoder, loader) -> dict:
    out = Path(cfg.train.out_dir)
    synthetic = cfg.data.use_synthetic
    latents, phases, _, animal = extract_latents(cfg, encoder, loader)

    # UMAP is O(n) memory/time-heavy; on the full real dataset (~283k trials) cap
    # the embedding to a random subset for the scatter. Centroid drift + silhouette
    # still use ALL trials (they only need means / a 5k sample).
    UMAP_MAX = 20000
    if latents.shape[0] > UMAP_MAX:
        idx = np.random.default_rng(cfg.train.seed).choice(
            latents.shape[0], UMAP_MAX, replace=False)
        emb_latents, emb_phases = latents[idx], phases[idx]
        emb_animal = animal[idx] if animal is not None else None
    else:
        emb_latents, emb_phases, emb_animal = latents, phases, animal

    emb2d = run_umap(emb_latents, seed=cfg.train.seed)
    plot_umap_by_phase(emb2d, emb_phases, out / "umap_by_phase.png", synthetic)
    drift = plot_centroid_drift(latents, phases, out / "centroid_drift.png", synthetic)
    sil = phase_separation_score(latents, phases)

    # Batch-effect check: if pooling animals, does the latent separate by PHASE
    # (what we want) or by ANIMAL (a confound to correct)?
    animal_sil = None
    from src.data.zarr_dataset import ANIMAL_NAMES
    if animal is not None and len(set(animal.tolist())) > 1:
        plot_umap_by_animal(emb2d, emb_animal, ANIMAL_NAMES,
                            out / "umap_by_animal.png", synthetic)
        animal_sil = phase_separation_score(latents, animal)

    report = [f"Phase silhouette (want high): {sil:.4f}"]
    if animal_sil is not None:
        report.append(f"Animal silhouette (want LOW vs phase): {animal_sil:.4f}")
        if animal_sil > sil:
            report.append("WARNING: animal identity dominates the latent more than "
                          "phase. Add per-animal normalization / batch correction "
                          "before trusting the drift result.")
    report.append("Centroid drift from Baseline per phase:")
    report += [f"  {PHASES[i]:15s} {d:.4f}" for i, d in enumerate(drift)
               if not np.isnan(d)]
    if synthetic:
        report.append("\nNOTE: SYNTHETIC data — validates the analysis, not a result.")
    (out / "phase_separation.txt").write_text("\n".join(report) + "\n")

    msg = f"[analysis] phase silhouette = {sil:.4f}"
    if animal_sil is not None:
        msg += f"  |  animal silhouette = {animal_sil:.4f}"
    print(msg + f"  (figures + report in {out}/)")
    return {"silhouette": sil, "animal_silhouette": animal_sil, "drift": drift.tolist()}
