"""The publication analysis — every control Dr. Carp asked for, in one place.

Carp's asks (2026-08-05 meeting) and where each lives here:
  A. "Fit those two things [stimulus size and background] and see what's left."
     -> H and the cortical latent are both residualised on BOTH the M-wave
        (stimulus efficacy) and the pre-stimulus EMG (motoneuron-pool excitability),
        including quadratic terms. Nothing downstream uses raw H.
  B. "Take the same data in a randomized order... that should definitely not show
     any drift."
     -> RANDOMISED-ORDER NULL: shuffle which trial belongs to which day, recompute
        the drift. Breaks any real time structure while keeping the numbers identical.
  C. "The really stable part is just the last 10 days before training starts."
     -> Baseline reference = the last BASELINE_DAYS days before onset, not all of it
        (early baseline had settings/stimulus changes).
  D. Success = a >=20% change in the reflex (the lab's criterion).
     -> reported per animal, on the fully-corrected H.

Outputs per animal into outputs/final/:
  behaviour_<A>.png   corrected H over time vs the 20% criterion
  drift_<A>.png       cortical drift with BOTH nulls (sham + randomised order)
  summary.txt / summary.csv

Usage:
  python scripts/final_analysis.py --zarrs data/processed/animal9.zarr ...
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

BASELINE_DAYS = 10      # Carp: only the last 10 baseline days are trustworthy
BLOCK_DAYS = 5
SUCCESS = 0.20          # lab criterion: 20% change counts as conditioned
VIOLET, TEAL, AMBER, GREY, RED = "#6d28d9", "#0d9488", "#d97706", "#64748b", "#dc2626"


def design(*cols):
    """Design matrix: intercept + each covariate (z-scored) and its square."""
    X = [np.ones(len(cols[0]))]
    for c in cols:
        c = np.nan_to_num(c, nan=float(np.nanmedian(c)))
        z = (c - c.mean()) / (c.std() + 1e-9)
        X += [z, z ** 2]
    return np.column_stack(X)


def residualise(Y, X):
    """Remove everything the covariates X can explain from each column of Y."""
    single = Y.ndim == 1
    Y2 = Y[:, None] if single else Y
    beta, *_ = np.linalg.lstsq(X, Y2, rcond=None)
    R = Y2 - X @ beta
    return R[:, 0] if single else R


def latents(cfg, ecog):
    import torch
    from src.models.heads import build_autoencoder
    from src.utils.seed import get_device
    from src.data.preprocessing import zscore_per_trial
    dev = get_device()
    m = build_autoencoder(cfg)
    m.load_state_dict(torch.load("outputs/encoder_phase1.pt", map_location="cpu")["model"])
    m = m.to(dev).eval()
    Z = []
    with torch.no_grad():
        for i in range(0, ecog.shape[0], 4096):
            x = zscore_per_trial(np.asarray(ecog[i:i + 4096]).astype(np.float32))
            Z.append(m.encode(torch.tensor(x, device=dev)).cpu().numpy())
    return np.concatenate(Z)


def block_drift(Z, block, ref_mask):
    ref = Z[ref_mask].mean(0)
    bl = sorted(set(block.tolist()))
    return np.array(bl), np.array([np.linalg.norm(Z[block == b].mean(0) - ref) for b in bl])


def analyse(cfg, zp, out, rng):
    import zarr
    r = zarr.open(zp, mode="r")
    emg = np.asarray(r["emg"]); ecog = r["ecog"]
    day = np.asarray(r["day"]); phase = np.asarray(r["phase"])
    animal = r.attrs.get("animal", Path(zp).stem); direction = r.attrs.get("direction", "?")
    prestim = np.asarray(r["prestim_emg"]) if "prestim_emg" in r else None
    if prestim is None:
        print(f"  [skip A{animal}] no prestim_emg — run scripts/add_prestim.py first")
        return None

    m_sl, h_sl, m_pk, h_pk = find_windows(emg)
    M, H, bg = measures(emg, m_sl, h_sl)
    onset = int(day[phase > 0].min()) if (phase > 0).any() else int(day.max() // 2)

    # --- C. baseline = last 10 days before onset -----------------------------
    base = (day >= onset - BASELINE_DAYS) & (day < onset)
    if base.sum() < 500:
        base = day < onset

    # --- A. residualise on stimulus (M) AND pre-stimulus excitability --------
    X = design(M, prestim)
    H_corr = residualise(H, X)
    valid = M > 3 * bg

    # behaviour: corrected H per block, expressed as % change from baseline level
    block = (day // BLOCK_DAYS).astype(np.int64)
    Hb = np.array([np.median(H_corr[(block == b) & valid]) if ((block == b) & valid).sum() > 30
                   else np.nan for b in sorted(set(block.tolist()))])
    bl_ids = np.array(sorted(set(block.tolist())))
    ref_level = np.median(H[base & valid])                       # uV scale for %
    ref_corr = np.median(H_corr[base & valid])
    pct = (Hb - ref_corr) / max(ref_level, 1e-6) * 100

    cond = bl_ids * BLOCK_DAYS >= onset
    final_pct = np.nanmedian(pct[cond][-2:]) if cond.any() else np.nan
    if direction == "down":
        worked = final_pct <= -SUCCESS * 100
    else:
        worked = final_pct >= SUCCESS * 100

    # --- cortical drift, residualised on the SAME covariates -----------------
    Z = residualise(latents(cfg, ecog), X)
    bl_ids2, drift = block_drift(Z, block, base)

    # B1. sham null — split baseline only
    bdays = np.unique(day[day < onset])
    if len(bdays) >= 4:
        cut = bdays[int(0.5 * len(bdays))]
        sham_ref = (day < cut)
        sel = day < onset
        _, sham = block_drift(Z[sel], block[sel], sham_ref[sel])
        sham_max = float(np.nanmax(sham)) if len(sham) else np.nan
    else:
        sham, sham_max = np.array([]), np.nan

    # B2. randomised-order null (Carp) — shuffle trial->day, keep numbers identical
    rand_stats = []
    for _ in range(50):
        pd_ = rng.permutation(day)
        blk = (pd_ // BLOCK_DAYS).astype(np.int64)
        ref = pd_ >= (onset - BASELINE_DAYS)
        ref &= pd_ < onset
        if ref.sum() < 100:
            ref = pd_ < onset
        ids, d_ = block_drift(Z, blk, ref)
        rand_stats.append(np.nanmean(d_[ids * BLOCK_DAYS >= onset]))
    rand_mean, rand_sd = float(np.mean(rand_stats)), float(np.std(rand_stats))
    real_drift = float(np.nanmean(drift[cond]))

    # ---- figures -----------------------------------------------------------
    mid = bl_ids * BLOCK_DAYS + BLOCK_DAYS / 2
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.plot(mid, pct, "-o", color=VIOLET, lw=2.2)
    ax.axvline(onset, color=AMBER, ls="--", lw=2, label="conditioning onset")
    ax.axhline(0, color=GREY, ls=":", lw=1)
    ax.axhline(-20 if direction == "down" else 20, color=TEAL, ls="--", lw=1.4,
               label="20% success criterion")
    ax.set_xlabel("day"); ax.set_ylabel("corrected H, % change from baseline")
    ax.set_title(f"Animal {animal} ({direction}) — H corrected for stimulus + background")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(out / f"behaviour_{animal}.png", dpi=140); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.plot(mid, drift, "-o", color=VIOLET, lw=2.4, label="real")
    if len(sham):
        ax.plot(mid[:len(sham)], sham, "-o", color=RED, lw=2, label="null: baseline sham")
    ax.axhline(rand_mean, color=GREY, ls="--", lw=1.6, label=f"null: randomised order ({rand_mean:.1f})")
    ax.axvline(onset, color=AMBER, ls="--", lw=2)
    ax.set_xlabel("day"); ax.set_ylabel("cortical drift from baseline")
    ax.set_title(f"Animal {animal} ({direction}) — drift with stimulus+background removed")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(out / f"drift_{animal}.png", dpi=140); plt.close(fig)

    return dict(animal=animal, direction=direction, m_pk=m_pk, h_pk=h_pk,
                valid=100 * valid.mean(), final_pct=final_pct, worked=worked,
                real=real_drift, sham=sham_max, rand=rand_mean, rand_sd=rand_sd,
                passes=(real_drift > 2 * sham_max if np.isfinite(sham_max) else False)
                       and real_drift > rand_mean + 3 * rand_sd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zarrs", nargs="+", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", default="outputs/final")
    args = ap.parse_args()
    from src.utils.config import Config
    cfg = Config.load(args.config)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(cfg.train.seed)

    res = [x for x in (analyse(cfg, z, out, rng) for z in args.zarrs) if x]
    L = ["=== FINAL ANALYSIS — stimulus + pre-stimulus background controlled ===",
         f"baseline = last {BASELINE_DAYS} days before onset;  success = {int(SUCCESS*100)}% change",
         "",
         f"{'animal':7s}{'dir':6s}{'Mpk':>5s}{'Hpk':>5s}{'valid%':>7s}{'H chg':>8s}{'cond?':>7s}"
         f"{'drift':>8s}{'sham':>8s}{'rand':>8s}{'PASS':>6s}"]
    for r in res:
        L.append(f"{'A'+r['animal']:7s}{r['direction']:6s}{r['m_pk']:5.1f}{r['h_pk']:5.1f}"
                 f"{r['valid']:7.1f}{r['final_pct']:+7.1f}%{'YES' if r['worked'] else 'no':>7s}"
                 f"{r['real']:8.1f}{r['sham']:8.1f}{r['rand']:8.1f}"
                 f"{'YES' if r['passes'] else 'no':>6s}")
    L += ["",
          "H chg  = corrected H at end of conditioning, % from baseline (>=20% = conditioned)",
          "drift  = mean cortical drift during conditioning, covariates removed",
          "sham   = baseline-only split (should be ~0);  rand = randomised trial order (should be ~0)",
          "PASS   = drift exceeds BOTH nulls (>2x sham and >3 SD above randomised)"]
    txt = "\n".join(L)
    print(txt); (out / "summary.txt").write_text(txt + "\n")
    with (out / "summary.csv").open("w") as f:
        f.write("animal,direction,m_peak_ms,h_peak_ms,valid_pct,H_change_pct,conditioned,"
                "drift,sham_null,rand_null,passes\n")
        for r in res:
            f.write(f"{r['animal']},{r['direction']},{r['m_pk']:.2f},{r['h_pk']:.2f},"
                    f"{r['valid']:.1f},{r['final_pct']:.1f},{r['worked']},{r['real']:.2f},"
                    f"{r['sham']:.2f},{r['rand']:.2f},{r['passes']}\n")
    print(f"\nfigures + summary -> {out}/")


if __name__ == "__main__":
    main()
