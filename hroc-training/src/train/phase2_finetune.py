"""Phase 2 — supervised H-reflex regression on the frozen encoder.

Freeze the Phase-1 encoder, attach an MLP head, and predict per-trial H-reflex
amplitude from the latent vector. We report R^2 and MSE on a held-out val set.
A high R^2 from a *frozen* encoder is the key evidence that the unsupervised
latent space captured H-reflex-relevant structure.
"""
from __future__ import annotations

from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from src.utils.config import Config
from src.utils.seed import get_device
from src.models.heads import HReflexHead
from src.train.trainer import MetricLog, save_checkpoint, Timer, human_time


def _r2(pred: torch.Tensor, target: torch.Tensor) -> float:
    ss_res = torch.sum((target - pred) ** 2)
    ss_tot = torch.sum((target - target.mean()) ** 2)
    return (1 - ss_res / (ss_tot + 1e-8)).item()


@torch.no_grad()
def _evaluate(encoder, head, loader, device):
    encoder.eval(); head.eval()
    preds, targets = [], []
    for batch in loader:
        x = batch["ecog"].to(device)
        y = batch["hreflex"].to(device)
        z = encoder.encode(x)
        preds.append(head(z).cpu())
        targets.append(y.cpu())
    pred = torch.cat(preds); target = torch.cat(targets)
    return F.mse_loss(pred, target).item(), _r2(pred, target)


def finetune(cfg: Config, encoder: torch.nn.Module,
             train_dl: DataLoader, val_dl: DataLoader) -> HReflexHead:
    device = get_device()
    encoder = encoder.to(device)
    for p in encoder.parameters():          # freeze
        p.requires_grad = False
    encoder.eval()

    head = HReflexHead(cfg.model.latent_dim).to(device)
    opt = torch.optim.AdamW(head.parameters(), lr=cfg.train.lr,
                            weight_decay=cfg.train.weight_decay)
    log = MetricLog(Path(cfg.train.out_dir) / "phase2_metrics.jsonl")

    print(f"[phase2] frozen encoder, training MLP head "
          f"({sum(p.numel() for p in head.parameters()):,} params)")
    with Timer() as t:
        for ep in range(1, cfg.train.phase2_epochs + 1):
            head.train()
            tot, n = 0.0, 0
            for batch in train_dl:
                x = batch["ecog"].to(device)
                y = batch["hreflex"].to(device)
                with torch.no_grad():
                    z = encoder.encode(x)
                pred = head(z)
                loss = F.mse_loss(pred, y)
                opt.zero_grad(); loss.backward(); opt.step()
                tot += loss.item() * x.size(0); n += x.size(0)
            val_mse, val_r2 = _evaluate(encoder, head, val_dl, device)
            log.log(epoch=ep, train_mse=tot / n, val_mse=val_mse, val_r2=val_r2)
            print(f"[phase2] epoch {ep:2d}/{cfg.train.phase2_epochs}  "
                  f"train_mse={tot/n:.5f}  val_mse={val_mse:.5f}  val_R2={val_r2:.3f}")
    log.save()
    save_checkpoint(head, Path(cfg.train.out_dir) / "hreflex_head.pt")
    final_mse, final_r2 = _evaluate(encoder, head, val_dl, device)
    print(f"[phase2] done in {human_time(t.elapsed)}  final val R^2 = {final_r2:.3f}")
    return head
