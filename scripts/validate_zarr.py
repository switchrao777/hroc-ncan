"""Validate a converted Zarr store (Checkpoint 4).

Checks shapes, dtypes, NaNs, per-phase counts, label distribution, and whether
the averaged EMG shows the M/H bumps. Run after convert.py, before training.

    python scripts/validate_zarr.py --zarr /path/animal9.zarr
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zarr", required=True)
    ap.add_argument("--out", default="outputs/validate")
    args = ap.parse_args()

    import zarr
    r = zarr.open(args.zarr, mode="r")
    ecog, emg = np.asarray(r["ecog"]), np.asarray(r["emg"])
    hreflex, phase = np.asarray(r["hreflex"]), np.asarray(r["phase"])

    print("=== shapes / dtypes ===")
    for name, a in [("ecog", ecog), ("emg", emg), ("hreflex", hreflex), ("phase", phase)]:
        print(f"  {name:8s} {a.shape} {a.dtype}")

    ok = True
    print("\n=== sanity ===")
    for name, a in [("ecog", ecog), ("emg", emg), ("hreflex", hreflex)]:
        nan = np.isnan(a).sum()
        print(f"  {name} NaNs: {nan}")
        ok &= nan == 0
    if np.ptp(hreflex) < 1e-6:
        print("  WARNING: hreflex is ~constant — label is broken"); ok = False
    print(f"  hreflex range [{hreflex.min():.3f}, {hreflex.max():.3f}] mean {hreflex.mean():.3f}")

    print("\n=== trials per phase ===")
    present = sorted(set(phase.tolist()))
    for p in range(6):
        c = int((phase == p).sum())
        tag = "" if p in present else "  (not run for this animal)"
        print(f"  phase {p}: {c}{tag}")
    # Require >=2 non-empty phases for a drift comparison; NOT all 6 (many animals
    # ran a partial protocol, e.g. Animal 9 = Baseline/HRdown/Post only).
    if len(present) < 2:
        print("  WARNING: <2 phases present — no cross-phase drift possible"); ok = False

    # averaged EMG bump check
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    t_ms = np.linspace(0, emg.shape[1] / 5000 * 1000, emg.shape[1])
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t_ms, emg.mean(0)); ax.axvspan(2, 4, color="#fde68a", alpha=.4)
    ax.axvspan(6, 9, color="#bbf7d0", alpha=.5); ax.set_xlabel("ms")
    ax.set_title("Averaged EMG — expect M (2-4ms) + H (6-9ms) bumps")
    fig.tight_layout(); fig.savefig(out / "avg_emg.png", dpi=150)

    print(f"\n{'PASS' if ok else 'FAIL'} — see {out/'avg_emg.png'} for the bump check")


if __name__ == "__main__":
    main()
