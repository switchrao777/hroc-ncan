"""Cortex->reflex COUPLING over conditioning — a drift-immune test.

The question we could not answer with centroid drift ("did the average cortical
state move?") is hopelessly confounded with slow recording nonstationarity, because
both are smooth functions of time. This asks a different and better question:

    How well can the cortical signal PREDICT the H-reflex on a trial-by-trial
    basis, and does that coupling CHANGE with conditioning?

Why this is immune to the confound that killed the drift analysis:
  * The decoder is trained and tested WITHIN a single 5-day block, by cross-
    validation. Slow drift shifts train and test data together, so it cancels; a
    gradual electrode change cannot manufacture within-block predictive structure.
  * Both sides are residualised on the M-wave and pre-stimulus background first, so
    the decoder cannot cheat by reading stimulus size or arousal (which drive both
    the cortical evoked response and the reflex).
  * A within-block LABEL SHUFFLE gives a per-block null; real coupling must beat it.

Biological reading: if cortex becomes more involved in controlling the reflex as the
animal learns, trial-by-trial coupling should strengthen after conditioning onset —
and the up and down groups give the direction test.

Outputs (outputs/coupling/):
  coupling_<A>.png   decoding R^2 per block, with the shuffle null
  coupling_group.png up vs down, aligned to each animal's onset
  summary.txt / summary.csv

Usage:
  python scripts/coupling_analysis.py --zarrs data/processed/animal*.zarr \
      --ckpt outputs/encoder_pooled.pt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.reflex_measures import find_windows, measures
from scripts.final_analysis import design, residualise, latents, BASELINE_DAYS, BLOCK_DAYS

DOWN_C, UP_C, GREY, VIOLET = "#2563eb", "#dc2626", "#64748b", "#6d28d9"
MIN_TRIALS = 400          # per block, else the CV estimate is too noisy
N_FOLDS = 5
RIDGE = 30.0


def ridge_cv_r2(Z, y, n_folds=N_FOLDS, lam=RIDGE, rng=None):
    """K-fold cross-validated R^2 for Z -> y, all within one block."""
    n = len(y)
    if n < MIN_TRIALS:
        return np.nan
    idx = (rng or np.random.default_rng(0)).permutation(n)
    folds = np.array_split(idx, n_folds)
    preds = np.empty(n); preds[:] = np.nan
    for k in range(n_folds):
        te = folds[k]
        tr = np.concatenate([folds[j] for j in range(n_folds) if j != k])
        Zt = np.column_stack([np.ones(len(tr)), Z[tr]])
        Zv = np.column_stack([np.ones(len(te)), Z[te]])
        A = Zt.T @ Zt + lam * np.eye(Zt.shape[1]); A[0, 0] -= lam
        try:
            beta = np.linalg.solve(A, Zt.T @ y[tr])
        except np.linalg.LinAlgError:
            return np.nan
        preds[te] = Zv @ beta
    ss_res = np.sum((y - preds) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    return float(1.0 - ss_res / (ss_tot + 1e-12))


def analyse(cfg, zp, ckpt, rng):
    import zarr
    r = zarr.open(zp, mode="r")
    emg = np.asarray(r["emg"]); ecog = r["ecog"]
    day = np.asarray(r["day"]); phase = np.asarray(r["phase"])
    animal = r.attrs.get("animal", Path(zp).stem)
    direction = r.attrs.get("direction", "?")
    if "prestim_emg" not in r:
        return None
    prestim = np.asarray(r["prestim_emg"])

    m_sl, h_sl, *_ = find_windows(emg)
    M, H, bg = measures(emg, m_sl, h_sl)
    onset = int(day[phase > 0].min()) if (phase > 0).any() else int(day.max() // 2)
    valid = M > 3 * bg

    # remove stimulus + excitability from BOTH sides, so coupling is not shared drive
    X = design(M, prestim)
    Hc = residualise(H, X)
    Zc = residualise(latents(cfg, ecog, ckpt), X)

    block = (day // BLOCK_DAYS).astype(np.int64)
    ids, r2s, nulls, ns = [], [], [], []
    for b in sorted(set(block.tolist())):
        sel = (block == b) & valid
        if sel.sum() < MIN_TRIALS:
            continue
        Zb, yb = Zc[sel], Hc[sel]
        # standardise within block so scale drift cannot help or hurt
        Zb = (Zb - Zb.mean(0)) / (Zb.std(0) + 1e-8)
        yb = (yb - yb.mean()) / (yb.std() + 1e-8)
        r2 = ridge_cv_r2(Zb, yb, rng=rng)
        nl = ridge_cv_r2(Zb, rng.permutation(yb), rng=rng)   # within-block shuffle null
        ids.append(b); r2s.append(r2); nulls.append(nl); ns.append(int(sel.sum()))

    ids = np.array(ids); r2s = np.array(r2s); nulls = np.array(nulls)
    rel = ids * BLOCK_DAYS + BLOCK_DAYS / 2 - onset
    base_m = rel < 0
    cond_m = rel > 0
    base_r2 = float(np.nanmean(r2s[base_m])) if base_m.any() else np.nan
    cond_r2 = float(np.nanmean(r2s[cond_m])) if cond_m.any() else np.nan
    return dict(animal=animal, direction=direction, rel=rel, r2=r2s, null=nulls,
                n=ns, base=base_r2, cond=cond_r2, delta=cond_r2 - base_r2,
                null_mean=float(np.nanmean(nulls)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zarrs", nargs="+", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--ckpt", default="outputs/encoder_pooled.pt")
    ap.add_argument("--out", default="outputs/coupling")
    ap.add_argument("--exclude", nargs="*", default=["12"])
    args = ap.parse_args()

    from src.utils.config import Config
    cfg = Config.load(args.config)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(cfg.train.seed)

    res = []
    for zp in args.zarrs:
        c = analyse(cfg, zp, args.ckpt, rng)
        if not c:
            continue
        if c["animal"] in args.exclude:
            print(f"  EXCLUDED A{c['animal']}"); continue
        res.append(c)
        print(f"  A{c['animal']:>2s} ({c['direction']:4s})  baseline R2={c['base']:.4f}  "
              f"conditioning R2={c['cond']:.4f}  delta={c['delta']:+.4f}  null={c['null_mean']:+.4f}")

        fig, ax = plt.subplots(figsize=(8.5, 4.4))
        ax.plot(c["rel"], c["r2"], "-o", color=VIOLET, lw=2.2, label="cortex -> reflex (CV R²)")
        ax.plot(c["rel"], c["null"], "-o", color=GREY, lw=1.4, ms=3, alpha=.8,
                label="within-block shuffle null")
        ax.axvline(0, color="#d97706", ls="--", lw=2, label="conditioning onset")
        ax.axhline(0, color="#cbd5e1", ls=":")
        ax.set_xlabel("day relative to conditioning onset"); ax.set_ylabel("cross-validated R²")
        ax.set_title(f"Animal {c['animal']} ({c['direction']}) — cortical coupling to the reflex")
        ax.legend(fontsize=8); fig.tight_layout()
        fig.savefig(out / f"coupling_{c['animal']}.png", dpi=140); plt.close(fig)

    if not res:
        print("no animals analysed"); return

    # ---- group figure -------------------------------------------------------
    grid = np.arange(-30, 61, 5)
    def gmean(grp):
        M = []
        for c in grp:
            ok = ~np.isnan(c["r2"])
            if ok.sum() > 1:
                M.append(np.interp(grid, c["rel"][ok], c["r2"][ok], left=np.nan, right=np.nan))
        return (np.nanmean(M, 0), len(M)) if M else (None, 0)

    ups = [c for c in res if c["direction"] == "up"]
    dns = [c for c in res if c["direction"] == "down"]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for c in res:
        ax.plot(c["rel"], c["r2"], "-o", ms=3, alpha=.5,
                color=UP_C if c["direction"] == "up" else DOWN_C,
                label=f"A{c['animal']} ({c['direction']})")
    for grp, col, nm in [(ups, UP_C, "up"), (dns, DOWN_C, "down")]:
        m, n = gmean(grp)
        if m is not None:
            ax.plot(grid, m, color=col, lw=3.4, label=f"{nm} mean (n={n})")
    ax.axvline(0, color="#94a3b8", ls="--"); ax.axhline(0, color="#cbd5e1", ls=":")
    # Carp (2026-08-12): only one animal runs past day 50 and it distracts; crop.
    ax.set_xlim(-35, 55)
    ax.set_xlabel("day relative to conditioning onset")
    ax.set_ylabel("cortex→reflex cross-validated R²")
    ax.set_title("Does cortical coupling to the reflex change with conditioning?")
    ax.legend(fontsize=7); fig.tight_layout()
    fig.savefig(out / "coupling_group.png", dpi=145); plt.close(fig)

    # ---- stats --------------------------------------------------------------
    d = np.array([c["delta"] for c in res]); d = d[~np.isnan(d)]
    L = ["=== CORTEX -> REFLEX COUPLING (drift-immune) ===",
         f"encoder: {args.ckpt}   block = {BLOCK_DAYS} days, {N_FOLDS}-fold CV within block",
         "measures residualised on M-wave + pre-stimulus background", "",
         f"{'animal':8s}{'dir':6s}{'baseR2':>9s}{'condR2':>9s}{'delta':>9s}{'null':>9s}"]
    for c in res:
        L.append(f"{'A'+c['animal']:8s}{c['direction']:6s}{c['base']:9.4f}{c['cond']:9.4f}"
                 f"{c['delta']:+9.4f}{c['null_mean']:+9.4f}")
    if len(d) > 1:
        se = d.std(ddof=1) / np.sqrt(len(d))
        t = d.mean() / (se + 1e-12)
        L += ["", f"change in coupling (all animals): mean {d.mean():+.4f}, t={t:.2f}, n={len(d)}"]
        L.append(f"  -> coupling {'INCREASES' if d.mean() > 0 else 'decreases'} with conditioning"
                 f" ({'significant' if abs(t) > 2.5 else 'not significant at this n'})")
    for grp, nm in [(ups, "up"), (dns, "down")]:
        dd = np.array([c["delta"] for c in grp]); dd = dd[~np.isnan(dd)]
        if len(dd):
            L.append(f"  {nm:4s} group mean delta = {dd.mean():+.4f} (n={len(dd)})")
    L += ["", "delta = conditioning R² minus baseline R². Null is a within-block label",
          "shuffle; real coupling must exceed it. Because train/test are inside one",
          "block, slow recording drift cannot produce a positive delta."]
    txt = "\n".join(L)
    print("\n" + txt); (out / "summary.txt").write_text(txt + "\n")
    with (out / "summary.csv").open("w") as f:
        f.write("animal,direction,baseline_r2,conditioning_r2,delta,null\n")
        for c in res:
            f.write(f"{c['animal']},{c['direction']},{c['base']:.5f},{c['cond']:.5f},"
                    f"{c['delta']:.5f},{c['null_mean']:.5f}\n")
    print(f"\nfigures -> {out}/")


if __name__ == "__main__":
    main()
