"""Store the full 1-s PRE-STIMULUS ECoG waveform for every trial.

The 30 ms response window is too short to contain slow cortical rhythms: one theta
cycle lasts 125-250 ms and one beta cycle 33-77 ms. Fragment 0 holds the second
before each stimulus at 1 kHz, which does. This copies it into the Zarr so the
encoder can be trained on pre-stimulus cortical state.

Fragment 0 = nSamples (normally 1000) little-endian int16 for ch0 (EMG), then the
same for ch1 (ECoG). The ECoG is stored in raw ADC units (int16) to halve disk use;
multiply by 2.441406 for microvolts. Rows follow `ORDER BY trial`, the same order
the converter used for the response window, and the row count is checked.

Writes to the Zarr:
    prestim_ecog_wave  (N, 1000) int16   raw units, right-aligned to stimulus onset
    prestim_ok         (N,)      bool    False where the fragment was missing or short

Usage:
  python scripts/add_prestim_wave.py --animal 9
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

SOCK = "/tmp/hroc_mysql.sock"
N_PRE = 1000          # 1 s at 1 kHz
CHUNK = 20000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--animal", required=True)
    ap.add_argument("--zarr", default=None)
    args = ap.parse_args()
    zp = args.zarr or f"data/processed/animal{args.animal}.zarr"

    import zarr
    from sqlalchemy import create_engine, text
    root = zarr.open(zp, mode="a")
    n = root["ecog"].shape[0]
    for name in ("prestim_ecog_wave", "prestim_ok"):
        if name in root:
            del root[name]
    W = root.create_array("prestim_ecog_wave", shape=(n, N_PRE), dtype="int16",
                          chunks=(CHUNK, N_PRE))
    ok = np.zeros(n, dtype=bool)

    eng = create_engine(f"mysql+pymysql://root@localhost/emg_eeg_{args.animal}"
                        f"?unix_socket={SOCK}")
    buf = np.zeros((CHUNK, N_PRE), np.int16)
    i = start = 0
    with eng.connect().execution_options(stream_results=True) as c:
        res = c.execute(text("SELECT data, nSamples FROM channel_data "
                             "WHERE fragment = 0 ORDER BY trial"))
        for blob, ns in res:
            if i >= n:
                sys.exit(f"row mismatch: fragment 0 has more rows than the zarr ({n})")
            a = np.frombuffer(blob, dtype="<i2")
            ns = int(ns)
            row = buf[i - start]
            row[:] = 0
            if ns > 0 and a.size >= 2 * ns:
                w = min(ns, N_PRE)
                row[-w:] = a[ns:2 * ns][-w:]
                ok[i] = ns >= N_PRE
            i += 1
            if i - start == CHUNK:
                W[start:i] = buf
                start = i
                print(f"[prestim-wave] A{args.animal}: {i}/{n}", flush=True)
    if i > start:
        W[start:i] = buf[:i - start]
    if i != n:
        sys.exit(f"row mismatch: zarr {n} vs fragment 0 {i}")

    z = root.create_array("prestim_ok", shape=(n,), dtype="bool")
    z[:] = ok
    print(f"[prestim-wave] A{args.animal}: {n} trials, {ok.mean():.1%} complete -> {zp}")


if __name__ == "__main__":
    main()
