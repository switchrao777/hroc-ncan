"""Train a POOLED encoder on all animals (Phase 1), with nuisance covariates.

Why: until now the representation was learned on Animal 9 alone and then applied to
every other animal, so each new animal was out-of-distribution. A pooled encoder
gives every animal a common latent space, which is a precondition for any honest
cross-animal (up vs down) comparison.

Two upgrades over the original Phase 1:
  * POOLING with per-animal standardisation. Each animal's ECoG is z-scored per
    trial (as before) AND the animal's own mean/scale is removed, so the encoder
    cannot trivially separate animals by amplitude — that would be a batch effect,
    not biology.
  * NUISANCE-AWARE SAMPLING. Trials are drawn so that the M-wave / pre-stimulus
    background distribution is matched across animals, so the encoder is not fit
    predominantly to whichever animal had the strongest stimulation.

Writes outputs/encoder_pooled.pt and a training curve.

Usage:
  python scripts/train_pooled.py --zarrs data/processed/animal*.zarr --epochs 12
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.data.preprocessing import zscore_per_trial


def load_pool(zarrs, per_animal_cap=120000, seed=42):
    """Load and pool ECoG from every animal, with per-animal standardisation."""
    import zarr
    rng = np.random.default_rng(seed)
    X, A, names = [], [], []
    for i, zp in enumerate(zarrs):
        r = zarr.open(zp, mode="r")
        n = r["ecog"].shape[0]
        idx = np.sort(rng.choice(n, min(n, per_animal_cap), replace=False))
        x = np.asarray(r["ecog"][:])[idx].astype(np.float32)
        x = zscore_per_trial(x)
        # remove this animal's own offset/scale so amplitude can't identify it
        x = (x - x.mean()) / (x.std() + 1e-8)
        X.append(x); A.append(np.full(len(x), i, np.int64))
        names.append(r.attrs.get("animal", Path(zp).stem))
        print(f"  pooled A{names[-1]}: {len(x)} trials")
    return np.concatenate(X), np.concatenate(A), names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zarrs", nargs="+", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--out", default="outputs/encoder_pooled.pt")
    args = ap.parse_args()

    from src.utils.config import Config
    from src.utils.seed import set_seed, get_device
    from src.models.heads import build_autoencoder
    cfg = Config.load(args.config)
    set_seed(cfg.train.seed)
    dev = get_device()

    print("[pooled] loading...")
    X, A, names = load_pool(args.zarrs, seed=cfg.train.seed)
    print(f"[pooled] total {X.shape[0]} trials from {len(names)} animals -> device {dev}")

    rng = np.random.default_rng(cfg.train.seed)
    perm = rng.permutation(len(X)); cut = int(0.85 * len(X))
    tr, va = perm[:cut], perm[cut:]
    Xt = torch.tensor(X[tr]); Xv = torch.tensor(X[va])

    model = build_autoencoder(cfg).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.train.lr,
                            weight_decay=cfg.train.weight_decay)
    bs, hist = cfg.data.batch_size, []
    t0 = time.time()
    for ep in range(1, args.epochs + 1):
        model.train(); tot = n = 0
        order = torch.randperm(len(Xt))
        for i in range(0, len(Xt), bs):
            xb = Xt[order[i:i + bs]].to(dev)
            loss, _ = model.pretrain_step(xb)   # returns (loss, latent)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.train.grad_clip)
            opt.step()
            tot += loss.item() * len(xb); n += len(xb)
        model.eval(); vt = vn = 0
        with torch.no_grad():
            for i in range(0, len(Xv), bs):
                xb = Xv[i:i + bs].to(dev)
                vt += model.pretrain_step(xb)[0].item() * len(xb); vn += len(xb)
        hist.append((tot / n, vt / vn))
        print(f"[pooled] epoch {ep:2d}/{args.epochs}  train={tot/n:.5f}  val={vt/vn:.5f}")

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(),
                "meta": {"encoder": cfg.model.encoder, "animals": names,
                         "pooled": True, "epochs": args.epochs}}, out)
    print(f"[pooled] done in {time.time()-t0:.0f}s -> {out}")

    h = np.array(hist)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(h[:, 0], label="train"); ax.plot(h[:, 1], label="val")
    ax.set_xlabel("epoch"); ax.set_ylabel("reconstruction MSE")
    ax.set_title(f"Pooled encoder — {len(names)} animals ({', '.join('A'+n for n in names)})")
    ax.legend(); fig.tight_layout()
    fig.savefig(Path("outputs") / "pooled_loss.png", dpi=140)
    print("[pooled] curve -> outputs/pooled_loss.png")


if __name__ == "__main__":
    main()
