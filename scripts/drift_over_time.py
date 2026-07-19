"""Drift over time + the null control + a shuffle significance test.

The scientific core for the write-up. Everything here uses the `day` array now in
the Zarr (see scripts/add_timestamps.py) and the M-wave control from
confound_control.py. Produces, for Animal 9:

  1. daily_waveform_qc.png  — per-day average EMG/ECoG heatmaps; catch bad days.
  2. drift_over_time.png     — centroid drift in 5-day blocks (raw vs M-removed),
                               with the H/M learning curve underneath.
  3. null_control.png        — Carp's sham test: split the BASELINE-only data into
                               pseudo-baseline / pseudo-conditioning and run the
                               exact same drift. Expect ~0. Big drift here => the
                               metric makes artifacts.
  4. shuffle_test.png        — permute the block labels many times to build a null
                               distribution for the drift; is the real drift above
                               chance?  Prints a p-value.

Run:  python scripts/drift_over_time.py --config config.yaml
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

VIOLET, TEAL, AMBER, GREY, RED = "#6d28d9", "#0d9488", "#d97706", "#64748b", "#dc2626"

# windows (5 kHz). Carp: tighten the M-wave left edge to ~2.5 ms.
M_WIN = slice(13, 23)     # 2.6–4.6 ms
H_WIN = slice(30, 45)     # 6–9 ms
BASE_WIN = slice(100, 150)  # 20–30 ms quiet tail
BLOCK_DAYS = 5
HRDOWN_ONSET_UNIX = 1148563194


def measures(emg):
    e = emg - emg[:, BASE_WIN].mean(1, keepdims=True)
    return np.abs(e[:, M_WIN]).mean(1), np.abs(e[:, H_WIN]).mean(1)


def residualize(Y, m):
    m = (m - m.mean()) / (m.std() + 1e-9)
    X = np.column_stack([np.ones_like(m), m, m**2])
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
    return Y - X @ beta


def extract_latents(cfg, ecog):
    import torch
    from src.models.heads import build_autoencoder
    from src.utils.seed import get_device
    from src.data.preprocessing import zscore_per_trial
    dev = get_device()
    model = build_autoencoder(cfg)
    model.load_state_dict(torch.load("outputs/encoder_phase1.pt", map_location="cpu")["model"])
    model = model.to(dev).eval()
    n = ecog.shape[0]; Z = []
    with torch.no_grad():
        for i in range(0, n, 4096):
            x = zscore_per_trial(np.asarray(ecog[i:i+4096]).astype(np.float32))
            Z.append(model.encode(torch.tensor(x, device=dev)).cpu().numpy())
    return np.concatenate(Z)


def block_drift(Z, block, baseline_mask):
    """Centroid distance of each block from the baseline centroid."""
    ref = Z[baseline_mask].mean(0)
    blocks = sorted(set(block.tolist()))
    return blocks, np.array([np.linalg.norm(Z[block == b].mean(0) - ref) for b in blocks])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--zarr", default="data/processed/animal9.zarr")
    ap.add_argument("--out", default="outputs/drift_time")
    ap.add_argument("--shuffles", type=int, default=500)
    args = ap.parse_args()

    from src.utils.config import Config
    cfg = Config.load(args.config)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    import zarr
    r = zarr.open(args.zarr, mode="r")
    emg = np.asarray(r["emg"]); ecog = r["ecog"]
    if "day" not in r:
        sys.exit("no `day` array — run scripts/add_timestamps.py first")
    day = np.asarray(r["day"]); time = np.asarray(r["time"])
    M, H = measures(emg)
    m_ok = M > np.percentile(M, 10)
    HM = np.full(len(M), np.nan); HM[m_ok] = H[m_ok] / M[m_ok]
    onset_day = int((HRDOWN_ONSET_UNIX - time.min()) // 86400)

    report = []; say = lambda s: (print(s), report.append(s))
    say(f"=== DRIFT OVER TIME — Animal 9 ===\n{len(day)} trials, {day.max()+1} days, "
        f"conditioning onset day {onset_day}")

    Z = extract_latents(cfg, ecog)
    Zres = residualize(Z, M)   # M-wave removed

    # ---- FIG 1: daily waveform QC (heatmaps) ---------------------------------
    days = np.arange(day.max() + 1)
    emg_day = np.array([np.abs(emg[day == d] - emg[day == d][:, BASE_WIN].mean(1, keepdims=True)).mean(0)
                        if (day == d).any() else np.full(emg.shape[1], np.nan) for d in days])
    t_ms = np.arange(emg.shape[1]) / 5.0
    fig, ax = plt.subplots(figsize=(11, 5))
    im = ax.imshow(emg_day, aspect="auto", origin="lower",
                   extent=[t_ms[0], t_ms[-1], 0, days[-1]], cmap="magma", vmax=np.nanpercentile(emg_day, 98))
    ax.axvline(2.6, color="w", ls=":", lw=1); ax.axvline(4.6, color="w", ls=":", lw=1)
    ax.axvline(6, color="c", ls=":", lw=1); ax.axvline(9, color="c", ls=":", lw=1)
    ax.axhline(onset_day, color="w", ls="--", lw=1.5)
    ax.set_xlabel("ms after stimulus"); ax.set_ylabel("day")
    ax.set_title("Daily average rectified EMG (white=M window, cyan=H window, dashed=onset)")
    fig.colorbar(im, ax=ax, label="µV"); fig.tight_layout()
    fig.savefig(out / "daily_waveform_qc.png", dpi=140); plt.close(fig)
    say("[fig] daily_waveform_qc.png")

    # ---- FIG 2: drift in 5-day blocks (real) + H/M ---------------------------
    block = (day // BLOCK_DAYS).astype(np.int64)
    base_mask = day < onset_day
    blocks, d_raw = block_drift(Z, block, base_mask)
    _, d_res = block_drift(Zres, block, base_mask)
    block_mid = np.array(blocks) * BLOCK_DAYS + BLOCK_DAYS / 2
    hm_block = np.array([np.nanmedian(HM[block == b]) for b in blocks])

    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True, height_ratios=[2, 1])
    ax[0].plot(block_mid, d_raw, "-o", color=GREY, lw=2, label="raw")
    ax[0].plot(block_mid, d_res, "-o", color=VIOLET, lw=2.5, label="M-wave removed (honest)")
    ax[0].axvline(onset_day, color=AMBER, ls="--", lw=2, label="conditioning onset")
    ax[0].set_ylabel("cortical drift from baseline"); ax[0].legend()
    ax[0].set_title("Cortical drift over time (5-day blocks)")
    ax[1].plot(block_mid, hm_block, "-o", color=TEAL, lw=2)
    ax[1].axvline(onset_day, color=AMBER, ls="--", lw=2); ax[1].axhline(1.0, color=GREY, ls=":")
    ax[1].set_ylabel("H/M (median)"); ax[1].set_xlabel("day")
    ax[1].set_title("Behaviour: H/M learning curve (same blocks)")
    fig.tight_layout(); fig.savefig(out / "drift_over_time.png", dpi=140); plt.close(fig)
    say("[fig] drift_over_time.png")
    real_cond_drift = d_res[np.array(blocks) * BLOCK_DAYS >= onset_day].mean()
    say(f"  mean M-removed drift during conditioning = {real_cond_drift:.2f}")

    # ---- FIG 3: NULL CONTROL — baseline-split sham --------------------------
    # Use ONLY pre-conditioning trials. Treat the first 40% of baseline days as
    # pseudo-baseline, the rest as pseudo-conditioning. Same drift pipeline.
    base_days = np.unique(day[base_mask])
    split = base_days[int(0.4 * len(base_days))]
    bmask = base_mask & (day < split)                 # pseudo-baseline
    _, d_null_raw = block_drift(Z[base_mask], block[base_mask], (day[base_mask] < split))
    _, d_null_res = block_drift(Zres[base_mask], block[base_mask], (day[base_mask] < split))
    null_blocks = sorted(set(block[base_mask].tolist()))
    null_mid = np.array(null_blocks) * BLOCK_DAYS + BLOCK_DAYS / 2

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(block_mid, d_res, "-o", color=VIOLET, lw=2.5, label="REAL conditioning (M-removed)")
    ax.plot(null_mid, d_null_res, "-o", color=RED, lw=2.5, label="NULL: baseline split as sham")
    ax.axvline(split, color=GREY, ls="--", lw=1.5, label="pseudo-onset")
    ax.set_xlabel("day"); ax.set_ylabel("cortical drift from baseline")
    ax.set_title("Null control: sham conditioning on baseline should stay ~flat")
    ax.legend(); fig.tight_layout(); fig.savefig(out / "null_control.png", dpi=140); plt.close(fig)
    null_drift = d_null_res[-1]
    say(f"[fig] null_control.png")
    say(f"  NULL sham max drift = {null_drift:.2f}   vs real conditioning {real_cond_drift:.2f}  "
        f"(ratio {real_cond_drift/max(null_drift,1e-6):.1f}x)")

    # ---- FIG 4: SHUFFLE significance test -----------------------------------
    # Statistic = mean drift of conditioning blocks. Null = permute day labels.
    rng = np.random.default_rng(cfg.train.seed)
    cond_blocks_mask = np.array(blocks) * BLOCK_DAYS >= onset_day
    def stat_from_labels(perm_day):
        blk = (perm_day // BLOCK_DAYS).astype(np.int64)
        bl = sorted(set(blk.tolist()))
        ref = Zres[perm_day < onset_day].mean(0)
        dd = {b: np.linalg.norm(Zres[blk == b].mean(0) - ref) for b in bl}
        return np.mean([dd[b] for b in bl if b * BLOCK_DAYS >= onset_day])
    null_stats = np.array([stat_from_labels(rng.permutation(day)) for _ in range(args.shuffles)])
    real_stat = real_cond_drift
    pval = (np.sum(null_stats >= real_stat) + 1) / (args.shuffles + 1)
    z = (real_stat - null_stats.mean()) / (null_stats.std() + 1e-9)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(null_stats, bins=40, color=GREY, alpha=.7, label="shuffled null")
    ax.axvline(real_stat, color=VIOLET, lw=3, label=f"real drift (p={pval:.3f}, z={z:.1f})")
    ax.set_xlabel("mean conditioning-block drift"); ax.set_ylabel("count")
    ax.set_title(f"Shuffle test: is the drift above chance?  ({args.shuffles} permutations)")
    ax.legend(); fig.tight_layout(); fig.savefig(out / "shuffle_test.png", dpi=140); plt.close(fig)
    say(f"[fig] shuffle_test.png")
    say(f"  shuffle test: real={real_stat:.2f}  null={null_stats.mean():.2f}±{null_stats.std():.2f}  "
        f"p={pval:.4f}  z={z:.1f}")

    # ---- verdict ------------------------------------------------------------
    say("\n=== VERDICT ===")
    say(f"  drift above chance (shuffle)   : {'YES' if pval < 0.05 else 'NO'} (p={pval:.4f})")
    say(f"  null control stays ~flat       : {'YES' if null_drift < 0.5*real_cond_drift else 'NO — metric suspect'}"
        f" (sham {null_drift:.2f} vs real {real_cond_drift:.2f})")
    say(f"  survives M-wave removal        : {'YES' if d_res[-1] > 0.5*d_raw[-1] else 'NO'}")
    (out / "verdict.txt").write_text("\n".join(report) + "\n")
    print(f"\nwrote {out}/verdict.txt")


if __name__ == "__main__":
    main()
