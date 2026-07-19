"""Add per-trial recording time + day to the Zarr, and export a trial->time CSV.

THE KEY FACT (for Tarun): the timestamp is NOT in the log file and needs no
separate `elizan_db` dump. It's a column — `time` (unix seconds) — on every row
of the `channel_data` data table, right next to `trial`, `fragment`, and `data`.
The raw-byte decoder_2006 path simply drops it; the MySQL path carries it for
free. So: read the row's `time` field and you're done.

This script pulls (trial, time) for the ERP fragment, then:
  1. writes `outputs/animal9_trial_time.csv`  (columns: trial, time_unix, day)
     -- portable; JOIN it onto your trials BY TRIAL NUMBER (robust even if your
        decode produced a different trial count than this one).
  2. if --zarr matches row-for-row (same N, same `ORDER BY trial` order the
     converter uses), adds `time` (int64) and `day` (int64) arrays to it.

Usage:
  python scripts/add_timestamps.py \
      --dsn "mysql+pymysql://root@localhost/emg_eeg_9?unix_socket=/tmp/hroc_mysql.sock" \
      --zarr data/processed/animal9.zarr
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

ERP_FRAGMENT = 1
DATA_TABLE = "channel_data"


def fetch_trial_times(dsn: str):
    """Return (trials, times) arrays for the ERP fragment, ordered by trial —
    the SAME order convert.py writes Zarr rows in, so positions line up."""
    from sqlalchemy import create_engine, text
    eng = create_engine(dsn)
    trials, times = [], []
    with eng.connect() as c:
        rows = c.execute(text(
            f"SELECT trial, time FROM {DATA_TABLE} "
            f"WHERE fragment = {ERP_FRAGMENT} ORDER BY trial"))
        for tr, ts in rows:
            trials.append(int(tr)); times.append(int(ts))
    return np.array(trials, dtype=np.int64), np.array(times, dtype=np.int64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", required=True, help="SQLAlchemy DSN for the animal DB")
    ap.add_argument("--zarr", default="data/processed/animal9.zarr")
    ap.add_argument("--csv", default="outputs/animal9_trial_time.csv")
    args = ap.parse_args()

    trials, times = fetch_trial_times(args.dsn)
    day = (times - times.min()) // 86400          # day 0 = first recording day
    print(f"[timestamps] {len(trials)} ERP trials  "
          f"span {times.max()-times.min():,} s = {day.max()+1} days")

    # 1) portable CSV keyed by trial number
    out_csv = Path(args.csv); out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["trial", "time_unix", "day"])
        for tr, ts, d in zip(trials, times, day):
            w.writerow([tr, ts, int(d)])
    print(f"[timestamps] wrote {out_csv}  (join onto your trials BY `trial`)")

    # 2) add arrays to the Zarr if it lines up row-for-row
    zpath = Path(args.zarr)
    if not zpath.exists():
        print(f"[timestamps] no zarr at {zpath}; CSV only."); return
    import zarr
    root = zarr.open(str(zpath), mode="a")
    n_zarr = root["ecog"].shape[0]
    if n_zarr != len(trials):
        print(f"[timestamps] WARNING: zarr has {n_zarr} rows but DB returned "
              f"{len(trials)} ERP trials — NOT the same decode. Skipping in-place "
              f"add; use the CSV and join by `trial` instead.")
        return
    for name, arr in [("time", times), ("day", day.astype(np.int64))]:
        if name in root:
            del root[name]
        z = root.create_array(name, shape=arr.shape, dtype=arr.dtype)
        z[:] = arr
    print(f"[timestamps] added `time` and `day` arrays to {zpath} "
          f"({n_zarr} rows, aligned to trial order)")


if __name__ == "__main__":
    main()
