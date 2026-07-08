"""Reproducibility helpers.

Neural-data results need to be reproducible before Dr. Carp / Chad will trust
a latent-space drift figure. Call `set_seed(...)` at the top of every entry
point.
"""
from __future__ import annotations

import os
import random

import numpy as np
import torch


def set_seed(seed: int = 42, deterministic: bool = True) -> None:
    """Seed python, numpy and torch RNGs.

    Args:
        seed: the integer seed.
        deterministic: if True, forces cuDNN into deterministic mode. Slightly
            slower but guarantees the same latent space every run, which is what
            we want when comparing phase-drift figures across experiments.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def get_device(prefer_cuda: bool = True) -> torch.device:
    """Pick the best available device.

    Order: CUDA (cloud/Windows NVIDIA) -> MPS (Apple Silicon Mac GPU) -> CPU.
    The models here are small, so an M-series MacBook trains them comfortably on
    MPS; no discrete GPU or cloud is needed.
    """
    if prefer_cuda and torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")
