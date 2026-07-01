"""Phase 1 — unsupervised pretraining.

Train the encoder to reconstruct the ECoG signal (waveform MSE for conv_ae,
masked-spectrogram MSE for brainbert) using ALL trials, including intermittent
'i' trials that carry no H-reflex label. No labels are used here. The output is
a frozen-ready encoder whose latent space we later probe.
"""
from __future__ import annotations

from pathlib import Path

import torch
from torch.utils.data import DataLoader

from src.utils.config import Config
from src.utils.seed import get_device
from src.models.heads import build_autoencoder
from src.train.trainer import MetricLog, save_checkpoint, count_params, Timer, human_time


def _run_epoch(model, loader, optimizer, device, grad_clip, train: bool):
    model.train(train)
    total, n = 0.0, 0
    torch.set_grad_enabled(train)
    for batch in loader:
        x = batch["ecog"].to(device)
        loss, _ = model.pretrain_step(x)
        if train:
            optimizer.zero_grad()
            loss.backward()
            if grad_clip:
                torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()
        total += loss.item() * x.size(0)
        n += x.size(0)
    torch.set_grad_enabled(True)
    return total / max(n, 1)


def pretrain(cfg: Config, train_dl: DataLoader, val_dl: DataLoader) -> torch.nn.Module:
    device = get_device()
    model = build_autoencoder(cfg).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.train.lr,
                            weight_decay=cfg.train.weight_decay)
    log = MetricLog(Path(cfg.train.out_dir) / "phase1_metrics.jsonl")

    print(f"[phase1] encoder={cfg.model.encoder}  params={count_params(model):,}  "
          f"device={device}")
    with Timer() as t:
        for ep in range(1, cfg.train.phase1_epochs + 1):
            tr = _run_epoch(model, train_dl, opt, device, cfg.train.grad_clip, True)
            va = _run_epoch(model, val_dl, opt, device, cfg.train.grad_clip, False)
            log.log(epoch=ep, train_recon=tr, val_recon=va)
            print(f"[phase1] epoch {ep:2d}/{cfg.train.phase1_epochs}  "
                  f"train={tr:.5f}  val={va:.5f}")
    log.save()
    ckpt = Path(cfg.train.out_dir) / "encoder_phase1.pt"
    save_checkpoint(model, ckpt, meta={"encoder": cfg.model.encoder,
                                       "latent_dim": cfg.model.latent_dim})
    print(f"[phase1] done in {human_time(t.elapsed)} -> {ckpt}")
    return model
