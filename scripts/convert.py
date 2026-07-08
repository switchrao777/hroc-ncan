"""MyISAM (MySQL) -> Zarr converter for the ani-emg-eeg animals.

This turns one animal's loaded MySQL database into the Zarr store the training
pipeline consumes:

    animalN.zarr/
      ecog     (N, 150)  float32
      emg      (N, 150)  float32
      hreflex  (N,)      float32   # mean rectified amplitude, Carp's spec
      phase    (N,)      int64     # conditioning phase 0..5

WHAT'S COMPLETE vs WHAT'S A HOOK
--------------------------------
Complete: the Zarr writing, the label computation, batching, and the CLI.
Hooks (3 functions marked `# HOOK`): reading raw trial rows, decoding the 2006
blob, and parsing phases from the log table. These depend on the lab's exact
table schema and `decoder_2006.py`, which are on the machine with the data, not
here. SETUP.md walks Claude Code through completing them at Checkpoint 2/3, using
the known constants below and the reference decode as a starting point.

KNOWN 2006-FORMAT CONSTANTS (from the reverse-engineering work; verify against
decoder_2006.py before trusting):
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
    "n_channels": 2,             # ch0 = SOLR EMG, ch1 = ECoG (CONFIRMED via decode)
    "record_bytes": 8536,        # (unused — we read blobs via MySQL, not raw bytes)
    "endian": "<",               # LITTLE-endian — CONFIRMED 2026-07-07. decoder_2006's
                                 # "big-endian" docstring is WRONG for emg-eeg-9 (big
                                 # decodes to pure noise; little gives clean M/H waves).
}

# The ERP response lives in fragment 1 (150 samples @ 5 kHz). frag0/frag2 are the
# 1 kHz baseline/late fragments and are not used for the model input.
ERP_FRAGMENT = 1
DATA_TABLE = "channel_data"      # real Elizan III table name (was generic `trials`)
LOG_TABLE = "log_data"


# ------------------------------------------------------------------ HOOK 1  (DONE)
def fetch_one_raw(engine):
    """Return the raw frag1 blob for a single trial (Checkpoint-2 decode test)."""
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


# ------------------------------------------------------------------ HOOK 2
def decode_trial(raw: bytes) -> dict:
    """Decode one 2006 blob into {'ecog': (150,), 'emg': (150,)} in microvolts.

    HOOK: the authoritative decoder is the lab's `decoder_2006.py`. Import and
    call it here once located:
        from decoder_2006 import decode_record
        ch = decode_record(raw)           # however it returns channels
    The reference below matches the documented 2006 layout (big-endian int16,
    block channel order: all of ch0 then all of ch1) and is a STARTING POINT to
    verify against the real decoder on one trial — do not trust it blindly.

    NOTE: Animal 9 (and likely all) need baseline subtraction using frag0 from
    the PRECEDING record. That cross-record step belongs in iter_raw_trials /
    a wrapper, not here. Flag at Checkpoint 2.
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


# ------------------------------------------------------------------ HOOK 3  (DONE)
# Phase names by id. Animal 9 ran Baseline -> Down-conditioning -> Post (NOT the
# full 6-phase protocol). Other animals may add up-conditioning / freely-running;
# extend PHASE_MARKERS below if their logs contain those markers.
PHASE_NAMES = {0: "Baseline", 1: "HRdown", 2: "Post"}

# Regex -> phase id. Scanned against type-15 log text, in chronological order, to
# find the timestamp where each phase BEGINS. Baseline (0) is implicit from start.
import re
PHASE_MARKERS = [
    (re.compile(r"start\s*hrdown", re.I), 1),      # down-conditioning begins
    (re.compile(r"stopped\s*conditioning", re.I), 2),  # post-conditioning begins
    # (re.compile(r"start\s*hrup", re.I), <id>),   # add for animals with up-cond
]


def parse_phases(engine):
    """Return sorted phase intervals [(start_unix, phase_id), ...] from type-15 log.

    Baseline (phase 0) is implicit from the session start. Each PHASE_MARKER match
    opens a new phase at its log timestamp. A trial is assigned the phase of the
    latest boundary at or before its own `time`.
    """
    from sqlalchemy import text
    with engine.connect() as c:
        rows = c.execute(text(
            f"SELECT time, text FROM {LOG_TABLE} WHERE type = 15 ORDER BY time"
        )).fetchall()

    boundaries = [(0, 0)]  # (unix_time, phase_id): phase 0 from the beginning
    for t, txt in rows:
        for rx, pid in PHASE_MARKERS:
            if rx.search(txt or ""):
                boundaries.append((int(t), pid))
                break
    boundaries.sort()
    return boundaries


def assign_phase(ts: int, boundaries) -> int:
    """Phase id for a trial timestamp: the last boundary whose time <= ts."""
    pid = 0
    for btime, bpid in boundaries:
        if ts >= btime:
            pid = bpid
        else:
            break
    return pid


# ------------------------------------------------------------------ complete
def convert(dsn: str, animal_id: str, out_path: str, cfg: Config,
            limit: int | None = None):
    """Full conversion: decode all trials, label, phase, write Zarr."""
    import zarr
    from sqlalchemy import create_engine
    eng = create_engine(dsn)

    boundaries = parse_phases(eng)                  # HOOK 3 (type-15 log)
    print(f"[convert] phase boundaries (unix_time -> phase): {boundaries}")

    ecog, emg, phase = [], [], []
    for i, (tid, raw, ts) in enumerate(iter_raw_trials(eng)):
        if limit and i >= limit:
            break
        d = decode_trial(raw)                       # HOOK 2
        ecog.append(d["ecog"]); emg.append(d["emg"])
        phase.append(assign_phase(int(ts), boundaries))
        if (i + 1) % 25000 == 0:
            print(f"[convert]   decoded {i+1} trials...")
    ecog = np.stack(ecog); emg = np.stack(emg)
    phase = np.array(phase, dtype=np.int64)

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
    print(f"[convert] animal {animal_id}: wrote {ecog.shape[0]} trials -> {out}")
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
