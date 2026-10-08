"""1-D convolutional autoencoder — the 'from scratch' encoder path.

This is the baseline Chad described: encode the raw ECoG window into a compact
latent, decode it back, train on reconstruction MSE over ALL trials (including
intermittent 'i' trials that have no H-reflex label).

Interface shared with BrainBERTAutoEncoder:
    .encode(x)  -> (B, latent_dim)
    .forward(x) -> (recon, latent)
    .latent_dim
"""
from __future__ import annotations

import torch
import torch.nn as nn


class ConvEncoder(nn.Module):
    def __init__(self, window: int, latent_dim: int, base: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(1, base, kernel_size=7, stride=2, padding=3),      # 150 -> 75
            nn.BatchNorm1d(base), nn.GELU(),
            nn.Conv1d(base, base * 2, kernel_size=5, stride=2, padding=2),  # 75 -> 38
            nn.BatchNorm1d(base * 2), nn.GELU(),
            nn.Conv1d(base * 2, base * 4, kernel_size=3, stride=2, padding=1),  # 38 -> 19
            nn.BatchNorm1d(base * 4), nn.GELU(),
        )
        # figure out flattened size dynamically
        with torch.no_grad():
            dummy = torch.zeros(1, 1, window)
            flat = self.net(dummy).flatten(1).shape[1]
        self._flat = flat
        self._conv_len = flat // (base * 4)
        self._base = base
        self.to_latent = nn.Linear(flat, latent_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.net(x)                 # (B, C, L)
        h = h.flatten(1)                # (B, C*L)
        return self.to_latent(h)        # (B, latent_dim)


class ConvDecoder(nn.Module):
    def __init__(self, window: int, latent_dim: int, base: int, conv_len: int):
        super().__init__()
        self._base = base
        self._conv_len = conv_len
        self._window = window
        self.from_latent = nn.Linear(latent_dim, base * 4 * conv_len)
        self.net = nn.Sequential(
            nn.ConvTranspose1d(base * 4, base * 2, kernel_size=3, stride=2,
                               padding=1, output_padding=1),
            nn.BatchNorm1d(base * 2), nn.GELU(),
            nn.ConvTranspose1d(base * 2, base, kernel_size=5, stride=2,
                               padding=2, output_padding=1),
            nn.BatchNorm1d(base), nn.GELU(),
            nn.ConvTranspose1d(base, 1, kernel_size=7, stride=2,
                               padding=3, output_padding=1),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        h = self.from_latent(z).view(-1, self._base * 4, self._conv_len)
        out = self.net(h)                       # (B, 1, ~window)
        # crop/pad to exact window length
        if out.shape[-1] != self._window:
            out = torch.nn.functional.interpolate(
                out, size=self._window, mode="linear", align_corners=False
            )
        return out


class ConvAutoEncoder(nn.Module):
    def __init__(self, window: int, latent_dim: int = 48, base: int = 32):
        super().__init__()
        self.latent_dim = latent_dim
        self.encoder = ConvEncoder(window, latent_dim, base)
        self.decoder = ConvDecoder(window, latent_dim, base, self.encoder._conv_len)

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 2:
            x = x.unsqueeze(1)          # (B, T) -> (B, 1, T)
        return self.encoder(x)

    def forward(self, x: torch.Tensor):
        if x.dim() == 2:
            x = x.unsqueeze(1)
        z = self.encoder(x)
        recon = self.decoder(z)
        return recon, z

    def pretrain_step(self, x: torch.Tensor):
        """Uniform interface with BrainBERT: waveform reconstruction MSE."""
        import torch.nn.functional as F
        if x.dim() == 2:
            x = x.unsqueeze(1)
        recon, z = self.forward(x)
        loss = F.mse_loss(recon, x)
        return loss, z
