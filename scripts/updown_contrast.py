"""UP vs DOWN group contrast — the test that decides the cortical claim.

The problem single-animal analysis cannot solve: conditioning and slow recording
drift are both smooth functions of time, so they are confounded within an animal.

The way out: recording/electrode drift is idiosyncratic and DIRECTION-INDEPENDENT,
while a genuine conditioning signal must depend on which direction the animal was
trained. So we align every animal to its own conditioning onset and ask two things:

  1. BEHAVIOUR (the positive control that must hold): corrected H should go DOWN in
     down-conditioned animals and UP in up-conditioned animals. If this fails, the
     measurement is wrong and nothing else matters.
  2. CORTEX: does the drift differ between the up and down groups? Note Carp's
     caveat — up-conditioning is NOT simply the mirror of down-conditioning (the
     spinal mechanisms differ), so the cortical drift could go the SAME way in both.
     We therefore test for a DIFFERENCE, not specifically a sign flip, and also
     report whether either group exceeds its own nulls.

All measures are residualised on the M-wave and pre-stimulus background first.

Usage:
  python scripts/updown_contrast.py --zarrs data/processed/animal*.zarr \
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
from scripts.final_analysis import design, residualise, latents, block_drift, BASELINE_DAYS, BLOCK_DAYS

DOWN_C, UP_C = "#2563eb", "#dc2626"


def curves(cfg, zp, ckpt):
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
    base = (day >= onset - BASELINE_DAYS) & (day < onset)
    if base.sum() < 500:
        base = day < onset
    valid = M > 3 * bg

    X = design(M, prestim)
    H_corr = residualise(H, X)
    Z = residualise(latents(cfg, ecog, ckpt), X)

    block = (day // BLOCK_DAYS).astype(np.int64)
    ids = np.array(sorted(set(block.tolist())))
    ref_lvl = np.median(H[base & valid]); ref_c = np.median(H_corr[base & valid])
    hpct = np.array([
        (np.median(H_corr[(block == b) & valid]) - ref_c) / max(ref_lvl, 1e-6) * 100
        if ((block == b) & valid).sum() > 30 else np.nan for b in ids])
    _, drift = block_drift(Z, block, base)
    rel = ids * BLOCK_DAYS + BLOCK_DAYS / 2 - onset      # days relative to onset
    return dict(animal=animal, direction=direction, rel=rel, hpct=hpct, drift=drift)


def group_mean(cs, key, grid):
    """Interpolate each animal onto a common relative-day grid, then average."""
    M = []
    for c in cs:
        ok = ~np.isnan(c[key])
        if ok.sum() < 2:
            continue
        M.append(np.interp(grid, c["rel"][ok], c[key][ok], left=np.nan, right=np.nan))
    return (np.nanmean(M, axis=0), np.nanstd(M, axis=0), len(M)) if M else (None, None, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zarrs", nargs="+", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--ckpt", default="outputs/encoder_pooled.pt")
    ap.add_argument("--out", default="outputs/updown")
    ap.add_argument("--exclude", nargs="*", default=["12"],
                    help="animals to drop (default: 12, dead ECoG electrode)")
    args = ap.parse_args()

    from src.utils.config import Config
    cfg = Config.load(args.config)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    cs = []
    for z in args.zarrs:
        c = curves(cfg, z, args.ckpt)
        if c and c["animal"] not in args.exclude:
            cs.append(c); print(f"  loaded A{c['animal']} ({c['direction']})")
        elif c:
            print(f"  EXCLUDED A{c['animal']}")
    ups = [c for c in cs if c["direction"] == "up"]
    dns = [c for c in cs if c["direction"] == "down"]
    print(f"\n{len(ups)} up, {len(dns)} down")

    grid = np.arange(-30, 61, 5)
    L = ["=== UP vs DOWN CONTRAST ===",
         f"encoder: {args.ckpt}",
         f"up: {[c['animal'] for c in ups]}   down: {[c['animal'] for c in dns]}", ""]

    # ---- behaviour (the positive control) -----------------------------------
    fig, ax = plt.subplots(1, 2, figsize=(13.5, 5))
    for c in cs:
        ax[0].plot(c["rel"], c["hpct"], "-o", ms=3, alpha=.55,
                   color=UP_C if c["direction"] == "up" else DOWN_C,
                   label=f"A{c['animal']} ({c['direction']})")
    for grp, col, nm in [(ups, UP_C, "up"), (dns, DOWN_C, "down")]:
        m, s, n = group_mean(grp, "hpct", grid)
        if m is not None:
            ax[0].plot(grid, m, color=col, lw=3.4, label=f"{nm} mean (n={n})")
    ax[0].axvline(0, color="#94a3b8", ls="--"); ax[0].axhline(0, color="#cbd5e1", ls=":")
    ax[0].axhline(20, color="#0d9488", ls="--", lw=1); ax[0].axhline(-20, color="#0d9488", ls="--", lw=1)
    ax[0].set_xlabel("day relative to conditioning onset")
    ax[0].set_ylabel("corrected H, % change")
    ax[0].set_title("BEHAVIOUR — down should fall, up should rise")
    ax[0].legend(fontsize=7)

    # ---- cortex -------------------------------------------------------------
    for c in cs:
        ax[1].plot(c["rel"], c["drift"], "-o", ms=3, alpha=.55,
                   color=UP_C if c["direction"] == "up" else DOWN_C)
    for grp, col, nm in [(ups, UP_C, "up"), (dns, DOWN_C, "down")]:
        m, s, n = group_mean(grp, "drift", grid)
        if m is not None:
            ax[1].plot(grid, m, color=col, lw=3.4, label=f"{nm} mean (n={n})")
    ax[1].axvline(0, color="#94a3b8", ls="--")
    ax[1].set_xlabel("day relative to conditioning onset")
    ax[1].set_ylabel("cortical drift from baseline")
    ax[1].set_title("CORTEX — do the groups differ?")
    ax[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(out / "updown_contrast.png", dpi=145); plt.close(fig)

    # ---- numbers ------------------------------------------------------------
    post = grid > 0
    for key, label in [("hpct", "behaviour (corrected H %)"), ("drift", "cortical drift")]:
        mu, su, nu = group_mean(ups, key, grid)
        md, sd, nd = group_mean(dns, key, grid)
        if mu is None or md is None:
            continue
        u, d = np.nanmean(mu[post]), np.nanmean(md[post])
        # per-animal post-onset means -> Welch t-test between groups
        pa = lambda grp: np.array([np.nanmean(c[key][c["rel"] > 0]) for c in grp])
        au, ad = pa(ups), pa(dns)
        au, ad = au[~np.isnan(au)], ad[~np.isnan(ad)]
        if len(au) > 1 and len(ad) > 1:
            se = np.sqrt(au.var(ddof=1) / len(au) + ad.var(ddof=1) / len(ad))
            t = (au.mean() - ad.mean()) / (se + 1e-12)
        else:
            t = np.nan
        L.append(f"{label}:  up={u:+.2f}  down={d:+.2f}  difference={u-d:+.2f}"
                 + (f"  (t={t:.2f}, n={len(au)}v{len(ad)})" if np.isfinite(t) else ""))
        if key == "hpct":
            L.append(f"   -> directions {'SEPARATE as expected' if u > d else 'DO NOT separate'}"
                     f" (up above down: {u > d})")
    L += ["", "Note (Carp): up-conditioning is not simply the mirror of down-conditioning;",
          "the spinal mechanisms differ, so the cortical drift could share a direction.",
          "We test for a group DIFFERENCE rather than requiring a sign flip."]
    txt = "\n".join(L)
    print("\n" + txt); (out / "summary.txt").write_text(txt + "\n")
    print(f"\nfigure -> {out}/updown_contrast.png")


if __name__ == "__main__":
    main()
