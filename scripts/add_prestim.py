"""Add PRE-STIMULUS background (motoneuron-pool excitability) to the Zarr.

Dr. Carp's request (2026-08-05 meeting), in his words: the size of the H-reflex is
driven by two things that are NOT learning —
  1. how effective the stimulus was  -> we estimate this from the M-wave, and
  2. how excited the motoneuron pool already was -> estimate this from the EMG
     activity in the ~20 ms immediately BEFORE the stimulus.
"If the background is high just before the stimulus, the motor neuron pool is in an
excited state, therefore of course you expect a larger H reflex... that's not really
learning, that's just moment-to-moment variation."

The online system already gates trials on a background window (the `RA:` range in the
logs), but there is still variation WITHIN that allowed range. This script measures it
per trial so the model / analysis can account for it explicitly rather than having to
infer it.

Where it comes from: fragment 0 is 1000 samples @ 1 kHz = 1 s of pre-stimulus signal,
two channels in block layout (ch0 = SOLR EMG, ch1 = ECoG). We take the LAST
`--window-ms` milliseconds (default 20 ms = last 20 samples) before the stimulus.

Writes two new arrays to the Zarr:
    prestim_emg   (N,)  mean rectified pre-stimulus EMG, uV   <- the covariate
    prestim_ecog  (N,)  same for the cortical channel (cortical state proxy)

Usage:
  python scripts/add_prestim.py --dsn "mysql+pymysql://root@localhost/emg_eeg_9?unix_socket=/tmp/hroc_mysql.sock" \
      --zarr data/processed/animal9.zarr
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

PRESTIM_FRAGMENT = 0
DATA_TABLE = "channel_data"
AD2UV = 2.441406
ENDIAN = "<"          # little-endian, confirmed
FRAG0_HZ = 1000       # 1 kHz


def iter_prestim(engine, window_samples: int):
    """Yield (trial, prestim_emg_uV, prestim_ecog_uV) for every trial.

    frag0 blob = 1000 int16 for ch0 then 1000 int16 for ch1 (block layout). We only
    need the tail of each channel, so we slice rather than decoding everything.
    """
    from sqlalchemy import text
    dt = np.dtype(ENDIAN + "i2")
    with engine.connect().execution_options(stream_results=True) as c:
        rows = c.execute(text(
            f"SELECT trial, data, nSamples FROM {DATA_TABLE} "
            f"WHERE fragment = {PRESTIM_FRAGMENT} ORDER BY trial"))
        for trial, blob, nsamp in rows:
            a = np.frombuffer(blob, dtype=dt)
            n = int(nsamp)
            if a.size < 2 * n:
                yield int(trial), np.nan, np.nan
                continue
            ch0 = a[:n].astype(np.float32) * AD2UV          # EMG
            ch1 = a[n:2 * n].astype(np.float32) * AD2UV     # ECoG
            w = min(window_samples, n)
            e, g = ch0[-w:], ch1[-w:]
            # mean rectified about the segment's own mean (removes DC offset)
            yield (int(trial),
                   float(np.abs(e - e.mean()).mean()),
                   float(np.abs(g - g.mean()).mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", required=True)
    ap.add_argument("--zarr", required=True)
    ap.add_argument("--window-ms", type=float, default=20.0,
                    help="pre-stimulus window length in ms (Carp suggested ~20)")
    args = ap.parse_args()

    win = int(round(args.window_ms / 1000.0 * FRAG0_HZ))
    from sqlalchemy import create_engine
    eng = create_engine(args.dsn)

    trials, pe, pg = [], [], []
    for i, (t, e, g) in enumerate(iter_prestim(eng, win)):
        trials.append(t); pe.append(e); pg.append(g)
        if (i + 1) % 50000 == 0:
            print(f"[prestim]   {i+1} trials...")
    pe = np.array(pe, dtype=np.float32); pg = np.array(pg, dtype=np.float32)
    print(f"[prestim] {len(trials)} trials, window = last {win} samples ({args.window_ms:g} ms)")
    print(f"[prestim] pre-stim EMG  median {np.nanmedian(pe):.1f} uV  "
          f"(IQR {np.nanpercentile(pe,25):.1f}-{np.nanpercentile(pe,75):.1f})")
    print(f"[prestim] pre-stim ECoG median {np.nanmedian(pg):.1f} uV")

    import zarr
    root = zarr.open(args.zarr, mode="a")
    n_zarr = root["ecog"].shape[0]
    if n_zarr != len(trials):
        sys.exit(f"row mismatch: zarr {n_zarr} vs frag0 {len(trials)} — same ORDER BY trial?")
    for name, arr in [("prestim_emg", pe), ("prestim_ecog", pg)]:
        if name in root:
            del root[name]
        z = root.create_array(name, shape=arr.shape, dtype=arr.dtype)
        z[:] = arr
    print(f"[prestim] added prestim_emg + prestim_ecog to {args.zarr}")


if __name__ == "__main__":
    main()
