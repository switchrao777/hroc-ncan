"""Inspect the loaded MyISAM DB and decode ONE trial (Checkpoint 2 gate).

Before converting ~95k trials, prove that (a) we can read the tables and (b) a
single trial decodes into a sane waveform. Run this first. If the printed
waveform doesn't show the M-wave / H-reflex bumps, STOP — the decode is wrong and
mass conversion would just produce garbage faster.

Usage:
    python scripts/inspect_db.py --dsn mysql+pymysql://user:pass@localhost/emg_eeg_9
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", required=True, help="SQLAlchemy DSN for the loaded animal DB")
    ap.add_argument("--out", default="outputs/inspect", help="where to drop the decode plot")
    args = ap.parse_args()

    from sqlalchemy import create_engine, text
    eng = create_engine(args.dsn)

    # 1) list tables + row counts so we know what we're working with
    with eng.connect() as c:
        tables = [r[0] for r in c.execute(text("SHOW TABLES"))]
        print("tables:", tables)
        for t in tables:
            n = c.execute(text(f"SELECT COUNT(*) FROM `{t}`")).scalar()
            cols = [row[0] for row in c.execute(text(f"SHOW COLUMNS FROM `{t}`"))]
            print(f"  {t}: {n} rows | columns: {cols}")

    # 2) decode ONE trial.
    #    HOOK: replace `fetch_one_raw` + `decode_trial` with the lab's real
    #    decoder_2006 once you've located it (SETUP.md, Checkpoint 2).
    from scripts.convert import fetch_one_raw, decode_trial, SIGNAL
    raw = fetch_one_raw(eng)
    trial = decode_trial(raw)
    ecog, emg = trial["ecog"], trial["emg"]
    print(f"\ndecoded one trial: ecog {ecog.shape}, emg {emg.shape}")
    print(f"ecog range [{ecog.min():.1f}, {ecog.max():.1f}] uV | "
          f"emg range [{emg.min():.1f}, {emg.max():.1f}] uV")

    # 3) plot it so a human can eyeball the M/H bumps
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    t_ms = np.arange(len(emg)) / SIGNAL["sample_rate_hz"] * 1000.0
    fig, ax = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax[0].plot(t_ms, emg); ax[0].set_ylabel("EMG (uV)"); ax[0].set_title("Decoded trial — check for M (~2-4ms) + H (~8-10ms) bumps")
    ax[0].axvspan(2, 4, color="#fde68a", alpha=.4); ax[0].axvspan(8, 10, color="#bbf7d0", alpha=.5)
    ax[1].plot(t_ms, ecog, color="#7c3aed"); ax[1].set_ylabel("ECoG (uV)"); ax[1].set_xlabel("ms")
    fig.tight_layout(); fig.savefig(out / "decoded_trial.png", dpi=150)
    print(f"\nwrote {out/'decoded_trial.png'} — LOOK AT IT before continuing.")


if __name__ == "__main__":
    main()
