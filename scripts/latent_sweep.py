"""Choose the embedding size by held-out reconstruction.

For each input and each candidate size, train the same convolutional autoencoder on
trials pooled across animals and score reconstruction on held-out DAYS: every 5th
recording day of every animal is never trained on. The score is the fraction of
variance explained on those days, FVE = 1 - SSE / SST.

Selection rule, fixed before looking at results: the smallest size whose held-out
FVE is within one percentage point of the best size. Reconstruction keeps improving
slightly with more dimensions; the rule picks where extra dimensions stop paying.
The size is chosen on reconstruction only, never on how well it predicts the reflex.

Inputs
  post      30 ms response window at 5 kHz (the input of the current model)
  pre       1 s pre-stimulus waveform at 1 kHz, mains-notched
  pre_spec  1 s pre-stimulus log power spectrum, 1-199 Hz (phase-invariant)

Outputs (outputs/latent_sweep/):
  sweep_<input>.csv   size, train FVE, held-out FVE, seconds
  norm_<input>.npz    per-animal normalisation, reused when encoding
  enc_<input>_k<k>.pt one checkpoint per size
  sweep.png, choice.json

Usage:
  python scripts/latent_sweep.py --inputs post pre pre_spec --dims 2 4 8 16 24 32 48 64
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams.update({"font.size": 13, "axes.labelsize": 15, "axes.titlesize": 16,
    "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 12})

ANIMALS = ["9", "10", "11", "3", "4"]      # A12 excluded: failed ECoG electrode
OUT = Path("outputs/latent_sweep")
TEST_EVERY = 5                               # every 5th recording day is held out
TOLERANCE = 0.01                             # selection rule, in FVE
LABEL = {"post": "30 ms after stimulus", "pre": "1 s before, waveform",
         "pre_spec": "1 s before, spectrum"}


def zpath(a):
    return f"data/processed/animal{a}.zarr"


def prepare(inp, r, idx, chunk=20000):
    """Rows `idx` of the chosen input, before per-animal normalisation."""
    from src.data.preprocessing import zscore_per_trial
    from src.data.prestim import clean_wave, log_spectrum
    arr = r["ecog"] if inp == "post" else r["prestim_ecog_wave"]
    out = []
    for lo in range(0, len(idx), chunk):
        x = arr.get_orthogonal_selection((idx[lo:lo + chunk], slice(None)))
        if inp == "post":
            x = zscore_per_trial(x.astype(np.float32))
        else:
            x = clean_wave(x)
            if inp == "pre_spec":
                x = log_spectrum(x)
        out.append(x)
    return np.concatenate(out)


def fit_norm(inp, X):
    """Remove each animal's own scale (and, for spectra, its mean spectrum) so the
    encoder cannot tell animals apart by electrode characteristics."""
    if inp == "post":                        # already z-scored per trial
        return {"mu": np.zeros(1, np.float32), "sd": np.ones(1, np.float32)}
    if inp == "pre":                         # keep per-trial power: it carries band power
        return {"mu": np.zeros(1, np.float32),
                "sd": np.array([np.median(X.std(axis=1))], np.float32)}
    mu = X.mean(axis=0, keepdims=True)
    return {"mu": mu.astype(np.float32), "sd": np.array([(X - mu).std()], np.float32)}


def apply_norm(X, nm):
    return ((X - nm["mu"]) / nm["sd"]).astype(np.float32)


def load_norm(inp):
    z = np.load(OUT / f"norm_{inp}.npz")
    return {a: {"mu": z[f"{a}_mu"], "sd": z[f"{a}_sd"]} for a in ANIMALS if f"{a}_mu" in z}


def load_model(inp, k, dev):
    import torch
    from src.models.autoencoder import ConvAutoEncoder
    ck = torch.load(OUT / f"enc_{inp}_k{k}.pt", map_location="cpu")
    m = ConvAutoEncoder(ck["meta"]["window"], latent_dim=k, base=32)
    m.load_state_dict(ck["model"])
    return m.to(dev).eval()


def encode_rows(inp, r, idx, nm, model, dev, chunk=20000):
    """Embeddings for rows `idx`, streamed so a full animal never sits in memory."""
    import torch
    Z = []
    with torch.no_grad():
        for lo in range(0, len(idx), chunk):
            x = apply_norm(prepare(inp, r, idx[lo:lo + chunk]), nm)
            for b in range(0, len(x), 4096):
                Z.append(model.encode(torch.from_numpy(x[b:b + 4096]).to(dev)).cpu().numpy())
    return np.concatenate(Z)


def fve(model, X, dev):
    import torch
    sse, mu = 0.0, X.mean(axis=0)
    sst = float(((X - mu) ** 2).sum())
    model.eval()
    with torch.no_grad():
        for b in range(0, len(X), 4096):
            xb = torch.from_numpy(X[b:b + 4096]).to(dev)
            rec = model(xb)[0].squeeze(1)
            sse += float(((rec - xb) ** 2).sum())
    return 1.0 - sse / sst


def train_ae(Xtr, k, epochs, dev, seed=42):
    import torch
    from src.models.autoencoder import ConvAutoEncoder
    torch.manual_seed(seed)
    m = ConvAutoEncoder(Xtr.shape[1], latent_dim=k, base=32).to(dev)
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3, weight_decay=1e-5)
    Xt, g = torch.from_numpy(Xtr), torch.Generator().manual_seed(seed)
    for _ in range(epochs):
        m.train()
        for b in torch.randperm(len(Xt), generator=g).split(256):
            loss, _ = m.pretrain_step(Xt[b].to(dev))
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
            opt.step()
    return m


def choose(rows):
    best = max(r[2] for r in rows)
    return min(r[0] for r in rows if r[2] >= best - TOLERANCE)


def summarise():
    choice, fig = {}, plt.figure(figsize=(9, 5.2))
    ax = fig.gca()
    for inp in LABEL:
        f = OUT / f"sweep_{inp}.csv"
        if not f.exists():
            continue
        rows = np.loadtxt(f, delimiter=",", skiprows=1, ndmin=2)
        rows = [tuple(x) for x in rows]
        k = int(choose(rows)); choice[inp] = k
        ks = [r[0] for r in rows]; te = [r[2] for r in rows]
        ln, = ax.plot(ks, te, "-o", lw=2.4, label=f"{LABEL[inp]}  (chosen {k})")
        ax.plot([k], [dict((r[0], r[2]) for r in rows)[k]], "o", ms=15, mfc="none",
                mec=ln.get_color(), mew=2.5)
    ax.set_xscale("log", base=2); ax.set_xticks([2, 4, 8, 16, 32, 64])
    ax.set_xticklabels(["2", "4", "8", "16", "32", "64"])
    ax.set_xlabel("embedding size (numbers per trial)")
    ax.set_ylabel("held-out variance explained")
    ax.set_title("Reconstruction on days the model never saw")
    ax.legend(frameon=False, loc="lower right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(OUT / "sweep.png", dpi=150); plt.close(fig)
    (OUT / "choice.json").write_text(json.dumps(choice, indent=2))
    print(f"[sweep] chosen sizes: {choice}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", default=["post", "pre", "pre_spec"])
    ap.add_argument("--dims", nargs="+", type=int, default=[2, 4, 8, 16, 24, 32, 48, 64])
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--cap", type=int, default=40000, help="trials per animal")
    args = ap.parse_args()

    import torch
    import zarr
    from src.utils.seed import get_device
    dev = get_device()
    OUT.mkdir(parents=True, exist_ok=True)

    for inp in args.inputs:
        rng = np.random.default_rng(42)
        Xtr, Xte, norms = [], [], {}
        for a in ANIMALS:
            r = zarr.open(zpath(a), mode="r")
            day = np.asarray(r["day"])
            ok = np.ones(len(day), bool) if inp == "post" else np.asarray(r["prestim_ok"])
            pool = np.where(ok)[0]
            idx = np.sort(rng.choice(pool, min(len(pool), args.cap), replace=False))
            X = prepare(inp, r, idx)
            norms[a] = fit_norm(inp, X)
            X = apply_norm(X, norms[a])
            test = (day[idx] % TEST_EVERY) == TEST_EVERY - 1
            Xtr.append(X[~test]); Xte.append(X[test])
            print(f"[sweep] {inp} A{a}: {int((~test).sum())} train / {int(test.sum())} held-out",
                  flush=True)
        np.savez(OUT / f"norm_{inp}.npz",
                 **{f"{a}_{key}": v for a, nm in norms.items() for key, v in nm.items()})
        Xtr, Xte = np.concatenate(Xtr), np.concatenate(Xte)
        sub = Xtr[np.random.default_rng(0).choice(len(Xtr), min(len(Xtr), 20000), replace=False)]

        rows = []
        for k in args.dims:
            t0 = time.time()
            m = train_ae(Xtr, k, args.epochs, dev)
            rows.append((k, fve(m, sub, dev), fve(m, Xte, dev), time.time() - t0))
            torch.save({"model": m.state_dict(),
                        "meta": {"input": inp, "latent_dim": k, "window": Xtr.shape[1],
                                 "animals": ANIMALS, "epochs": args.epochs}},
                       OUT / f"enc_{inp}_k{k}.pt")
            print(f"[sweep] {inp} k={k:2d}  train FVE {rows[-1][1]:.4f}  "
                  f"held-out FVE {rows[-1][2]:.4f}  ({rows[-1][3]:.0f}s)", flush=True)
            np.savetxt(OUT / f"sweep_{inp}.csv", np.array(rows), delimiter=",",
                       header="k,train_fve,heldout_fve,seconds", comments="", fmt="%.6g")
        summarise()


if __name__ == "__main__":
    main()
