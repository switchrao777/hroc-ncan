"""Does each embedding predict single-trial reflex size? A like-for-like comparison.

For the embedding size chosen by reconstruction (outputs/latent_sweep/choice.json),
encode every usable trial and run the same within-window test as the main result:
inside each 5-day window, remove the M-wave and pre-stimulus background from both
sides, fit ridge regression with 5-fold cross-validation, and compare against the
same data with the reflex values shuffled. Every feature set is scored on the same
trials with the same folds, so differences come from the features alone.

Reference feature set: the six pre-stimulus band powers used earlier (last 512 ms,
delta to >100 Hz; the >100 Hz band includes the 120 Hz mains line).

Outputs (outputs/embedding_coupling/): summary.txt, summary.csv, comparison.png

Usage:
  python scripts/embedding_coupling.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams.update({"font.size": 13, "axes.labelsize": 15, "axes.titlesize": 16,
    "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 12})

from scripts.reflex_measures import find_windows, measures
from scripts.final_analysis import design, residualise, BLOCK_DAYS
from scripts.coupling_analysis import ridge_cv_r2, MIN_TRIALS
from scripts.latent_sweep import (ANIMALS, LABEL, OUT as SWEEP, encode_rows,
                                  load_model, load_norm, zpath)

OUT = Path("outputs/embedding_coupling")


def within_block(F, M, pre, H, day, seed=42):
    """Per-window cross-validated R² of F -> H, and the same with H shuffled."""
    rng = np.random.default_rng(seed)
    block = (day // BLOCK_DAYS).astype(np.int64)
    r2, nl = [], []
    for b in sorted(set(block.tolist())):
        sel = block == b
        if sel.sum() < MIN_TRIALS:
            continue
        Xb = design(M[sel], pre[sel])
        y, Z = residualise(H[sel], Xb), residualise(F[sel], Xb)
        Z = (Z - Z.mean(0)) / (Z.std(0) + 1e-8)
        y = (y - y.mean()) / (y.std() + 1e-8)
        r2.append(ridge_cv_r2(Z, y, rng=rng))
        nl.append(ridge_cv_r2(Z, rng.permutation(y), rng=rng))
    return np.array(r2), np.array(nl)


SUCCESS, FAILED = ("9", "11", "3"), ("10", "4")     # 20% criterion in the trained direction


def partition(F, M, pre, H, day, seed=42):
    """Variance split as on the talk's slide: cross-validated R² of stimulus (M-wave),
    background EMG, cortex, stimulus + background, and all three; mean over windows.
    'unique' is what cortex adds once stimulus and background are in the model."""
    rng = np.random.default_rng(seed)
    block = (day // BLOCK_DAYS).astype(np.int64)
    zs = lambda x: ((x - x.mean(0)) / (x.std(0) + 1e-8)).reshape(len(x), -1)
    acc = {k: [] for k in ("stim", "bg", "cortex", "stim_bg", "all")}
    for b in sorted(set(block.tolist())):
        sel = block == b
        if sel.sum() < MIN_TRIALS:
            continue
        y = zs(H[sel])[:, 0]
        Mm, Bb, Cc = zs(M[sel]), zs(pre[sel]), zs(F[sel])
        MB = np.column_stack([Mm, Bb])
        for key, X in (("stim", Mm), ("bg", Bb), ("cortex", Cc), ("stim_bg", MB),
                       ("all", np.column_stack([MB, Cc]))):
            acc[key].append(ridge_cv_r2(X, y, rng=rng))
    out = {k: float(np.nanmean(v)) for k, v in acc.items()}
    out["unique"] = out["all"] - out["stim_bg"]
    return out


def main():
    import zarr
    from scipy import stats
    from src.utils.seed import get_device
    dev = get_device()
    OUT.mkdir(parents=True, exist_ok=True)
    choice = json.loads((SWEEP / "choice.json").read_text())
    sets = [s for s in LABEL if s in choice] + ["bands"]
    models = {s: load_model(s, choice[s], dev) for s in sets if s != "bands"}
    norms = {s: load_norm(s) for s in models}

    res, parts = {s: [] for s in sets}, {s: {} for s in sets}
    for a in ANIMALS:
        r = zarr.open(zpath(a), mode="r")
        emg = np.asarray(r["emg"]); day = np.asarray(r["day"])
        m_sl, h_sl, *_ = find_windows(emg)
        M, H, bg = measures(emg, m_sl, h_sl)
        idx = np.where((M > 3 * bg) & np.asarray(r["prestim_ok"]))[0]
        pre = np.asarray(r["prestim_emg"])[idx]
        for s in sets:
            F = (np.asarray(r["prestim_bands"])[idx] if s == "bands"
                 else encode_rows(s, r, idx, norms[s][a], models[s], dev))
            r2, nl = within_block(F, M[idx], pre, H[idx], day[idx])
            parts[s][a] = partition(F, M[idx], pre, H[idx], day[idx])
            res[s].append((a, np.nanmean(r2), np.nanmean(nl), int(np.sum(r2 > nl)), len(r2)))
            print(f"  A{a:>2s} {s:9s} dims={F.shape[1]:2d}  R2={res[s][-1][1]:.4f}  "
                  f"null={res[s][-1][2]:+.4f}  above null {res[s][-1][3]}/{res[s][-1][4]}",
                  flush=True)

    name = dict(LABEL, bands="1 s before, 6 band powers")
    L = ["=== EMBEDDING -> REFLEX: WITHIN-WINDOW PREDICTION, SAME TRIALS AND FOLDS ===",
         "sizes chosen by held-out reconstruction: " + json.dumps(choice), "",
         f"{'features':28s}{'dims':>5s}{'mean R2':>9s}{'null':>9s}{'windows':>10s}{'t(4)':>7s}{'p':>8s}"]
    rows = []
    for s in sets:
        v = np.array([x[1:] for x in res[s]], float)
        d = v[:, 0] - v[:, 1]
        t, p = stats.ttest_1samp(d, 0.0)
        dims = 6 if s == "bands" else choice[s]
        L.append(f"{name[s]:28s}{dims:5d}{v[:, 0].mean():9.4f}{v[:, 1].mean():+9.4f}"
                 f"{int(v[:, 2].sum()):>5d}/{int(v[:, 3].sum()):<4d}{t:7.2f}{p:8.3f}")
        rows.append((s, dims, v))
    L += ["", "per animal (R2):  " + "  ".join(f"A{a}" for a in ANIMALS)]
    for s, dims, v in rows:
        L.append(f"  {name[s]:26s}" + "  ".join(f"{x:.4f}" for x in v[:, 0]))
    L += ["", "t(4): one-sample t on each animal's (real - shuffled), i.e. the animal is the unit."]
    L += ["", "=== VARIANCE SPLIT (method of the talk's slide) AND COUPLING, BY GROUP ===",
          "learned = 9, 11, 3 (met the 20% criterion); did not = 10, 4", "",
          f"{'features':28s}{'group':>9s}{'stim':>7s}{'bg':>7s}{'cortex':>8s}{'unique':>8s}"
          f"{'unexpl':>8s}{'coupling':>10s}"]
    with (OUT / "partition.csv").open("w") as f:
        f.write("features,animal,stim,bg,cortex,stim_bg,all,unique\n")
        for s in sets:
            for a in ANIMALS:
                q = parts[s][a]
                f.write(f"{s},{a}," + ",".join(f"{q[k]:.5f}" for k in
                        ("stim", "bg", "cortex", "stim_bg", "all", "unique")) + "\n")
            for gname, grp in (("all 5", ANIMALS), ("learned", SUCCESS), ("did not", FAILED)):
                m = {k: np.mean([parts[s][a][k] for a in grp]) for k in parts[s][grp[0]]}
                cp = np.mean([x[1] for x in res[s] if x[0] in grp])
                L.append(f"{name[s]:28s}{gname:>9s}{100*m['stim']:6.1f}%{100*m['bg']:6.1f}%"
                         f"{100*m['cortex']:7.1f}%{100*m['unique']:7.1f}%{100*(1-m['all']):7.1f}%"
                         f"{cp:10.4f}")
            L.append("")
    txt = "\n".join(L); print("\n" + txt); (OUT / "summary.txt").write_text(txt + "\n")
    with (OUT / "summary.csv").open("w") as f:
        f.write("features,animal,r2,null,windows_above,windows\n")
        for s in sets:
            for a, r2, nl, ab, n in res[s]:
                f.write(f"{s},{a},{r2:.5f},{nl:.5f},{ab},{n}\n")

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    for i, (s, dims, v) in enumerate(rows):
        ax.bar(i, v[:, 0].mean(), width=0.6, color="#15718F" if s != "bands" else "#9AA8B4")
        ax.scatter(np.full(len(v), i) + np.linspace(-0.18, 0.18, len(v)), v[:, 0],
                   color="#14212E", s=22, zorder=3)
        ax.plot([i - 0.3, i + 0.3], [v[:, 1].mean()] * 2, color="#A44430", lw=2.2)
    ax.axhline(0, color="#5A6B7B", lw=1)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels([f"{name[s]}\n({d} numbers)" for s, d, _ in rows], fontsize=11.5)
    ax.set_ylabel("prediction score (R²)")
    ax.set_title("How well each description of the brain signal predicts the reflex")
    ax.text(0.99, 0.97, "bar = mean of 5 animals · dots = animals · red line = shuffled",
            transform=ax.transAxes, ha="right", va="top", fontsize=11, color="#5A6B7B")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout(); fig.savefig(OUT / "comparison.png", dpi=150); plt.close(fig)
    print(f"\nfigures -> {OUT}/")


if __name__ == "__main__":
    main()
