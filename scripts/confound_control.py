"""Confound control — is the cortical effect real, or just stimulus drift?

Motivation (from Carp-style review):
  * Raw H-reflex amplitude is NOT a valid measure. H depends steeply on stimulus
    intensity, so a bigger H during conditioning can just mean a bigger stimulus.
    Wolpaw's lab always controls for this — H/M ratio, or H at a matched M-wave.
  * The same stimulus can inflate BOTH the cortical drift and the Phase-2 R²,
    because the ECoG window contains a stimulus-evoked response whose size tracks
    the stimulus. So "cortex mirrors reflex" could be "big stimulus -> big
    everything."

This script does three things:
  1. PHASE CORRECTION. The type-15 log's "Stopped conditioning" marker is
     unreliable (H/M keeps dropping long after it). We derive phases from time +
     the documented conditioning ONSET only: Baseline vs Down-conditioning
     (split early/late to show progression).
  2. PHYSIOLOGICAL MEASURES. Per-trial M-wave, H-reflex, and H/M. Figures:
     learning curve (H/M over time), M-wave over time (the confound), and H/M by
     corrected phase.
  3. THE TEST THAT SETTLES IT. Regress the M-wave out of BOTH the H-reflex and the
     ECoG latent, then recompute the Phase-2 R² and the centroid drift. If they
     survive M-regression, the cortical effect is not just stimulus. If they
     collapse, it was stimulus — learned cheaply, before publishing.

Run:  python scripts/confound_control.py --config config.yaml
Needs: data/processed/animal9.zarr, outputs/encoder_phase1.pt, and (for trial
times) the loaded MariaDB, or falls back to trial order if the DB is down.
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
# sample windows (5 kHz, 150-sample / 30 ms trace)
M_WIN = slice(10, 20)     # 2–4 ms  (M-wave; log: "MR interval 2-4")
H_WIN = slice(30, 45)     # 6–9 ms  (H-reflex; log: "HR interval 6-9")
BASE_WIN = slice(100, 150)  # 20–30 ms quiet tail for baseline correction

VIOLET, TEAL, AMBER, GREY = "#6d28d9", "#0d9488", "#d97706", "#64748b"


# ----------------------------------------------------------------- measures
def per_trial_measures(emg: np.ndarray):
    """Return baseline-corrected, rectified M-wave and H-reflex per trial (µV)."""
    base = emg[:, BASE_WIN].mean(1, keepdims=True)
    e = emg - base
    M = np.abs(e[:, M_WIN]).mean(1)
    H = np.abs(e[:, H_WIN]).mean(1)
    return M, H


def load_times(n_expected: int):
    """Per-trial unix time aligned to Zarr order (fragment=1, ORDER BY trial)."""
    try:
        import pymysql
        con = pymysql.connect(unix_socket="/tmp/hroc_mysql.sock", user="root",
                              database="emg_eeg_9")
        cur = con.cursor()
        cur.execute("SELECT time FROM channel_data WHERE fragment=1 ORDER BY trial")
        t = np.array([r[0] for r in cur.fetchall()], dtype=np.int64)
        con.close()
        if len(t) == n_expected:
            return t
        print(f"[warn] DB times ({len(t)}) != trials ({n_expected}); using index order")
    except Exception as ex:
        print(f"[warn] no DB times ({ex}); using index order as a proxy for time")
    return np.arange(n_expected, dtype=np.int64)


# ----------------------------------------------------------------- phases
# Documented conditioning ONSET (type-15 "Start HRdown"). We deliberately do NOT
# use the unreliable "Stopped conditioning" marker.
HRDOWN_ONSET_UNIX = 1148563194
PHASE_NAMES = {0: "Baseline", 1: "Down-cond (early)", 2: "Down-cond (late)"}


def corrected_phases(t: np.ndarray):
    """0=Baseline (pre-onset), 1=early down-cond, 2=late down-cond (split at the
    midpoint of the conditioning span). Falls back to terciles if times are a
    plain index proxy."""
    if t.max() > 1e6:  # real unix times
        onset = HRDOWN_ONSET_UNIX
        cond = t >= onset
        ph = np.zeros(len(t), dtype=np.int64)
        if cond.any():
            mid = (t[cond].min() + t.max()) // 2
            ph[cond & (t < mid)] = 1
            ph[cond & (t >= mid)] = 2
        return ph
    # fallback: terciles by order
    q = np.quantile(t, [1/3, 2/3])
    return np.digitize(t, q).astype(np.int64)


# ----------------------------------------------------------------- regression utils
def _design(x):
    x = (x - x.mean()) / (x.std() + 1e-9)
    return np.column_stack([np.ones_like(x), x, x**2])  # intercept + M + M^2


def residualize(Y, m):
    """Remove the M-wave's linear+quadratic contribution from each column of Y."""
    X = _design(m)
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
    return Y - X @ beta


def r2(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    return 1.0 - ss_res / (ss_tot + 1e-12)


def ridge_r2(Ztr, ytr, Zva, yva, lam=10.0):
    """Fit ridge Z->y on train, return R^2 on val."""
    Zt = np.column_stack([np.ones(len(Ztr)), Ztr])
    Zv = np.column_stack([np.ones(len(Zva)), Zva])
    A = Zt.T @ Zt + lam * np.eye(Zt.shape[1]); A[0, 0] -= lam
    beta = np.linalg.solve(A, Zt.T @ ytr)
    return r2(yva, Zv @ beta)


# ----------------------------------------------------------------- latents
def extract_latents(cfg, zarr_ecog):
    import torch
    from src.models.heads import build_autoencoder
    from src.utils.seed import get_device
    dev = get_device()
    model = build_autoencoder(cfg)
    ck = torch.load("outputs/encoder_phase1.pt", map_location="cpu")
    model.load_state_dict(ck["model"]); model = model.to(dev).eval()
    from src.data.preprocessing import zscore_per_trial
    n = zarr_ecog.shape[0]
    Z = []
    with torch.no_grad():
        for i in range(0, n, 4096):
            # IMPORTANT: apply the SAME per-trial z-score the training dataloader
            # used, or the encoder sees out-of-distribution inputs.
            chunk = zscore_per_trial(np.asarray(zarr_ecog[i:i+4096]).astype(np.float32))
            x = torch.tensor(chunk, dtype=torch.float32, device=dev)
            Z.append(model.encode(x).cpu().numpy())
    return np.concatenate(Z)


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--zarr", default="data/processed/animal9.zarr")
    ap.add_argument("--out", default="outputs/confound")
    args = ap.parse_args()

    from src.utils.config import Config
    cfg = Config.load(args.config)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    import zarr
    r = zarr.open(args.zarr, mode="r")
    emg = np.asarray(r["emg"]); ecog = r["ecog"]
    N = emg.shape[0]
    t = load_times(N)
    M, H = per_trial_measures(emg)
    ph = corrected_phases(t)

    # robust H/M: ignore trials with tiny M (unstable ratio)
    m_ok = M > np.percentile(M, 10)
    HM = np.full(N, np.nan); HM[m_ok] = H[m_ok] / M[m_ok]

    report = []
    def say(s): print(s); report.append(s)

    say("=== CONFOUND CONTROL — Animal 9 ===")
    say(f"trials: {N}")
    for p in sorted(set(ph.tolist())):
        m = ph == p
        say(f"  {PHASE_NAMES.get(p,p):18s} n={m.sum():6d}  "
            f"M={M[m].mean():6.1f}  H={H[m].mean():6.1f}  H/M={np.nanmean(HM[m]):.3f}")

    # ---- FIG 1: learning curve (H/M over time) + M over time -----------------
    if t.max() > 1e6:
        day = (t - t.min()) // 86400
        days = np.arange(day.max() + 1)
        hm_d = np.array([np.nanmedian(HM[day == d]) if (day == d).any() else np.nan for d in days])
        m_d = np.array([np.nanmedian(M[day == d]) if (day == d).any() else np.nan for d in days])
        onset_day = (HRDOWN_ONSET_UNIX - t.min()) // 86400
        fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
        ax[0].plot(days, hm_d, "-o", color=VIOLET, ms=4)
        ax[0].axvline(onset_day, color=AMBER, ls="--", lw=2, label="conditioning onset")
        ax[0].axhline(1.0, color=GREY, ls=":", lw=1)
        ax[0].set_title("Down-conditioning learning curve (H/M ratio)")
        ax[0].set_xlabel("day"); ax[0].set_ylabel("H/M (median)"); ax[0].legend()
        ax[1].plot(days, m_d, "-o", color=TEAL, ms=4)
        ax[1].axvline(onset_day, color=AMBER, ls="--", lw=2)
        ax[1].set_title("M-wave over time  (the confound: stimulus drifts up)")
        ax[1].set_xlabel("day"); ax[1].set_ylabel("M-wave µV (median)")
        fig.tight_layout(); fig.savefig(out / "learning_curve.png", dpi=140); plt.close(fig)
        say(f"\n[fig] learning_curve.png  (H/M {hm_d[~np.isnan(hm_d)][0]:.2f} -> "
            f"{hm_d[~np.isnan(hm_d)][-1]:.2f}; M {m_d[~np.isnan(m_d)][0]:.0f} -> {m_d[~np.isnan(m_d)][-1]:.0f})")

    # ---- FIG 2: valid vs confounded — H/M vs raw H by phase ------------------
    ps = sorted(set(ph.tolist()))
    labels = [PHASE_NAMES.get(p, str(p)) for p in ps]
    def mean_ci(v):
        v = v[~np.isnan(v)]
        return v.mean(), 1.96 * v.std() / np.sqrt(len(v))
    hm_m = [mean_ci(HM[ph == p]) for p in ps]
    h_m = [mean_ci(H[ph == p]) for p in ps]
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6))
    ax[0].bar(labels, [x[0] for x in hm_m], yerr=[x[1] for x in hm_m], color=VIOLET, alpha=.85, capsize=4)
    ax[0].set_title("VALID measure: H/M by phase"); ax[0].set_ylabel("H/M"); ax[0].axhline(hm_m[0][0], color=GREY, ls=":")
    ax[1].bar(labels, [x[0] for x in h_m], yerr=[x[1] for x in h_m], color=AMBER, alpha=.7, capsize=4)
    ax[1].set_title("CONFOUNDED: raw H by phase (do not trust)"); ax[1].set_ylabel("H µV")
    for a in ax: a.tick_params(axis="x", rotation=12)
    fig.tight_layout(); fig.savefig(out / "hm_vs_rawH_by_phase.png", dpi=140); plt.close(fig)
    say("[fig] hm_vs_rawH_by_phase.png")

    behavioral_ok = hm_m[-1][0] < hm_m[0][0]  # late conditioning H/M below baseline
    say(f"\nBEHAVIOR: H/M baseline={hm_m[0][0]:.3f} -> late-cond={hm_m[-1][0]:.3f}  "
        f"=> down-conditioning {'WORKED (H/M fell)' if behavioral_ok else 'did NOT show'}")

    # ---- THE TEST: M-regressed R^2 and drift --------------------------------
    say("\n=== does the CORTICAL effect survive removing the M-wave? ===")
    Z = extract_latents(cfg, ecog)
    rng = np.random.default_rng(cfg.train.seed)
    idx = rng.permutation(N); cut = int(0.85 * N)
    tr, va = idx[:cut], idx[cut:]

    # R^2: stimulus alone, cortex raw, cortex with M regressed out of both
    r2_M = ridge_r2(M[tr, None], H[tr], M[va, None], H[va])
    r2_Z = ridge_r2(Z[tr], H[tr], Z[va], H[va])
    H_res = residualize(H[:, None], M)[:, 0]
    Z_res = residualize(Z, M)
    r2_partial = ridge_r2(Z_res[tr], H_res[tr], Z_res[va], H_res[va])
    say(f"  R2  stimulus (M -> H)            : {r2_M:.3f}")
    say(f"  R2  cortex raw (Z -> H)          : {r2_Z:.3f}")
    say(f"  R2  cortex | M removed (partial) : {r2_partial:.3f}   <-- the honest number")

    # drift: raw latents vs M-regressed latents, on corrected phases
    def drift(Zin):
        base = Zin[ph == ps[0]].mean(0)
        return {p: float(np.linalg.norm(Zin[ph == p].mean(0) - base)) for p in ps}
    d_raw, d_reg = drift(Z), drift(Z_res)
    say("  centroid drift from Baseline:")
    for p in ps:
        say(f"    {PHASE_NAMES.get(p,p):18s} raw={d_raw[p]:7.2f}   M-removed={d_reg[p]:7.2f}")

    fig, ax = plt.subplots(figsize=(8.5, 5))
    xs = range(len(ps))
    ax.plot(xs, [d_raw[p] for p in ps], "-o", color=GREY, lw=2, label="raw (confounded)")
    ax.plot(xs, [d_reg[p] for p in ps], "-o", color=VIOLET, lw=2.5, label="M-wave removed (honest)")
    ax.set_xticks(list(xs)); ax.set_xticklabels(labels, rotation=12)
    ax.set_ylabel("latent centroid distance from Baseline")
    ax.set_title("Cortical drift: does it survive removing the stimulus?")
    ax.legend(); fig.tight_layout(); fig.savefig(out / "drift_confound_control.png", dpi=140); plt.close(fig)
    say("[fig] drift_confound_control.png")

    # verdict
    drift_survives = d_reg[ps[-1]] > 0.5 * d_raw[ps[-1]] and d_reg[ps[-1]] > d_reg[ps[0]] + 1e-6
    r2_survives = r2_partial > 0.03
    say("\n=== VERDICT ===")
    say(f"  behavioral down-conditioning real : {'YES' if behavioral_ok else 'NO'}")
    say(f"  cortex->reflex beyond stimulus    : {'YES' if r2_survives else 'NO / collapses'} "
        f"(partial R2={r2_partial:.3f} vs raw {r2_Z:.3f})")
    say(f"  cortical drift beyond stimulus    : {'SURVIVES' if drift_survives else 'COLLAPSES -> was stimulus'}")
    (out / "verdict.txt").write_text("\n".join(report) + "\n")
    print(f"\nwrote {out}/verdict.txt")


if __name__ == "__main__":
    main()
