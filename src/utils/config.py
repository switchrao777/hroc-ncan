"""Typed config loaded from config.yaml.

Everything tunable lives in config.yaml so Tarun never edits code to change a
hyperparameter or a data path. This module just turns that YAML into a typed
object with sane defaults.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import yaml


# The six HROC conditioning phases, in temporal order. This ordering is the
# x-axis of the novel result: does the latent centroid drift across it?
# Phase id -> name. Ids 0-2 are what Animal 9 actually ran (recovered from the
# type-15 log); 3-5 are placeholders for animals that ran the fuller protocol.
# NOTE: match these to each animal's real protocol before trusting the labels.
PHASES = [
    "Baseline",
    "Down-conditioning",
    "Post-conditioning",
    "Phase 3",
    "Phase 4",
    "Phase 5",
]


@dataclass
class SignalConfig:
    """Physical parameters of the Animal-9 ERP window (from the reverse-eng work)."""
    sample_rate_hz: int = 5000          # frag1 sample rate
    window_samples: int = 150           # Animal 9 = 150 samples = 30 ms
    ad2uv: float = 2.441406             # int16 -> microvolts
    mwave_ms: tuple = (2.0, 4.0)        # direct motor response latency
    hreflex_ms: tuple = (8.0, 10.0)     # spinal reflex latency (nominal)
    # Matched window for the mean-rectified-amplitude label (Carp's spec).
    # WIDEN to encompass the full burst once you've seen the trial average.
    hreflex_window_ms: tuple = (7.0, 12.0)
    baseline_window_ms: tuple = (0.0, 2.0)


@dataclass
class DataConfig:
    # --- multi-animal (the real path) ---
    # List of {id: "9", zarr_path: "data/animal9.zarr"} dicts. When non-empty,
    # all listed animals are pooled into one training set. This is the default
    # real-data mode.
    animals: list = field(default_factory=list)
    # ECoG/EMG windows differ by format (150 samples for 2006, 250 for 2013), so
    # every animal is resampled to this common length before pooling. Labels are
    # computed per-animal on the NATIVE signal in the converter, so this only
    # affects the autoencoder input, not the H-reflex amplitude.
    common_window_samples: int = 200

    # --- single-store / smoke-test fallbacks ---
    zarr_path: str = ""                  # single real store (ignored if animals set)
    use_synthetic: bool = False          # True => fabricate data, no real files
    n_trials_synthetic: int = 12000
    n_animals_synthetic: int = 3         # for the multi-animal smoke test

    batch_size: int = 128
    val_fraction: float = 0.15
    num_workers: int = 0


@dataclass
class ModelConfig:
    encoder: str = "conv_ae"             # "conv_ae" (from scratch) | "brainbert"
    latent_dim: int = 48                 # Chad suggested 32-64
    # conv_ae specifics
    base_channels: int = 32
    # brainbert specifics (spectrogram transformer)
    n_fft: int = 32
    hop: int = 8
    d_model: int = 128
    n_heads: int = 4
    n_layers: int = 4
    brainbert_weights: str = ""          # path to real pretrained .pth (optional)


@dataclass
class TrainConfig:
    phase1_epochs: int = 15
    phase2_epochs: int = 15
    lr: float = 1e-3
    weight_decay: float = 1e-5
    grad_clip: float = 1.0
    seed: int = 42
    out_dir: str = "outputs"


@dataclass
class Config:
    signal: SignalConfig = field(default_factory=SignalConfig)
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    train: TrainConfig = field(default_factory=TrainConfig)

    @staticmethod
    def load(path: str | Path) -> "Config":
        raw = yaml.safe_load(Path(path).read_text()) or {}
        return Config(
            signal=SignalConfig(**raw.get("signal", {})),
            data=DataConfig(**raw.get("data", {})),
            model=ModelConfig(**raw.get("model", {})),
            train=TrainConfig(**raw.get("train", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
