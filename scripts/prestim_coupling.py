"""Does PRE-STIMULUS cortical state predict the size of the reflex?

This is the strongest form of the cortical question we can ask with this dataset,
for three reasons:

  1. CROSSTALK-IMMUNE IN TIME. The predictor is measured entirely BEFORE the
     stimulus, so it cannot contain the evoked muscle response. The standard
     objection to the post-stimulus coupling result ("your ECoG electrode is just
     picking up EMG") does not apply.
  2. DRIFT-IMMUNE. Decoders are fit and cross-validated WITHIN one 5-day block, so
     slow recording nonstationarity moves train and test together and cancels.
  3. MECHANISTIC. "Cortical state modulates spinal excitability trial by trial" is a
     real, testable mechanism, and the natural cortical analogue of the
     motoneuron-pool excitability that Dr Carp asked us to control for.

Controls included:
  * Everything is residualised on the M-wave and the pre-stimulus EMG background,
    so we are not just re-measuring stimulus strength or muscle tone.
  * Within-block label shuffle gives a per-block null.
  * CROSSTALK TEST: the same decode is run from pre-stimulus EMG band power. If
    ECoG only works because it mirrors EMG, the two should be equivalent and the
    ECoG advantage should vanish once EMG bands are included as covariates.
  * BAND BREAKDOWN: low bands (delta-beta) are implausible as EMG contamination;
    the >100 Hz band is where contamination would live. We report both.

Usage:
  python scripts/prestim_coupling.py --zarrs data/processed/animal*.zarr
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
from scripts.final_analysis import design, residualise, BLOCK_DAYS
from scripts.coupling_analysis import ridge_cv_r2, MIN_TRIALS

BAND_NAMES = ["delta", "theta", "alpha", "beta", "gamma", "high"]
LOW = [0, 1, 2, 3]        # delta..beta — implausible as EMG contamination
HIGH = [5]                # >100 Hz — where contamination would live
DOWN_C, UP_C, GREY, VIOLET, TEAL = "#2563eb", "#dc2626", "#64748b", "#6d28d9", "#0d9488"


def zs(A):
    A = np.asarray(A, dtype=np.float64)
    if A.ndim == 1:
        A = A[:, None]
    return (A - A.mean(0)) / (A.std(0) + 1e-8)


def analyse(zp, rng):
    import zarr
    r = zarr.open(zp, mode="r")
    if "prestim_bands" not in r:
        print(f"  [skip {zp}] no prestim_bands"); return None
    emg = np.asarray(r["emg"]); day = np.asarray(r["day"]); phase = np.asarray(r["phase"])
    animal = r.attrs.get("animal", Path(zp).stem); direction = r.attrs.get("direction", "?")
    B = np.asarray(r["prestim_bands"])            # (N,6) cortical
    Bm = np.asarray(r["prestim_emg_bands"])       # (N,6) muscle — crosstalk control
    prestim = np.asarray(r["prestim_emg"])

    m_sl, h_sl, *_ = find_windows(emg)
    M, H, bg = measures(emg, m_sl, h_sl)
    valid = M > 3 * bg
    onset = int(day[phase > 0].min()) if (phase > 0).any() else int(day.max() // 2)

    # remove stimulus efficacy + muscle background from the target
    X = design(M, prestim)
    Hc = residualise(H, X)
    block = (day // BLOCK_DAYS).astype(np.int64)

    rows = []
    for b in sorted(set(block.tolist())):
        sel = (block == b) & valid
        if sel.sum() < MIN_TRIALS:
            continue
        y = zs(Hc[sel])[:, 0]
        cortical = zs(B[sel])
        muscle = zs(Bm[sel])
        rows.append(dict(
            block=b,
            rel=b * BLOCK_DAYS + BLOCK_DAYS / 2 - onset,
            n=int(sel.sum()),
            r2_ecog=ridge_cv_r2(cortical, y, rng=rng),
            r2_null=ridge_cv_r2(cortical, rng.permutation(y), rng=rng),
            r2_emg=ridge_cv_r2(muscle, y, rng=rng),                       # crosstalk ref
            r2_low=ridge_cv_r2(cortical[:, LOW], y, rng=rng),             # delta..beta
            r2_high=ridge_cv_r2(cortical[:, HIGH], y, rng=rng),           # >100 Hz
            # ECoG *after* also giving the model the EMG bands: unique cortical part
            r2_joint=ridge_cv_r2(np.column_stack([cortical, muscle]), y, rng=rng),
            r2_emg_only=ridge_cv_r2(muscle, y, rng=rng),
        ))
    if not rows:
        return None
    g = lambda k: np.array([x[k] for x in rows], dtype=float)
    rel = g("rel")
    base, cond = rel < 0, rel > 0
    return dict(animal=animal, direction=direction, rel=rel,
                r2=g("r2_ecog"), null=g("r2_null"), emg=g("r2_emg"),
                low=g("r2_low"), high=g("r2_high"), joint=g("r2_joint"),
                base=float(np.nanmean(g("r2_ecog")[base])) if base.any() else np.nan,
                cond=float(np.nanmean(g("r2_ecog")[cond])) if cond.any() else np.nan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zarrs", nargs="+", required=True)
    ap.add_argument("--out", default="outputs/prestim")
    ap.add_argument("--exclude", nargs="*", default=["12"])
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    res = []
    for zp in args.zarrs:
        c = analyse(zp, rng)
        if not c:
            continue
        if c["animal"] in args.exclude:
            print(f"  EXCLUDED A{c['animal']}"); continue
        res.append(c)
        print(f"  A{c['animal']:>2s} ({c['direction']:4s})  ECoG R2={np.nanmean(c['r2']):.4f}  "
              f"null={np.nanmean(c['null']):+.4f}  EMG-bands R2={np.nanmean(c['emg']):.4f}  "
              f"low-band={np.nanmean(c['low']):.4f}  base->cond {c['base']:.3f}->{c['cond']:.3f}")
    if not res:
        print("nothing analysed"); return

    # ---- figure 1: the main result + null + crosstalk reference -------------
    fig, ax = plt.subplots(1, 2, figsize=(13.5, 5))
    for c in res:
        ax[0].plot(c["rel"], c["r2"], "-o", ms=3, alpha=.6,
                   color=UP_C if c["direction"] == "up" else DOWN_C,
                   label=f"A{c['animal']} ({c['direction']})")
    allnull = np.concatenate([c["null"] for c in res])
    ax[0].axhline(np.nanmean(allnull), color=GREY, ls="--", lw=1.6,
                  label=f"shuffle null ({np.nanmean(allnull):+.3f})")
    ax[0].axvline(0, color="#94a3b8", ls="--"); ax[0].axhline(0, color="#e2e8f0", ls=":")
    ax[0].set_xlabel("day relative to conditioning onset")
    ax[0].set_ylabel("pre-stimulus cortex → reflex, CV R²")
    ax[0].set_title("Pre-stimulus cortical state predicts reflex size")
    ax[0].legend(fontsize=7)

    labels = ["ECoG\n(all bands)", "ECoG\nlow (δ-β)", "ECoG\n>100 Hz", "EMG bands\n(crosstalk ref)", "shuffle\nnull"]
    vals = [np.nanmean(np.concatenate([c[k] for c in res])) for k in ["r2", "low", "high", "emg", "null"]]
    cols = [VIOLET, TEAL, "#a78bfa", "#f59e0b", GREY]
    ax[1].bar(labels, vals, color=cols, alpha=.9)
    ax[1].axhline(0, color="#94a3b8", lw=1)
    ax[1].set_ylabel("CV R² (mean over animals & blocks)")
    ax[1].set_title("Is it really cortical? band + crosstalk breakdown")
    for i, v in enumerate(vals):
        ax[1].text(i, v + 0.002, f"{v:.3f}", ha="center", fontsize=9)
    fig.tight_layout(); fig.savefig(out / "prestim_coupling.png", dpi=145); plt.close(fig)

    # ---- stats --------------------------------------------------------------
    m = lambda k: float(np.nanmean(np.concatenate([c[k] for c in res])))
    L = ["=== PRE-STIMULUS CORTICAL STATE -> REFLEX SIZE ===",
         "predictor measured entirely BEFORE the stimulus (crosstalk-immune in time)",
         "target = H residualised on M-wave + pre-stimulus EMG background",
         "decoders fit and cross-validated WITHIN 5-day blocks (drift-immune)", "",
         f"{'animal':8s}{'dir':6s}{'ECoG R2':>9s}{'null':>9s}{'low band':>10s}{'>100Hz':>9s}{'EMG ref':>9s}"]
    for c in res:
        L.append(f"{'A'+c['animal']:8s}{c['direction']:6s}{np.nanmean(c['r2']):9.4f}"
                 f"{np.nanmean(c['null']):+9.4f}{np.nanmean(c['low']):10.4f}"
                 f"{np.nanmean(c['high']):9.4f}{np.nanmean(c['emg']):9.4f}")
    L += ["",
          f"OVERALL  ECoG R2 = {m('r2'):.4f}   shuffle null = {m('null'):+.4f}",
          f"         low bands (delta-beta) = {m('low'):.4f}   >100 Hz = {m('high'):.4f}",
          f"         EMG-band reference     = {m('emg'):.4f}",
          f"         ECoG + EMG jointly     = {m('joint'):.4f}"]
    d = np.array([c["cond"] - c["base"] for c in res], dtype=float); d = d[~np.isnan(d)]
    if len(d) > 1:
        t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)) + 1e-12)
        L.append(f"         change with conditioning: {d.mean():+.4f} (t={t:.2f}, n={len(d)})")
    L += ["",
          "Interpretation guide:",
          " * ECoG R2 well above the shuffle null => pre-stimulus cortical state carries",
          "   trial-by-trial information about how large the reflex will be.",
          " * If the LOW bands carry it, EMG contamination is an implausible explanation",
          "   (muscle artefact lives at high frequency).",
          " * If ECoG >> the EMG-band reference, the effect is not simply muscle tone."]
    txt = "\n".join(L)
    print("\n" + txt); (out / "summary.txt").write_text(txt + "\n")
    print(f"\nfigure -> {out}/prestim_coupling.png")


if __name__ == "__main__":
    main()
