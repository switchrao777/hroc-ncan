"""End-to-end HROC training run.

    python scripts/run_all.py --config config.yaml

Pipeline:
    1. build data (synthetic Animal-9-like, or real Zarr if configured)
    2. Phase 1: unsupervised autoencoder pretraining (all trials)
    3. Phase 2: frozen-encoder MLP predicting H-reflex amplitude
    4. Latent analysis: UMAP + centroid drift across the 6 conditioning phases
    5. Loss-curve figures for the slide deck

Everything lands in outputs/.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# make `src` importable when run from repo root
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.utils.config import Config
from src.utils.seed import set_seed
from src.data.zarr_dataset import build_loaders
from src.train.phase1_pretrain import pretrain
from src.train.phase2_finetune import finetune
from src.analysis.latent_umap import analyze, extract_latents
from src.analysis import neuro_figures


def _plot_loss_curves(out_dir: Path):
    for phase, key in [("phase1", "val_recon"), ("phase2", "val_mse")]:
        p = out_dir / f"{phase}_metrics.jsonl"
        if not p.exists():
            continue
        recs = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
        ep = [r["epoch"] for r in recs]
        fig, ax = plt.subplots(figsize=(7, 4.5))
        if phase == "phase1":
            ax.plot(ep, [r["train_recon"] for r in recs], "-o", label="train", ms=4)
            ax.plot(ep, [r["val_recon"] for r in recs], "-o", label="val", ms=4)
            ax.set_ylabel("reconstruction MSE")
            ax.set_title("Phase 1 — unsupervised pretraining")
        else:
            ax.plot(ep, [r["train_mse"] for r in recs], "-o", label="train MSE", ms=4)
            ax.plot(ep, [r["val_mse"] for r in recs], "-o", label="val MSE", ms=4)
            ax2 = ax.twinx()
            ax2.plot(ep, [r["val_r2"] for r in recs], "-s", color="#16a34a",
                     label="val R²", ms=4)
            ax2.set_ylabel("val R²", color="#16a34a")
            ax.set_ylabel("MSE")
            ax.set_title("Phase 2 — H-reflex regression (frozen encoder)")
        ax.set_xlabel("epoch"); ax.legend(loc="upper right")
        fig.tight_layout(); fig.savefig(out_dir / f"{phase}_loss.png", dpi=150)
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()

    cfg = Config.load(args.config)
    set_seed(cfg.train.seed)
    out_dir = Path(cfg.train.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if cfg.data.animals:
        ids = ", ".join(str(a["id"]) for a in cfg.data.animals)
        mode = f"REAL pooled animals [{ids}]"
    elif cfg.data.use_synthetic:
        mode = "SYNTHETIC (multi-animal smoke test)"
    else:
        mode = f"REAL single ({cfg.data.zarr_path})"
    print("=" * 64)
    print(f"HROC training run  |  data={mode}  |  encoder={cfg.model.encoder}")
    print("=" * 64)

    train_dl, val_dl = build_loaders(cfg)

    encoder = pretrain(cfg, train_dl, val_dl)          # Phase 1
    finetune(cfg, encoder, train_dl, val_dl)           # Phase 2
    results = analyze(cfg, encoder, val_dl)            # UMAP + drift
    # neuro-result figures for Carp (val loader is unshuffled, so order aligns)
    lat, ph, hr, _an = extract_latents(cfg, encoder, val_dl)
    emg = val_dl.dataset.emg
    emg = emg.numpy() if emg is not None else None
    neuro_figures.make_all(cfg, lat, ph, hr, emg)
    _plot_loss_curves(out_dir)                         # deck figures

    (out_dir / "run_summary.json").write_text(json.dumps({
        "config": cfg.to_dict(),
        "results": results,
    }, indent=2))
    print("\nDone. Artifacts in", out_dir.resolve())


if __name__ == "__main__":
    main()
