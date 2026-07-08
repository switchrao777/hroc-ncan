"""Shared training utilities used by both phases."""
from __future__ import annotations

import json
import time
from pathlib import Path

import torch


class MetricLog:
    """Tiny JSON-lines metric logger so we can plot loss curves for the deck."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: list[dict] = []

    def log(self, **kw):
        self.records.append(kw)

    def save(self):
        self.path.write_text("\n".join(json.dumps(r) for r in self.records))


def save_checkpoint(model: torch.nn.Module, path: str | Path, meta: dict | None = None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(), "meta": meta or {}}, path)


def load_checkpoint(model: torch.nn.Module, path: str | Path, map_location="cpu"):
    ckpt = torch.load(path, map_location=map_location)
    model.load_state_dict(ckpt["model"])
    return ckpt.get("meta", {})


def count_params(model: torch.nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def human_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}m{s:02d}s"


class Timer:
    def __enter__(self):
        self.t0 = time.time()
        return self

    def __exit__(self, *a):
        self.elapsed = time.time() - self.t0
