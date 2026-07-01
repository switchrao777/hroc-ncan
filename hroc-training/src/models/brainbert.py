"""BrainBERT-style encoder — the 'external / pretrained' path.

Reference: Wang et al., "BrainBERT: Self-supervised representation learning for
intracranial recordings" (ICLR 2023). arxiv.org/abs/2302.14367,
github.com/czlwang/BrainBERT.

BrainBERT is a masked-spectrogram-modeling transformer: it takes an STFT
spectrogram of a neural channel, masks random time-frequency regions, and trains
a transformer to reconstruct them. The learned frame embeddings transfer to
downstream tasks. It is channel-count agnostic — which is why Chad flagged it as
usable for our single/dual-channel rat ECoG despite being pretrained on human
epilepsy sEEG.

This module ports that architecture faithfully so that:
  1. it runs end-to-end on our data today (random init), and
  2. Tarun can drop in the real pretrained checkpoint later via
     `BrainBERTEncoder.load_pretrained(path)` once the weights are downloaded.

Shared interface with ConvAutoEncoder:
    .encode(x)        -> (B, latent_dim)
    .pretrain_step(x) -> (loss, latent)      # masked-spectrogram reconstruction
    .latent_dim
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.data.preprocessing import stft_spectrogram


class BrainBERTEncoder(nn.Module):
    """Transformer over spectrogram time-frames with masked-reconstruction pretraining."""

    def __init__(
        self,
        window: int,
        latent_dim: int = 48,
        n_fft: int = 32,
        hop: int = 8,
        d_model: int = 128,
        n_heads: int = 4,
        n_layers: int = 4,
        mask_ratio: float = 0.4,
    ):
        super().__init__()
        self.latent_dim = latent_dim
        self.n_fft = n_fft
        self.hop = hop
        self.mask_ratio = mask_ratio
        self.freq_bins = n_fft // 2 + 1

        # per-frame linear projection (freq bins -> d_model)
        self.input_proj = nn.Linear(self.freq_bins, d_model)
        self.mask_token = nn.Parameter(torch.zeros(1, 1, d_model))
        self.cls_token = nn.Parameter(torch.zeros(1, 1, d_model))

        # figure out number of time frames for positional embedding
        with torch.no_grad():
            n_frames = stft_spectrogram(
                torch.zeros(1, window), n_fft=n_fft, hop=hop
            ).shape[-1]
        self.n_frames = n_frames
        self.pos_emb = nn.Parameter(torch.zeros(1, n_frames + 1, d_model))  # +1 CLS

        layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_model * 4,
            dropout=0.1, activation="gelu", batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(layer, num_layers=n_layers)

        # heads
        self.recon_head = nn.Linear(d_model, self.freq_bins)   # masked-frame reconstruction
        self.to_latent = nn.Linear(d_model, latent_dim)        # CLS -> latent

        nn.init.trunc_normal_(self.pos_emb, std=0.02)
        nn.init.trunc_normal_(self.mask_token, std=0.02)
        nn.init.trunc_normal_(self.cls_token, std=0.02)

    # ------------------------------------------------------------------ #
    def _spectrogram(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 3:
            x = x.squeeze(1)
        spec = stft_spectrogram(x, n_fft=self.n_fft, hop=self.hop)  # (B, F, N)
        return spec.transpose(1, 2)  # (B, N, F) -- frames as tokens

    def _encode_frames(self, frames: torch.Tensor) -> torch.Tensor:
        """frames: (B, N, F) -> transformer output including CLS: (B, N+1, d_model)."""
        b = frames.shape[0]
        tok = self.input_proj(frames)                                 # (B, N, d)
        cls = self.cls_token.expand(b, -1, -1)                        # (B, 1, d)
        tok = torch.cat([cls, tok], dim=1) + self.pos_emb             # (B, N+1, d)
        return self.transformer(tok)

    # ------------------------------------------------------------------ #
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Return the latent (CLS-token projection). No masking at inference."""
        frames = self._spectrogram(x)
        out = self._encode_frames(frames)
        cls = out[:, 0]                        # (B, d_model)
        return self.to_latent(cls)             # (B, latent_dim)

    def pretrain_step(self, x: torch.Tensor):
        """Masked-spectrogram reconstruction, BrainBERT-style.

        Randomly mask a fraction of frames, replace with the mask token, and ask
        the transformer to reconstruct the original frame's frequency content.
        Loss is computed only on masked frames.
        """
        frames = self._spectrogram(x)                 # (B, N, F)
        b, n, f = frames.shape

        tok = self.input_proj(frames)                 # (B, N, d)
        # build a random mask over frames
        mask = torch.rand(b, n, device=x.device) < self.mask_ratio
        mask_tok = self.mask_token.expand(b, n, -1)
        tok = torch.where(mask.unsqueeze(-1), mask_tok, tok)

        cls = self.cls_token.expand(b, -1, -1)
        seq = torch.cat([cls, tok], dim=1) + self.pos_emb
        out = self.transformer(seq)                   # (B, N+1, d)

        frame_out = out[:, 1:]                         # drop CLS
        recon = self.recon_head(frame_out)             # (B, N, F)

        if mask.any():
            loss = F.mse_loss(recon[mask], frames[mask])
        else:  # pathological tiny batch — reconstruct everything
            loss = F.mse_loss(recon, frames)

        latent = self.to_latent(out[:, 0])
        return loss, latent

    # ------------------------------------------------------------------ #
    def load_pretrained(self, path: str, strict: bool = False) -> list[str]:
        """Load real BrainBERT weights.

        The official checkpoint keys won't match 1:1 (their tokenizer/head naming
        differs), so we load non-strict and return the list of missing/unexpected
        keys for Tarun to inspect. The transformer/backbone tensors are what
        matter for transfer; the recon_head and to_latent stay randomly init and
        get trained on our data.
        """
        state = torch.load(path, map_location="cpu")
        state = state.get("model", state)  # some checkpoints wrap in {"model": ...}
        result = self.load_state_dict(state, strict=strict)
        missing = list(result.missing_keys) + list(result.unexpected_keys)
        return missing


class BrainBERTAutoEncoder(nn.Module):
    """Thin wrapper giving BrainBERT the same call surface as ConvAutoEncoder."""

    def __init__(self, window: int, latent_dim: int = 48, **kw):
        super().__init__()
        self.encoder = BrainBERTEncoder(window, latent_dim=latent_dim, **kw)
        self.latent_dim = latent_dim

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder.encode(x)

    def pretrain_step(self, x: torch.Tensor):
        return self.encoder.pretrain_step(x)
