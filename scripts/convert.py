"""MyISAM (MySQL) -> Zarr converter for the ani-emg-eeg animals.

This turns one animal's loaded MySQL database into the Zarr store the training
pipeline consumes:

    animalN.zarr/
      ecog     (N, 150)  float32
      emg      (N, 150)  float32
      hreflex  (N,)      float32   # mean rectified amplitude, matched window
      phase    (N,)      int64     # 0 = baseline, 1 = conditioning

Format constants below were established empirically and verified against the
decoded waveform (a stimulus artifact followed by an M-wave and an H-reflex at
the latencies the experimenters recorded in the log).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from src.utils.config import Config
from src.data.hreflex_label import compute_hreflex_label

SIGNAL = {
    "sample_rate_hz": 5000,
    "window_samples": 150,       # 30 ms ERP window (Animal 9 / all 2006 animals)
    "ad2uv": 2.441406,           # int16 -> microvolts (confirmed: log type-5 entry)
    "n_channels": 2,             # ch0 = soleus EMG, ch1 = ECoG
    "endian": "<",               # little-endian; the archived decoder documents
                                 # big-endian, which decodes to noise.
}

# The ERP response lives in fragment 1 (150 samples @ 5 kHz). frag0/frag2 are the
# 1 kHz baseline/late fragments and are not used for the model input.
ERP_FRAGMENT = 1
DATA_TABLE = "channel_data"
LOG_TABLE = "log_data"


def fetch_one_raw(engine):
    """Return the raw frag1 blob for a single trial."""
    from sqlalchemy import text
    with engine.connect() as c:
        row = c.execute(text(
            f"SELECT data FROM {DATA_TABLE} WHERE fragment = {ERP_FRAGMENT} LIMIT 1"
        )).fetchone()
    if row is None:
        raise RuntimeError("no rows returned — check DATA_TABLE / fragment filter")
    return row[0]


def iter_raw_trials(engine):
    """Yield (trial_id, raw_frag1_blob, unix_time) for every ERP trial, in order.

    Streams server-side (stream_results) so the 2.3 GB table doesn't load at once.
    """
    from sqlalchemy import text
    with engine.connect().execution_options(stream_results=True) as c:
        result = c.execute(text(
            f"SELECT trial, data, time FROM {DATA_TABLE} "
            f"WHERE fragment = {ERP_FRAGMENT} ORDER BY trial"
        ))
        for row in result:
            yield row[0], row[1], row[2]


def decode_trial(raw: bytes) -> dict:
    """Decode one blob into {'ecog': (150,), 'emg': (150,)} in microvolts.

    Little-endian int16 in block channel order: the first 150 samples are the
    soleus EMG channel, the next 150 the cortical ECoG channel.
    """
    n = SIGNAL["window_samples"]
    dt = np.dtype(SIGNAL["endian"] + "i2")
    samples = np.frombuffer(raw, dtype=dt)
    # block order: first n = ch0, next n = ch1 (per Elizan III manual 4.5.3)
    if samples.size < 2 * n:
        raise ValueError(f"trial too short: {samples.size} < {2*n} samples")
    ch0 = samples[:n].astype(np.float32) * SIGNAL["ad2uv"]
    ch1 = samples[n:2 * n].astype(np.float32) * SIGNAL["ad2uv"]
    return {"emg": ch0, "ecog": ch1}   # confirm which channel is which!


# Two phases: 0 = baseline, 1 = conditioning. The log's "stopped conditioning"
# marker is unreliable (the reflex continues to change after it), so only the
# onset marker is used. That marker also carries the conditioning direction.
PHASE_NAMES = {0: "Baseline", 1: "Conditioning"}

import re
# Onset = first appearance of "HRdown"/"HRup". Matches both "Start HRdown" and
# "Started HRup conditioning"; does not match "HR interval: 6-9".
_ONSET = re.compile(r"hr\s*(down|up)", re.I)
_UP = re.compile(r"\bhr\s*up\b|up-?cond", re.I)
_DOWN = re.compile(r"\bhr\s*down\b|down-?cond", re.I)


def parse_phases(engine):
    """Return (boundaries, direction). boundaries = [(unix_time, phase_id), ...];
    direction in {'down','up','unknown'} from the first onset marker."""
    from sqlalchemy import text
    with engine.connect() as c:
        rows = c.execute(text(
            f"SELECT time, text FROM {LOG_TABLE} WHERE type = 15 ORDER BY time"
        )).fetchall()

    boundaries = [(0, 0)]                 # phase 0 (baseline) from the beginning
    direction = "unknown"
    for t, txt in rows:
        m = _ONSET.search(txt or "")
        if m and len(boundaries) == 1:    # first onset opens the conditioning phase
            boundaries.append((int(t), 1))
            direction = m.group(1).lower()   # 'down' or 'up'
    # fallback: some logs write the direction without the word "start"
    if direction == "unknown":
        allo = " ".join((txt or "") for _, txt in rows)
        if _UP.search(allo) and not _DOWN.search(allo):
            direction = "up"
        elif _DOWN.search(allo) and not _UP.search(allo):
            direction = "down"
    boundaries.sort()
    return boundaries, direction


def assign_phase(ts: int, boundaries) -> int:
    """Phase id for a trial timestamp: the last boundary whose time <= ts."""
    pid = 0
    for btime, bpid in boundaries:
        if ts >= btime:
            pid = bpid
        else:
            break
    return pid


def convert(dsn: str, animal_id: str, out_path: str, cfg: Config,
            limit: int | None = None):
    """Full conversion: decode all trials, label, phase, write Zarr."""
    import zarr
    from sqlalchemy import create_engine
    eng = create_engine(dsn)

    boundaries, direction = parse_phases(eng)       # from the type-15 log
    print(f"[convert] direction={direction}  boundaries(unix->phase)={boundaries}")

    ecog, emg, phase, times = [], [], [], []
    for i, (tid, raw, ts) in enumerate(iter_raw_trials(eng)):
        if limit and i >= limit:
            break
        d = decode_trial(raw)
        ecog.append(d["ecog"]); emg.append(d["emg"])
        phase.append(assign_phase(int(ts), boundaries))
        times.append(int(ts))                       # per-trial recording time
        if (i + 1) % 25000 == 0:
            print(f"[convert]   decoded {i+1} trials...")
    ecog = np.stack(ecog); emg = np.stack(emg)
    phase = np.array(phase, dtype=np.int64)
    # recording time (unix s) + day index (0 = first recording day). `day`
    # is what the drift-per-day analysis groups on — see scripts/confound_control.py.
    time_arr = np.array(times, dtype=np.int64)
    day = (time_arr - time_arr.min()) // 86400

    # label = mean rectified amplitude, matched window (Carp's spec)
    hreflex = compute_hreflex_label(
        emg, cfg.signal,
        hreflex_window_ms=cfg.signal.hreflex_window_ms,
        baseline_window_ms=cfg.signal.baseline_window_ms,
    )

    out = Path(out_path)
    root = zarr.open(str(out), mode="w")

    def _write(name, arr):
        # zarr 3.x API: create_array then assign (create_dataset was removed).
        z = root.create_array(name, shape=arr.shape, dtype=arr.dtype)
        z[:] = arr

    _write("ecog", ecog.astype(np.float32))
    _write("emg", emg.astype(np.float32))
    _write("hreflex", hreflex.astype(np.float32))
    _write("phase", phase)
    _write("time", time_arr)                         # unix seconds per trial
    _write("day", day.astype(np.int64))              # day index for drift-per-day
    root.attrs["direction"] = direction              # 'down' | 'up' | 'unknown'
    root.attrs["animal"] = str(animal_id)
    print(f"[convert] animal {animal_id} ({direction}-conditioned): "
          f"wrote {ecog.shape[0]} trials ({day.max()+1} days) -> {out}")
    # per-phase counts for the human
    for p in sorted(set(phase.tolist())):
        print(f"   phase {p} ({PHASE_NAMES.get(p,'?')}): {(phase == p).sum()} trials")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", required=True)
    ap.add_argument("--animal", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--limit", type=int, default=None, help="cap trials (for a quick test)")
    args = ap.parse_args()
    convert(args.dsn, args.animal, args.out, Config.load(args.config), args.limit)


if __name__ == "__main__":
    main()
