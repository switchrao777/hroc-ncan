"""Phase-2 head + model factory.

Phase 2 (Chad's supervised stage): freeze the encoder, attach a small MLP on top
of the latent vector, and regress the per-trial H-reflex amplitude. If the frozen
latent already carries H-reflex information, this head learns it easily — which is
evidence the unsupervised representation is meaningful.
"""
from __future__ import annotations

import torch
import torch.nn as nn

from src.utils.config import Config
from src.models.autoencoder import ConvAutoEncoder
from src.models.brainbert import BrainBERTAutoEncoder


class HReflexHead(nn.Module):
    """Small MLP: latent -> scalar H-reflex amplitude."""

    def __init__(self, latent_dim: int, hidden: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, hidden),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Linear(hidden // 2, 1),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z).squeeze(-1)


def build_autoencoder(cfg: Config) -> nn.Module:
    """Factory selecting the encoder path from config."""
    window = cfg.signal.window_samples
    m = cfg.model
    if m.encoder == "conv_ae":
        return ConvAutoEncoder(window, latent_dim=m.latent_dim, base=m.base_channels)
    if m.encoder == "brainbert":
        return BrainBERTAutoEncoder(
            window,
            latent_dim=m.latent_dim,
            n_fft=m.n_fft,
            hop=m.hop,
            d_model=m.d_model,
            n_heads=m.n_heads,
            n_layers=m.n_layers,
        )
    raise ValueError(f"unknown encoder '{m.encoder}' (use 'conv_ae' or 'brainbert')")
