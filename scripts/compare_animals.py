"""Up-vs-down cross-animal contrast — the test that decides the cortical claim.

Single-animal drift is confounded with recording nonstationarity (see
outputs/drift_time/ and NEXT_TWO_WEEKS.md). The way out: recording drift is
idiosyncratic per electrode and direction-independent, whereas a real conditioning
effect must differ by DIRECTION. So we align every animal to its own conditioning
onset and overlay, coloured by up vs down:

  * behaviour_by_direction.png — H/M vs day. Sanity check that MUST hold: down
    animals' H/M falls, up animals' H/M rises. If this fails, the pipeline is wrong.
  * cortex_by_direction.png    — cortical drift vs day (M-removed). The real test:
    do up and down animals separate? If they overlap, the cortical "drift" is
    recording nonstationarity, not conditioning.

Uses ONE shared encoder (outputs/encoder_phase1.pt) as a fixed feature extractor so
all animals live in a common latent space. Run once >=2 animals of differing
direction are converted (each animalN.zarr carries its `direction` attr).

Usage:
  python scripts/compare_animals.py --zarrs data/processed/animal9.zarr \
      data/processed/animal10.zarr data/processed/animal11.zarr
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

from scripts.drift_over_time import measures, residualize, extract_latents, BLOCK_DAYS

DOWN_C, UP_C = "#2563eb", "#dc2626"   # blue = down, red = up


def per_animal_curves(cfg, zpath):
    import zarr
    r = zarr.open(zpath, mode="r")
    emg = np.asarray(r["emg"]); ecog = r["ecog"]
    day = np.asarray(r["day"]); time = np.asarray(r["time"])
    phase = np.asarray(r["phase"]) if "phase" in r else np.zeros(len(day), np.int64)
    direction = r.attrs.get("direction", "unknown")
    animal = r.attrs.get("animal", Path(zpath).stem)
    onset_day = int(day[phase > 0].min()) if (phase > 0).any() else int(day.max() // 2)

    M, H = measures(emg)
    m_ok = M > np.percentile(M, 10)
    HM = np.full(len(M), np.nan); HM[m_ok] = H[m_ok] / M[m_ok]

    Z = residualize(extract_latents(cfg, ecog), M)     # M-removed latents
    block = (day // BLOCK_DAYS).astype(np.int64)
    base = Z[day < onset_day].mean(0)
    blocks = sorted(set(block.tolist()))
    rel_day = np.array(blocks) * BLOCK_DAYS + BLOCK_DAYS / 2 - onset_day  # day rel. to onset
    drift = np.array([np.linalg.norm(Z[block == b].mean(0) - base) for b in blocks])
    hm = np.array([np.nanmedian(HM[block == b]) for b in blocks])
    return dict(animal=animal, direction=direction, rel_day=rel_day, drift=drift, hm=hm)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zarrs", nargs="+", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", default="outputs/compare")
    args = ap.parse_args()

    from src.utils.config import Config
    cfg = Config.load(args.config)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    curves = [per_animal_curves(cfg, z) for z in args.zarrs]
    col = lambda d: UP_C if d == "up" else (DOWN_C if d == "down" else "#64748b")

    # behaviour: H/M vs day-relative-to-onset
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for c in curves:
        ax.plot(c["rel_day"], c["hm"], "-o", color=col(c["direction"]), alpha=.8,
                label=f"A{c['animal']} ({c['direction']})")
    ax.axvline(0, color="#94a3b8", ls="--", lw=1.5); ax.axhline(1.0, color="#cbd5e1", ls=":")
    ax.set_xlabel("day relative to conditioning onset"); ax.set_ylabel("H/M (median)")
    ax.set_title("Behaviour by direction — down should FALL, up should RISE")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(out / "behaviour_by_direction.png", dpi=140); plt.close(fig)

    # cortex: drift vs day-relative-to-onset
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for c in curves:
        ax.plot(c["rel_day"], c["drift"], "-o", color=col(c["direction"]), alpha=.8,
                label=f"A{c['animal']} ({c['direction']})")
    ax.axvline(0, color="#94a3b8", ls="--", lw=1.5)
    ax.set_xlabel("day relative to conditioning onset")
    ax.set_ylabel("cortical drift from baseline (M-removed)")
    ax.set_title("Cortex by direction — do up and down SEPARATE? (if not, it's recording drift)")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(out / "cortex_by_direction.png", dpi=140); plt.close(fig)

    # crude summary
    def cond_mean(key):
        ups = [np.nanmean(c[key][c["rel_day"] > 0]) for c in curves if c["direction"] == "up"]
        dns = [np.nanmean(c[key][c["rel_day"] > 0]) for c in curves if c["direction"] == "down"]
        return (np.mean(ups) if ups else np.nan), (np.mean(dns) if dns else np.nan)
    hu, hd = cond_mean("hm"); du, dd = cond_mean("drift")
    lines = [
        f"animals: " + ", ".join(f"A{c['animal']}({c['direction']})" for c in curves),
        f"behaviour  H/M during conditioning:  up={hu:.3f}  down={hd:.3f}"
        f"  ({'OK: opposite' if hu > hd else 'CHECK: not opposite'})",
        f"cortex     drift during conditioning: up={du:.2f}  down={dd:.2f}",
        "NOTE: needs >=1 up AND >=1 down animal to be meaningful.",
    ]
    (out / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines)); print(f"\nfigures -> {out}/")


if __name__ == "__main__":
    main()
