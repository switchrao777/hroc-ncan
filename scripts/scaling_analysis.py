"""Does the cortical effect SCALE with how much the animal learned?

Dr Carp (2026-08-12): "Some of these will have stronger training than others, which
is sort of a good control. Things should scale. If you have an animal that shows big
change in the size of the reflex, you would expect either bigger change or sooner, or
quicker change... something about the time course or the amplitude of the cortical
signal predicts the time course or the amplitude of the H-reflex change. Especially
if there's a lot of variation among these animals — if some of them don't even hit
the 20%, that becomes an internal control. If they're not successful, then you don't
expect to see this cortical learning."

This is a strong design because it needs no extra animals to be informative and it
uses the animals that FAILED to condition as a built-in negative control. If cortical
coupling tracks learning magnitude across animals, that is evidence the coupling is
related to conditioning rather than to being recorded.

Two relationships tested, across animals:
    behavioural change (|% change in corrected H|)   vs   coupling magnitude
    behavioural change                               vs   change in coupling

Usage:
  python scripts/scaling_analysis.py --zarrs data/processed/animal*.zarr \
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
from scripts.coupling_analysis import ridge_cv_r2, MIN_TRIALS

VIOLET, TEAL, AMBER, GREY, RED, DOWN_C, UP_C = \
    "#6d28d9", "#0d9488", "#d97706", "#64748b", "#dc2626", "#2563eb", "#dc2626"


def zs(A):
    A = np.asarray(A, float)
    if A.ndim == 1:
        A = A[:, None]
    return (A - A.mean(0)) / (A.std(0) + 1e-8)


def per_animal(cfg, zp, ckpt, rng):
    import zarr
    r = zarr.open(zp, mode="r")
    emg = np.asarray(r["emg"]); day = np.asarray(r["day"]); phase = np.asarray(r["phase"])
    animal = r.attrs.get("animal", Path(zp).stem); direction = r.attrs.get("direction", "?")
    prestim = np.asarray(r["prestim_emg"])
    m_sl, h_sl, *_ = find_windows(emg)
    M, H, bg = measures(emg, m_sl, h_sl)
    valid = M > 3 * bg
    onset = int(day[phase > 0].min()) if (phase > 0).any() else int(day.max() // 2)
    base = (day >= onset - BASELINE_DAYS) & (day < onset)
    if base.sum() < 500:
        base = day < onset

    # behavioural change: corrected H at end of conditioning vs baseline, in %
    X = design(M, prestim)
    Hc = residualise(H, X)
    block = (day // BLOCK_DAYS).astype(np.int64)
    ids = np.array(sorted(set(block.tolist())))
    ref_lvl = np.median(H[base & valid]); ref_c = np.median(Hc[base & valid])
    pct = np.array([(np.median(Hc[(block == b) & valid]) - ref_c) / max(ref_lvl, 1e-6) * 100
                    if ((block == b) & valid).sum() > 30 else np.nan for b in ids])
    rel = ids * BLOCK_DAYS + BLOCK_DAYS / 2 - onset
    cond = rel > 0
    final = float(np.nanmedian(pct[cond][-2:])) if cond.any() else np.nan
    signed = final if direction == "up" else -final     # positive = learned as intended

    # coupling, within-block residualisation (the conservative estimate)
    Zraw = latents(cfg, r["ecog"], ckpt)
    cvals, crel = [], []
    for b in ids:
        sel = (block == b) & valid
        if sel.sum() < MIN_TRIALS:
            continue
        Xb = design(M[sel], prestim[sel])
        y = zs(residualise(H[sel], Xb))[:, 0]
        Zb = zs(residualise(Zraw[sel], Xb))
        cvals.append(ridge_cv_r2(Zb, y, rng=rng))
        crel.append(b * BLOCK_DAYS + BLOCK_DAYS / 2 - onset)
    cvals = np.array(cvals); crel = np.array(crel)
    cb = float(np.nanmean(cvals[crel < 0])) if (crel < 0).any() else np.nan
    cc = float(np.nanmean(cvals[crel > 0])) if (crel > 0).any() else np.nan
    # success requires the change to be in the TRAINED direction, not just large:
    # an up-conditioned animal whose H fell has failed, however big the change.
    return dict(animal=animal, direction=direction, learned=signed,
                abs_learned=abs(final), coupling=cc, coupling_change=cc - cb,
                success=signed >= 20)


def corr(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        return np.nan, np.nan
    x, y = x[ok], y[ok]
    r = float(np.corrcoef(x, y)[0, 1])
    n = ok.sum()
    t = r * np.sqrt((n - 2) / max(1 - r ** 2, 1e-12))
    return r, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zarrs", nargs="+", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--ckpt", default="outputs/encoder_pooled.pt")
    ap.add_argument("--out", default="outputs/scaling")
    ap.add_argument("--exclude", nargs="*", default=["12"])
    args = ap.parse_args()
    from src.utils.config import Config
    cfg = Config.load(args.config)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(cfg.train.seed)

    res = []
    for zp in args.zarrs:
        c = per_animal(cfg, zp, args.ckpt, rng)
        if c["animal"] in args.exclude:
            print(f"  EXCLUDED A{c['animal']}"); continue
        res.append(c)
        print(f"  A{c['animal']:>2s} ({c['direction']:4s})  learned={c['learned']:+7.1f}%  "
              f"{'SUCCESS' if c['success'] else 'failed ':8s}  coupling={c['coupling']:.4f}  "
              f"Δcoupling={c['coupling_change']:+.4f}")

    learn = np.array([c["abs_learned"] for c in res])
    signed = np.array([c["learned"] for c in res])
    coup = np.array([c["coupling"] for c in res])
    dcoup = np.array([c["coupling_change"] for c in res])

    r1, t1 = corr(signed, coup)
    r2, t2 = corr(signed, dcoup)

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    for a, (yv, ttl, yl, rr, tt) in zip(
            ax, [(coup, "Coupling magnitude vs learning", "cortex→reflex R² (conditioning)", r1, t1),
                 (dcoup, "Change in coupling vs learning", "Δ coupling (cond − baseline)", r2, t2)]):
        for c, y in zip(res, yv):
            a.scatter(c["learned"], y, s=120, color=UP_C if c["direction"] == "up" else DOWN_C,
                      edgecolors="white", zorder=3)
            a.annotate(f"A{c['animal']}", (c["learned"], y), textcoords="offset points",
                       xytext=(8, 5), fontsize=10)
        ok = np.isfinite(signed) & np.isfinite(yv)
        if ok.sum() > 2:
            m, b = np.polyfit(signed[ok], yv[ok], 1)
            xs = np.linspace(signed[ok].min(), signed[ok].max(), 10)
            a.plot(xs, m * xs + b, color=GREY, ls="--", lw=1.6)
        a.axvline(20, color=TEAL, ls=":", lw=1.2)
        a.axhline(0, color="#e2e8f0", ls=":")
        a.set_xlabel("behavioural change in the trained direction (%)")
        a.set_ylabel(yl); a.set_title(f"{ttl}\nr = {rr:+.2f}, t = {tt:+.2f}, n = {len(res)}")
    fig.tight_layout(); fig.savefig(out / "scaling.png", dpi=145); plt.close(fig)

    L = ["=== DOES THE CORTICAL EFFECT SCALE WITH LEARNING? ===",
         "(Carp's internal control: animals that failed to condition should not show it)", "",
         f"{'animal':8s}{'dir':6s}{'learned %':>11s}{'success':>9s}{'coupling':>10s}{'Δcoupling':>11s}"]
    for c in res:
        L.append(f"{'A'+c['animal']:8s}{c['direction']:6s}{c['learned']:+11.1f}"
                 f"{('YES' if c['success'] else 'no'):>9s}{c['coupling']:10.4f}{c['coupling_change']:+11.4f}")
    L += ["",
          f"learning vs coupling magnitude : r = {r1:+.3f}  (t = {t1:+.2f}, n = {len(res)})",
          f"learning vs change in coupling : r = {r2:+.3f}  (t = {t2:+.2f}, n = {len(res)})",
          "",
          "A positive correlation would mean animals that learned more show more cortical",
          "coupling — evidence the coupling is tied to conditioning rather than to being",
          "recorded. With this n the test is underpowered; it is the analysis that the",
          "remaining animals (7, 8, 13, 14, 15) will actually power."]
    txt = "\n".join(L)
    print("\n" + txt); (out / "summary.txt").write_text(txt + "\n")
    print(f"\nfigure -> {out}/scaling.png")


if __name__ == "__main__":
    main()
