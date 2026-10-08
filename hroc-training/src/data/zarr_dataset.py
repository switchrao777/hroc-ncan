"""Dataset layer.

`build_datasets(cfg)` is the single entry point. It returns train/val
`HROCDataset` objects. It either:
  * loads the real Zarr store Chad recommended (cfg.data.use_synthetic=False), or
  * fabricates synthetic Animal-9-like data (cfg.data.use_synthetic=True).

The Zarr layout Tarun should write (from the SQLAlchemy -> Zarr converter) is:

    store.zarr/
      ecog     (N, window)  float32   # cortical channel, the AE input
      emg      (N, window)  float32   # EMG channel (optional, validation)
      hreflex  (N,)         float32   # per-trial H-reflex amplitude label
      phase    (N,)         int64     # conditioning phase 0..5

Once the converter writes that, flipping use_synthetic to False is the only
change needed here.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

from src.utils.config import Config
from src.data.preprocessing import zscore_per_trial
from src.data import synthetic


class HROCDataset(Dataset):
    """Wraps in-memory arrays. Signals are z-scored per trial at construction."""

    def __init__(
        self,
        ecog: np.ndarray,
        hreflex: np.ndarray,
        phase: np.ndarray,
        emg: np.ndarray | None = None,
        normalize: bool = True,
    ):
        if normalize:
            ecog = zscore_per_trial(ecog)
        self.ecog = torch.from_numpy(ecog.astype(np.float32))
        self.hreflex = torch.from_numpy(hreflex.astype(np.float32))
        self.phase = torch.from_numpy(phase.astype(np.int64))
        self.emg = None if emg is None else torch.from_numpy(emg.astype(np.float32))

    def __len__(self) -> int:
        return self.ecog.shape[0]

    def __getitem__(self, i: int) -> dict[str, torch.Tensor]:
        item = {
            "ecog": self.ecog[i],
            "hreflex": self.hreflex[i],
            "phase": self.phase[i],
        }
        if self.emg is not None:
            item["emg"] = self.emg[i]
        return item


def _load_zarr(path: str) -> dict[str, np.ndarray]:
    import zarr

    root = zarr.open(path, mode="r")
    out = {
        "ecog": np.asarray(root["ecog"]),
        "hreflex": np.asarray(root["hreflex"]),
        "phase": np.asarray(root["phase"]),
    }
    if "emg" in root:
        out["emg"] = np.asarray(root["emg"])
    return out


def _split(data: dict[str, np.ndarray], val_fraction: float, seed: int):
    n = data["ecog"].shape[0]
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    n_val = int(n * val_fraction)
    val_idx, train_idx = idx[:n_val], idx[n_val:]
    take = lambda d, ix: {k: v[ix] for k, v in d.items()}
    return take(data, train_idx), take(data, val_idx)


def build_datasets(cfg: Config) -> tuple[HROCDataset, HROCDataset]:
    if cfg.data.use_synthetic:
        data = synthetic.generate(
            cfg.signal,
            n_trials=cfg.data.n_trials_synthetic,
            seed=cfg.train.seed,
        )
    else:
        if not cfg.data.zarr_path or not Path(cfg.data.zarr_path).exists():
            raise FileNotFoundError(
                f"use_synthetic=False but zarr_path '{cfg.data.zarr_path}' not found. "
                "Point cfg.data.zarr_path at the real store or set use_synthetic=True."
            )
        data = _load_zarr(cfg.data.zarr_path)

    train_raw, val_raw = _split(data, cfg.data.val_fraction, cfg.train.seed)
    train_ds = HROCDataset(
        train_raw["ecog"], train_raw["hreflex"], train_raw["phase"],
        emg=train_raw.get("emg"),
    )
    val_ds = HROCDataset(
        val_raw["ecog"], val_raw["hreflex"], val_raw["phase"],
        emg=val_raw.get("emg"),
    )
    return train_ds, val_ds


def build_loaders(cfg: Config) -> tuple[DataLoader, DataLoader]:
    train_ds, val_ds = build_datasets(cfg)
    train_dl = DataLoader(
        train_ds, batch_size=cfg.data.batch_size, shuffle=True,
        num_workers=cfg.data.num_workers, drop_last=True,
    )
    val_dl = DataLoader(
        val_ds, batch_size=cfg.data.batch_size, shuffle=False,
        num_workers=cfg.data.num_workers,
    )
    return train_dl, val_dl
