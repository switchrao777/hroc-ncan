"""Dataset layer.

`build_datasets(cfg)` is the single entry point. It returns train/val
`HROCDataset` objects and pools data across ALL animals listed in the config.

Real-data mode (default): set `cfg.data.animals` to a list of
    {id: "9", zarr_path: "data/animal9.zarr"}
entries. Every animal's store is loaded, resampled to a common window length
(because 2006 format = 150 samples, 2013 format = 250 samples), tagged with an
animal id, and pooled. One autoencoder then learns a representation across all
animals.

Each per-animal Zarr store (written by the converter) must contain:

    store.zarr/
      ecog     (N, window)  float32   # cortical channel, the AE input
      emg      (N, window)  float32   # EMG channel (optional, validation)
      hreflex  (N,)         float32   # per-trial H-reflex amplitude label
      phase    (N,)         int64     # conditioning phase 0..5

IMPORTANT: the `hreflex` label is computed per-animal on the NATIVE signal in the
converter (correct latencies / sample rate). Resampling here only touches the
ecog/emg the autoencoder sees, never the label.

Fallbacks: if `animals` is empty, uses single `zarr_path`, or `use_synthetic`
for a smoke test (which now fabricates multiple fake animals with different
window lengths so the pooling path is exercised).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

from src.utils.config import Config
from src.data.preprocessing import zscore_per_trial
from src.data import synthetic


def _resample(x: np.ndarray, target_len: int) -> np.ndarray:
    """Resample (N, T) -> (N, target_len) by linear interpolation.

    Used to bring different-format windows (150 vs 250 samples) to a common
    length so animals can be pooled. Linear interp preserves waveform shape well
    enough for representation learning; exact latencies live in the label, which
    is computed before this step.
    """
    if x.shape[1] == target_len:
        return x.astype(np.float32)
    t = torch.from_numpy(x.astype(np.float32)).unsqueeze(1)   # (N,1,T)
    out = F.interpolate(t, size=target_len, mode="linear", align_corners=False)
    return out.squeeze(1).numpy()


class HROCDataset(Dataset):
    """Wraps in-memory arrays. Signals are z-scored per trial at construction."""

    def __init__(self, ecog, hreflex, phase, emg=None, animal=None, normalize=True):
        if normalize:
            ecog = zscore_per_trial(ecog)
        self.ecog = torch.from_numpy(ecog.astype(np.float32))
        self.hreflex = torch.from_numpy(hreflex.astype(np.float32))
        self.phase = torch.from_numpy(phase.astype(np.int64))
        self.emg = None if emg is None else torch.from_numpy(emg.astype(np.float32))
        self.animal = (None if animal is None
                       else torch.from_numpy(animal.astype(np.int64)))

    def __len__(self) -> int:
        return self.ecog.shape[0]

    def __getitem__(self, i: int) -> dict:
        item = {"ecog": self.ecog[i], "hreflex": self.hreflex[i],
                "phase": self.phase[i]}
        if self.emg is not None:
            item["emg"] = self.emg[i]
        if self.animal is not None:
            item["animal"] = self.animal[i]
        return item


def _load_zarr(path: str) -> dict[str, np.ndarray]:
    import zarr
    root = zarr.open(path, mode="r")
    out = {"ecog": np.asarray(root["ecog"]),
           "hreflex": np.asarray(root["hreflex"]),
           "phase": np.asarray(root["phase"])}
    if "emg" in root:
        out["emg"] = np.asarray(root["emg"])
    return out


def _load_pooled(cfg: Config) -> tuple[dict[str, np.ndarray], list[str]]:
    """Load + resample + concatenate every configured animal.

    Returns (pooled_dict, animal_id_names) where pooled_dict has an extra
    `animal` integer array indexing into animal_id_names.
    """
    animals = cfg.data.animals
    tgt = cfg.data.common_window_samples

    # decide sources: animals list > single zarr_path > synthetic
    if animals:
        sources = [(a["id"], a["zarr_path"]) for a in animals]
        raw_stores = []
        for aid, path in sources:
            if not Path(path).exists():
                raise FileNotFoundError(f"animal {aid}: zarr '{path}' not found")
            raw_stores.append((str(aid), _load_zarr(path)))
    elif cfg.data.zarr_path:
        if not Path(cfg.data.zarr_path).exists():
            raise FileNotFoundError(f"zarr_path '{cfg.data.zarr_path}' not found")
        raw_stores = [("single", _load_zarr(cfg.data.zarr_path))]
    elif cfg.data.use_synthetic:
        raw_stores = synthetic.generate_multi(
            cfg.signal, n_animals=cfg.data.n_animals_synthetic,
            n_trials=cfg.data.n_trials_synthetic, seed=cfg.train.seed)
    else:
        raise ValueError(
            "No data source. Set cfg.data.animals (real, preferred), "
            "cfg.data.zarr_path (single), or cfg.data.use_synthetic=True.")

    id_names = [aid for aid, _ in raw_stores]
    ecog, emg, hreflex, phase, animal = [], [], [], [], []
    have_emg = all("emg" in d for _, d in raw_stores)
    for idx, (aid, d) in enumerate(raw_stores):
        n = d["ecog"].shape[0]
        ecog.append(_resample(d["ecog"], tgt))
        if have_emg:
            emg.append(_resample(d["emg"], tgt))
        hreflex.append(d["hreflex"].astype(np.float32))
        phase.append(d["phase"].astype(np.int64))
        animal.append(np.full(n, idx, dtype=np.int64))

    pooled = {
        "ecog": np.concatenate(ecog),
        "hreflex": np.concatenate(hreflex),
        "phase": np.concatenate(phase),
        "animal": np.concatenate(animal),
    }
    if have_emg:
        pooled["emg"] = np.concatenate(emg)
    return pooled, id_names


def _split(data: dict[str, np.ndarray], val_fraction: float, seed: int):
    n = data["ecog"].shape[0]
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    n_val = int(n * val_fraction)
    val_idx, train_idx = idx[:n_val], idx[n_val:]
    take = lambda d, ix: {k: v[ix] for k, v in d.items()}
    return take(data, train_idx), take(data, val_idx)


# animal id names from the most recent build, for analysis labelling
ANIMAL_NAMES: list[str] = []


def build_datasets(cfg: Config) -> tuple[HROCDataset, HROCDataset]:
    global ANIMAL_NAMES
    data, ANIMAL_NAMES = _load_pooled(cfg)
    tr, va = _split(data, cfg.data.val_fraction, cfg.train.seed)
    mk = lambda d: HROCDataset(d["ecog"], d["hreflex"], d["phase"],
                               emg=d.get("emg"), animal=d.get("animal"))
    return mk(tr), mk(va)


def build_loaders(cfg: Config) -> tuple[DataLoader, DataLoader]:
    train_ds, val_ds = build_datasets(cfg)
    train_dl = DataLoader(train_ds, batch_size=cfg.data.batch_size, shuffle=True,
                          num_workers=cfg.data.num_workers, drop_last=True)
    val_dl = DataLoader(val_ds, batch_size=cfg.data.batch_size, shuffle=False,
                        num_workers=cfg.data.num_workers)
    return train_dl, val_dl
