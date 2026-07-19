"""End-to-end for ONE animal: load -> convert -> timestamps -> QC -> analyses.

Assumes the animal's MyISAM is already in MariaDB (run scripts/load_animal.py
first) and the Phase-1 encoder exists (outputs/encoder_phase1.pt). Chains:
  convert.py -> add_timestamps.py -> validate_zarr.py -> confound_control.py
  -> drift_over_time.py, writing per-animal outputs to outputs/animalN/.

Usage:
  python scripts/load_animal.py --animal 10 --dir ~/Downloads/ani-emg-eeg-10
  python scripts/run_animal.py  --animal 10
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOCK = "/tmp/hroc_mysql.sock"


def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    if subprocess.run(cmd, cwd=ROOT).returncode:
        sys.exit(f"step failed: {cmd[1] if len(cmd) > 1 else cmd}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--animal", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    a = args.animal
    db = f"emg_eeg_{a}"
    dsn = f"mysql+pymysql://root@localhost/{db}?unix_socket={SOCK}"
    zarr = f"data/processed/animal{a}.zarr"
    outdir = f"outputs/animal{a}"
    py = args.python

    run([py, "scripts/convert.py", "--dsn", dsn, "--animal", a, "--out", zarr, "--config", args.config])
    run([py, "scripts/add_timestamps.py", "--dsn", dsn, "--zarr", zarr,
         "--csv", f"{outdir}/trial_time.csv"])
    run([py, "scripts/validate_zarr.py", "--zarr", zarr, "--out", f"{outdir}/validate"])
    run([py, "scripts/confound_control.py", "--config", args.config, "--zarr", zarr,
         "--out", f"{outdir}/confound"])
    run([py, "scripts/drift_over_time.py", "--config", args.config, "--zarr", zarr,
         "--out", f"{outdir}/drift"])

    print(f"\n=== animal {a} done -> {outdir}/ ===")
    print("Check, in order: confound/learning_curve.png (did conditioning work?), "
          "drift/null_control.png (does the metric make artifacts?), drift/verdict.txt.")


if __name__ == "__main__":
    main()
