"""Correct reflex measurement: background-subtracted M/H, validity criterion,
and M-matched comparison (instead of the H/M ratio).

Why this exists
---------------
The first pass measured M and H as MEAN RECTIFIED amplitude in a window. Rectified
background does not cancel, so a ~65 uV background pedestal was added to BOTH M and
H. Two numbers inflated by the same constant have a ratio pulled toward 1, which is
why every H/M we reported sat near 1.0 — and it can hide or manufacture an effect.

Three fixes here:
  1. BACKGROUND SUBTRACTION. Estimate the rectified background from the quiet tail
     and subtract it from both the M and H window measures.
     (TODO: the better background is frag0, the -50->0 ms pre-stimulus fragment in
      the DB. Not in the Zarr yet — that's the pre-stimulus-excitability item.)
  2. VALIDITY CRITERION. A trial only has a usable M-wave if the corrected M rises
     meaningfully above the noise. We report how many trials are excluded rather
     than hiding it behind a percentile cut.
  3. M-MATCHED COMPARISON instead of dividing. Compare H only between trials whose
     M-waves match, so stimulus is controlled by construction. This is the standard
     in the Wolpaw lab and avoids dividing by a near-noise-floor number.

Also sets the M and H windows PER ANIMAL from that animal's own grand-average
waveform, rather than reusing Animal 9's latencies.

Usage:
  python scripts/reflex_measures.py --zarrs data/processed/animal*.zarr
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

SR = 5000
TAIL = slice(100, 150)          # 20-30 ms, background estimate
VIOLET, TEAL, AMBER, GREY = "#6d28d9", "#0d9488", "#d97706", "#64748b"


def ms_to_i(ms): return int(round(ms / 1000 * SR))


def find_windows(emg):
    """Set M and H windows from this animal's own grand-average rectified EMG.

    M = largest peak in 1.5-5.5 ms, H = largest peak in 5.5-12 ms. Returns
    (m_slice, h_slice, m_peak_ms, h_peak_ms). Windows are +/-1 ms around each peak.
    """
    e = emg - emg[:, TAIL].mean(1, keepdims=True)
    avg = np.abs(e).mean(0)
    t = np.arange(len(avg)) / SR * 1000
    def peak(lo, hi):
        m = (t >= lo) & (t <= hi)
        idx = np.where(m)[0]
        return t[idx[np.argmax(avg[idx])]]
    # Start the M search AFTER the stimulus artifact (~0-2 ms), or the artifact wins.
    m_pk = peak(2.2, 5.5)
    # H must sit clearly after M, so it can't latch onto the M-wave's tail.
    h_pk = peak(max(m_pk + 1.5, 5.5), 12.0)
    m_sl = slice(max(ms_to_i(m_pk - 0.8), 0), ms_to_i(m_pk + 0.8))
    h_sl = slice(ms_to_i(h_pk - 1.2), ms_to_i(h_pk + 1.2))
    return m_sl, h_sl, m_pk, h_pk


def measures(emg, m_sl, h_sl):
    """Background-SUBTRACTED M and H (uV), plus the per-trial background level."""
    e = emg - emg[:, TAIL].mean(1, keepdims=True)
    bg = np.abs(e[:, TAIL]).mean(1)                     # rectified background pedestal
    M = np.maximum(np.abs(e[:, m_sl]).mean(1) - bg, 0.0)
    H = np.maximum(np.abs(e[:, h_sl]).mean(1) - bg, 0.0)
    return M, H, bg


def m_matched_H(M, H, grp_a, grp_b, nbins=8):
    """Median H in group A vs group B, compared WITHIN matched M bins.

    Returns (bin_centres, H_a, H_b, overall_a, overall_b, n_used). Only the M range
    where both groups have data is used, so stimulus is matched by construction.
    """
    lo = max(np.percentile(M[grp_a], 5), np.percentile(M[grp_b], 5))
    hi = min(np.percentile(M[grp_a], 95), np.percentile(M[grp_b], 95))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return None
    edges = np.linspace(lo, hi, nbins + 1)
    ctr, ha, hb, wt = [], [], [], []
    for i in range(nbins):
        sel = (M >= edges[i]) & (M < edges[i + 1])
        a, b = sel & grp_a, sel & grp_b
        if a.sum() < 30 or b.sum() < 30:
            continue
        ctr.append(0.5 * (edges[i] + edges[i + 1]))
        ha.append(np.median(H[a])); hb.append(np.median(H[b]))
        wt.append(min(a.sum(), b.sum()))
    if not ctr:
        return None
    wt = np.array(wt, float); wt /= wt.sum()
    return (np.array(ctr), np.array(ha), np.array(hb),
            float(np.sum(wt * np.array(ha))), float(np.sum(wt * np.array(hb))),
            int(sum(wt > 0)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zarrs", nargs="+", required=True)
    ap.add_argument("--out", default="outputs/reflex")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    import zarr

    rows = []
    fig, axes = plt.subplots(1, len(args.zarrs), figsize=(4.6 * len(args.zarrs), 4.4), squeeze=False)
    for k, zp in enumerate(args.zarrs):
        r = zarr.open(zp, mode="r")
        emg = np.asarray(r["emg"]); day = np.asarray(r["day"])
        phase = np.asarray(r["phase"]) if "phase" in r else np.zeros(len(day), np.int64)
        direction = r.attrs.get("direction", "?"); animal = r.attrs.get("animal", Path(zp).stem)

        m_sl, h_sl, m_pk, h_pk = find_windows(emg)
        M, H, bg = measures(emg, m_sl, h_sl)
        # validity: corrected M must clear 3x the trial's own background level
        valid = M > 3 * bg
        onset = int(day[phase > 0].min()) if (phase > 0).any() else int(day.max() // 2)

        base = (day < onset) & valid
        cond_days = day[(day >= onset)]
        late_cut = np.percentile(cond_days, 60) if len(cond_days) else onset
        late = (day >= late_cut) & valid

        res = m_matched_H(M, H, base, late)
        ax = axes[0][k]
        if res is None:
            ax.text(.5, .5, f"A{animal}\nno matched M overlap", ha="center", va="center")
            rows.append((animal, direction, m_pk, h_pk, valid.mean() * 100, np.nan, np.nan, np.nan))
        else:
            ctr, ha_, hb_, oa, ob, nb = res
            chg = (ob - oa) / oa * 100 if oa > 0 else np.nan
            ax.plot(ctr, ha_, "-o", color=GREY, lw=2, label="baseline")
            ax.plot(ctr, hb_, "-o", color=VIOLET, lw=2.5, label="late conditioning")
            ax.set_title(f"A{animal} ({direction})   H at matched M\n{chg:+.1f}%", fontsize=11)
            ax.set_xlabel("M-wave (uV, background-subtracted)"); ax.set_ylabel("H (uV)")
            ax.legend(fontsize=8)
            rows.append((animal, direction, m_pk, h_pk, valid.mean() * 100, oa, ob, chg))

    fig.tight_layout(); fig.savefig(out / "H_at_matched_M.png", dpi=140); plt.close(fig)

    lines = [f"{'animal':7s}{'dir':6s}{'Mpk':>6s}{'Hpk':>6s}{'valid%':>8s}{'H base':>9s}{'H late':>9s}{'change':>9s}"]
    for a, d, mp, hp, v, oa, ob, c in rows:
        lines.append(f"{a:7s}{d:6s}{mp:6.1f}{hp:6.1f}{v:8.1f}"
                     + (f"{oa:9.1f}{ob:9.1f}{c:+8.1f}%" if np.isfinite(c) else "      n/a      n/a      n/a"))
    lines.append("")
    lines.append("H compared WITHIN matched M-wave bins (stimulus controlled by construction).")
    lines.append("M/H are background-subtracted; valid% = trials whose M cleared 3x background.")
    txt = "\n".join(lines)
    print(txt); (out / "summary.txt").write_text(txt + "\n")
    print(f"\nfigure -> {out}/H_at_matched_M.png")


if __name__ == "__main__":
    main()
