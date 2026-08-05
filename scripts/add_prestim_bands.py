"""Extract PRE-STIMULUS cortical band power from fragment 0.

Why this matters more than the evoked response: everything measured *after* the
stimulus is open to the objection that the ECoG electrode is picking up muscle
activity (EMG->ECoG crosstalk), since both channels record simultaneously. Activity
measured BEFORE the stimulus cannot be contaminated by a response that has not
happened yet. So if pre-stimulus cortical state predicts how big the reflex will be,
that is a much harder result to explain away — and it is a real mechanism: cortical
state modulating spinal excitability.

Band power is also the standard way ECoG is analysed, and it separates plausible
neural signal (delta/theta/alpha/beta) from the high-frequency range where EMG
contamination lives (>100 Hz).

Fragment 0 = 1000 samples @ 1 kHz = 1 s before the stimulus, block layout
(ch0 = EMG, ch1 = ECoG). We take the final `--window-ms` (default 512 ms) of the
ECoG channel and compute log power in six bands.

Writes to the Zarr:
    prestim_bands  (N, 6) float32   log power: delta theta alpha beta gamma high
    prestim_emg_bands (N, 6)        same for the EMG channel (for the crosstalk test)

Usage:
  python scripts/add_prestim_bands.py --dsn "...emg_eeg_9..." --zarr data/processed/animal9.zarr
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

FRAG = 0
TABLE = "channel_data"
AD2UV = 2.441406
FS = 1000.0                      # frag0 sample rate
BANDS = [(1, 4), (4, 8), (8, 13), (13, 30), (30, 100), (100, 200)]
BAND_NAMES = ["delta", "theta", "alpha", "beta", "gamma", "high"]


def band_power(seg: np.ndarray) -> np.ndarray:
    """(n, w) segments -> (n, 6) log band power via rFFT."""
    seg = seg - seg.mean(axis=1, keepdims=True)
    w = np.hanning(seg.shape[1])[None, :]
    P = np.abs(np.fft.rfft(seg * w, axis=1)) ** 2
    f = np.fft.rfftfreq(seg.shape[1], d=1.0 / FS)
    out = np.empty((seg.shape[0], len(BANDS)), dtype=np.float32)
    for i, (lo, hi) in enumerate(BANDS):
        m = (f >= lo) & (f < hi)
        out[:, i] = np.log10(P[:, m].mean(axis=1) + 1e-6)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", required=True)
    ap.add_argument("--zarr", required=True)
    ap.add_argument("--window-ms", type=float, default=512.0)
    ap.add_argument("--chunk", type=int, default=20000)
    args = ap.parse_args()

    win = int(round(args.window_ms / 1000.0 * FS))
    from sqlalchemy import create_engine, text
    eng = create_engine(args.dsn)
    dt = np.dtype("<i2")

    ecog_rows, emg_rows, buf_e, buf_m, n = [], [], [], [], 0
    with eng.connect().execution_options(stream_results=True) as c:
        res = c.execute(text(f"SELECT data, nSamples FROM {TABLE} "
                             f"WHERE fragment={FRAG} ORDER BY trial"))
        for blob, nsamp in res:
            a = np.frombuffer(blob, dtype=dt); ns = int(nsamp)
            if a.size < 2 * ns:
                buf_m.append(np.zeros(win, np.float32)); buf_e.append(np.zeros(win, np.float32))
            else:
                m_ = a[:ns].astype(np.float32) * AD2UV
                e_ = a[ns:2 * ns].astype(np.float32) * AD2UV
                w = min(win, ns)
                pm = np.zeros(win, np.float32); pe = np.zeros(win, np.float32)
                pm[-w:] = m_[-w:]; pe[-w:] = e_[-w:]
                buf_m.append(pm); buf_e.append(pe)
            n += 1
            if len(buf_e) >= args.chunk:
                ecog_rows.append(band_power(np.stack(buf_e)))
                emg_rows.append(band_power(np.stack(buf_m)))
                buf_e, buf_m = [], []
                print(f"[bands]   {n} trials...")
    if buf_e:
        ecog_rows.append(band_power(np.stack(buf_e)))
        emg_rows.append(band_power(np.stack(buf_m)))

    E = np.concatenate(ecog_rows); M = np.concatenate(emg_rows)
    print(f"[bands] {n} trials, window = last {win} ms")
    for i, nm in enumerate(BAND_NAMES):
        print(f"   ECoG {nm:6s} median log-power {np.median(E[:, i]):7.3f}")

    import zarr
    root = zarr.open(args.zarr, mode="a")
    if root["ecog"].shape[0] != E.shape[0]:
        sys.exit(f"row mismatch: zarr {root['ecog'].shape[0]} vs frag0 {E.shape[0]}")
    for name, arr in [("prestim_bands", E), ("prestim_emg_bands", M)]:
        if name in root:
            del root[name]
        z = root.create_array(name, shape=arr.shape, dtype=arr.dtype)
        z[:] = arr
    root.attrs["band_names"] = BAND_NAMES
    print(f"[bands] added prestim_bands + prestim_emg_bands to {args.zarr}")


if __name__ == "__main__":
    main()
