"""Two-dimensional maps of each embedding (UMAP), and how it moves over the recording.

For the embedding size chosen by reconstruction (outputs/latent_sweep/choice.json),
3,000 usable trials per animal are encoded and projected to two dimensions with UMAP,
fitted once on all five animals together. UMAP preserves local neighbourhoods; its
axes have no units, and distances between far-apart clusters are not meaningful.

map_<input>.png         the same map coloured four ways: animal, days relative to the
                        start of training, baseline vs training, and reflex size
                        (corrected for stimulus and background, ranked within animal)
trajectory_<input>.png  one panel per animal: each 5-day window's average position on
                        the map, joined in time order, so change over weeks is visible

Usage:
  python scripts/embedding_map.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
matplotlib.rcParams.update({"font.size": 13, "axes.titlesize": 15, "legend.fontsize": 12})

from scripts.reflex_measures import find_windows, measures
from scripts.final_analysis import design, residualise, BLOCK_DAYS
from scripts.latent_sweep import (ANIMALS, LABEL, OUT as SWEEP, encode_rows,
                                  load_model, load_norm, zpath)

OUT = Path("outputs/embeddings")
N_PER = 3000
COLOURS = {"9": "#15718F", "10": "#6B8FA3", "11": "#3B6E43", "3": "#B4671A", "4": "#A44430"}
DIRECTION = {"9": "down", "10": "down", "11": "down", "3": "up", "4": "up"}


def collect(inp, k, dev):
    import zarr
    model, norms = load_model(inp, k, dev), load_norm(inp)
    rng = np.random.default_rng(42)
    Z, A, D, P, R, B = [], [], [], [], [], []
    for a in ANIMALS:
        r = zarr.open(zpath(a), mode="r")
        emg = np.asarray(r["emg"]); day = np.asarray(r["day"]); phase = np.asarray(r["phase"])
        m_sl, h_sl, *_ = find_windows(emg)
        M, H, bg = measures(emg, m_sl, h_sl)
        good = np.where((M > 3 * bg) & np.asarray(r["prestim_ok"]))[0]
        pre = np.asarray(r["prestim_emg"])
        Hc = residualise(H[good], design(M[good], pre[good]))   # reflex, stimulus/background removed
        pick = np.sort(rng.choice(len(good), min(len(good), N_PER), replace=False))
        idx = good[pick]
        onset = int(day[phase > 0].min()) if (phase > 0).any() else int(day.max() // 2)
        Z.append(encode_rows(inp, r, idx, norms[a], model, dev))
        A += [a] * len(idx)
        D.append(day[idx] - onset); P.append(phase[idx]); B.append(day[idx] // BLOCK_DAYS)
        h = Hc[pick]
        R.append(np.argsort(np.argsort(h)) / max(len(h) - 1, 1))
    return (np.concatenate(Z), np.array(A), np.concatenate(D), np.concatenate(P),
            np.concatenate(R), np.concatenate(B))


def tidy(ax, title):
    ax.set_title(title); ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlabel("UMAP 1 (no units)"); ax.set_ylabel("UMAP 2 (no units)")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def main():
    import umap
    from src.utils.seed import get_device
    dev = get_device()
    OUT.mkdir(parents=True, exist_ok=True)
    choice = json.loads((SWEEP / "choice.json").read_text())

    for inp, k in choice.items():
        Z, A, D, P, R, B = collect(inp, k, dev)
        Zs = (Z - Z.mean(0)) / (Z.std(0) + 1e-8)
        E = umap.UMAP(n_neighbors=30, min_dist=0.25, random_state=42).fit_transform(Zs)
        order = np.random.default_rng(0).permutation(len(E))     # no animal drawn on top
        kw = dict(s=3, alpha=0.55, linewidths=0, rasterized=True)

        fig, ax = plt.subplots(2, 2, figsize=(13, 11))
        ax = ax.ravel()
        ax[0].scatter(*E[order].T, c=[COLOURS[a] for a in A[order]], **kw)
        for a in ANIMALS:
            ax[0].scatter([], [], c=COLOURS[a], s=60, label=f"A{a} ({DIRECTION[a]})")
        ax[0].legend(frameon=False, loc="best", markerscale=1.2)
        tidy(ax[0], "Animal")
        sc = ax[1].scatter(*E[order].T, c=D[order], cmap="coolwarm",
                           norm=TwoSlopeNorm(vcenter=0, vmin=-40, vmax=60), **kw)
        fig.colorbar(sc, ax=ax[1], shrink=0.8).set_label("days relative to start of training")
        tidy(ax[1], "Time")
        ax[2].scatter(*E[order].T, c=np.where(P[order] > 0, "#B4671A", "#9AA8B4"), **kw)
        ax[2].scatter([], [], c="#9AA8B4", s=60, label="baseline")
        ax[2].scatter([], [], c="#B4671A", s=60, label="training")
        ax[2].legend(frameon=False, loc="best")
        tidy(ax[2], "Baseline vs training")
        sc = ax[3].scatter(*E[order].T, c=R[order], cmap="viridis", vmin=0, vmax=1, **kw)
        fig.colorbar(sc, ax=ax[3], shrink=0.8).set_label("reflex size, rank within animal")
        tidy(ax[3], "Reflex size (stimulus and background removed)")
        fig.suptitle(f"Embedding map: {LABEL[inp]}, {k} numbers per trial",
                     fontsize=17, weight="bold")
        fig.tight_layout(); fig.savefig(OUT / f"map_{inp}.png", dpi=140); plt.close(fig)

        fig, ax = plt.subplots(1, len(ANIMALS), figsize=(4.2 * len(ANIMALS), 4.6))
        for j, a in enumerate(ANIMALS):
            m = A == a
            ax[j].scatter(*E[m].T, c="#DDE4EA", s=2, linewidths=0, rasterized=True)
            blocks = np.unique(B[m])
            C = np.array([E[m][B[m] == b].mean(0) for b in blocks])
            t = np.array([D[m][B[m] == b].mean() for b in blocks])
            ax[j].plot(*C.T, color="#5A6B7B", lw=1, zorder=2)
            sc = ax[j].scatter(*C.T, c=t, cmap="coolwarm", s=46, zorder=3, edgecolors="white",
                               norm=TwoSlopeNorm(vcenter=0, vmin=-40, vmax=60))
            on = np.argmin(np.abs(t))
            ax[j].scatter(*C[on], marker="*", s=260, c="#14212E", zorder=4)
            tidy(ax[j], f"A{a} ({DIRECTION[a]})")
            ax[j].set_xlabel(""); ax[j].set_ylabel("")
        fig.colorbar(sc, ax=ax, shrink=0.85).set_label("days relative to start of training")
        fig.suptitle(f"How each animal's average moves across the recording ({LABEL[inp]}); "
                     f"dots = 5-day windows, star = start of training", fontsize=14)
        fig.savefig(OUT / f"trajectory_{inp}.png", dpi=140, bbox_inches="tight"); plt.close(fig)
        print(f"[map] {inp} (k={k}): {len(E)} trials -> {OUT}/map_{inp}.png, trajectory_{inp}.png",
              flush=True)


if __name__ == "__main__":
    main()
