"""Two verifications Dr Carp asked for (2026-08-12 meeting).

1. TIGHTENED COUPLING NUMBER.
   The 0.35 figure removed the M-wave and background GLOBALLY (one fit over all
   trials) and then measured cortex within 5-day blocks. If the M->H relationship
   shifts between blocks, global removal leaves stimulus variance behind, and cortex
   tracks the stimulus, so the number can be inflated. Here we remove M and
   background WITHIN each block, then decode. This is the conservative estimate and
   the one to quote.

2. CROSSTALK TEST, his method.
   "What if you did just a correlation between the cortical signal and the muscle
   signal and just look to see how much cross talk there is... the power at any given
   frequency should be going up and down, or we hope that they're independent between
   the cortex and the muscle. And if there is some kind of coordination there, it
   would suggest that we are getting this contamination."
   So: per frequency band, correlate cortical power against muscle power across
   trials. High correlation (especially at high frequency, where muscle artefact
   lives) implies contamination. We also report a lag check — whether cortical power
   leads or follows muscle power across trials, since cortex leading is acceptable
   and cortex following is the contamination signature.

Usage:
  python scripts/verify_coupling.py --zarrs data/processed/animal*.zarr \
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
from scripts.final_analysis import design, residualise, latents, BLOCK_DAYS
from scripts.coupling_analysis import ridge_cv_r2, MIN_TRIALS

BANDS = ["delta", "theta", "alpha", "beta", "gamma", "high"]
VIOLET, TEAL, AMBER, GREY, RED = "#6d28d9", "#0d9488", "#d97706", "#64748b", "#dc2626"


def zs(A):
    A = np.asarray(A, float)
    if A.ndim == 1:
        A = A[:, None]
    return (A - A.mean(0)) / (A.std(0) + 1e-8)


def analyse(cfg, zp, ckpt, rng):
    import zarr
    r = zarr.open(zp, mode="r")
    emg = np.asarray(r["emg"]); day = np.asarray(r["day"]); phase = np.asarray(r["phase"])
    animal = r.attrs.get("animal", Path(zp).stem); direction = r.attrs.get("direction", "?")
    prestim = np.asarray(r["prestim_emg"])
    m_sl, h_sl, *_ = find_windows(emg)
    M, H, bg = measures(emg, m_sl, h_sl)
    valid = M > 3 * bg
    onset = int(day[phase > 0].min()) if (phase > 0).any() else int(day.max() // 2)
    Zraw = latents(cfg, r["ecog"], ckpt)
    block = (day // BLOCK_DAYS).astype(np.int64)

    # ---- 1. within-block residualisation (the tightened number) -------------
    glob_X = design(M, prestim)
    H_glob = residualise(H, glob_X)          # the old, global way
    Z_glob = residualise(Zraw, glob_X)
    tight, loose, nulls, rels = [], [], [], []
    for b in sorted(set(block.tolist())):
        sel = (block == b) & valid
        if sel.sum() < MIN_TRIALS:
            continue
        # OLD: globally residualised, then block-standardised
        loose.append(ridge_cv_r2(zs(Z_glob[sel]), zs(H_glob[sel])[:, 0], rng=rng))
        # NEW: residualise M + background inside this block only
        Xb = design(M[sel], prestim[sel])
        yb = zs(residualise(H[sel], Xb))[:, 0]
        Zb = zs(residualise(Zraw[sel], Xb))
        tight.append(ridge_cv_r2(Zb, yb, rng=rng))
        nulls.append(ridge_cv_r2(Zb, rng.permutation(yb), rng=rng))
        rels.append(b * BLOCK_DAYS + BLOCK_DAYS / 2 - onset)

    # ---- 2. crosstalk: cortex vs muscle band power correlation --------------
    xtalk = np.full(len(BANDS), np.nan)
    lead = np.nan
    if "prestim_bands" in r and "prestim_emg_bands" in r:
        Bc = np.asarray(r["prestim_bands"]); Bm = np.asarray(r["prestim_emg_bands"])
        ok = np.isfinite(Bc).all(1) & np.isfinite(Bm).all(1)
        for i in range(len(BANDS)):
            xtalk[i] = np.corrcoef(Bc[ok, i], Bm[ok, i])[0, 1]
        # lag check on the high band: does cortical power lead or follow muscle?
        c = Bc[ok, 5] - Bc[ok, 5].mean(); m = Bm[ok, 5] - Bm[ok, 5].mean()
        c /= (c.std() + 1e-9); m /= (m.std() + 1e-9)
        n = min(len(c), 200000)
        r0 = float(np.mean(c[:n] * m[:n]))
        r_lead = float(np.mean(c[:n - 1] * m[1:n]))   # cortex now vs muscle next
        r_fol = float(np.mean(c[1:n] * m[:n - 1]))    # cortex now vs muscle before
        lead = r_lead - r_fol
        xt0 = r0
    else:
        xt0 = np.nan

    return dict(animal=animal, direction=direction,
                tight=float(np.nanmean(tight)), loose=float(np.nanmean(loose)),
                null=float(np.nanmean(nulls)), rel=np.array(rels),
                tight_series=np.array(tight), loose_series=np.array(loose),
                xtalk=xtalk, xt0=xt0, lead=lead)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zarrs", nargs="+", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--ckpt", default="outputs/encoder_pooled.pt")
    ap.add_argument("--out", default="outputs/verify")
    ap.add_argument("--exclude", nargs="*", default=["12"])
    args = ap.parse_args()
    from src.utils.config import Config
    cfg = Config.load(args.config)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(cfg.train.seed)

    res = []
    for zp in args.zarrs:
        c = analyse(cfg, zp, args.ckpt, rng)
        if c["animal"] in args.exclude:
            print(f"  EXCLUDED A{c['animal']}"); continue
        res.append(c)
        print(f"  A{c['animal']:>2s} ({c['direction']:4s})  global-resid R2={c['loose']:.4f}   "
              f"within-block R2={c['tight']:.4f}   null={c['null']:+.4f}   "
              f"cortex-muscle r={c['xt0']:+.3f}")

    # ---- figure -------------------------------------------------------------
    fig, ax = plt.subplots(1, 2, figsize=(13.5, 5))
    labels = [f"A{c['animal']}" for c in res]
    x = np.arange(len(res)); w = 0.36
    ax[0].bar(x - w/2, [c["loose"] for c in res], w, color=GREY, label="global residualisation (old)")
    ax[0].bar(x + w/2, [c["tight"] for c in res], w, color=VIOLET, label="within-block (conservative)")
    ax[0].axhline(np.nanmean([c["null"] for c in res]), color=RED, ls="--", lw=1.4, label="shuffle null")
    ax[0].set_xticks(x); ax[0].set_xticklabels(labels)
    ax[0].set_ylabel("cortex → reflex CV R²")
    ax[0].set_title("Tightened coupling estimate")
    ax[0].legend(fontsize=8)

    X = np.array([c["xtalk"] for c in res])
    for i, c in enumerate(res):
        ax[1].plot(BANDS, c["xtalk"], "-o", alpha=.6, label=f"A{c['animal']}")
    ax[1].plot(BANDS, np.nanmean(X, 0), "-o", color=VIOLET, lw=3, label="mean")
    ax[1].axhline(0, color=GREY, ls=":")
    ax[1].set_ylabel("correlation, cortical power vs muscle power")
    ax[1].set_title("Crosstalk check — high values imply contamination")
    ax[1].set_ylim(-1, 1); ax[1].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(out / "verification.png", dpi=145); plt.close(fig)

    L = ["=== VERIFICATION (Carp, 2026-08-12) ===", "",
         "1. TIGHTENED COUPLING — M and background removed WITHIN each block",
         f"{'animal':8s}{'dir':6s}{'global (old)':>14s}{'within-block':>14s}{'null':>9s}"]
    for c in res:
        L.append(f"{'A'+c['animal']:8s}{c['direction']:6s}{c['loose']:14.4f}{c['tight']:14.4f}{c['null']:+9.4f}")
    tm = float(np.nanmean([c["tight"] for c in res])); lm = float(np.nanmean([c["loose"] for c in res]))
    L += [f"{'MEAN':14s}{lm:14.4f}{tm:14.4f}",
          f"  -> the conservative estimate is {tm:.3f}; the earlier global-residual figure was {lm:.3f}.", "",
          "2. CROSSTALK — correlation between cortical and muscle band power across trials",
          f"{'animal':8s}" + "".join(f"{b:>9s}" for b in BANDS)]
    for c in res:
        L.append(f"{'A'+c['animal']:8s}" + "".join(f"{v:9.3f}" for v in c["xtalk"]))
    mx = np.nanmean(np.array([c["xtalk"] for c in res]), 0)
    L.append(f"{'MEAN':8s}" + "".join(f"{v:9.3f}" for v in mx))
    hi = mx[5]
    L += ["",
          f"  high-band (>100 Hz) cortex-muscle correlation = {hi:+.3f}",
          "  Interpretation: muscle artefact lives at high frequency. A correlation near",
          "  zero there means the ECoG is not simply reproducing the EMG. A large positive",
          "  value would indicate contamination.",
          f"  lead-lag asymmetry (positive = cortex leads muscle): "
          f"{np.nanmean([c['lead'] for c in res]):+.4f}"]
    txt = "\n".join(L)
    print("\n" + txt); (out / "summary.txt").write_text(txt + "\n")
    print(f"\nfigure -> {out}/verification.png")


if __name__ == "__main__":
    main()
