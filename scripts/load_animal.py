"""Load one animal's MyISAM tables into the local MariaDB (automates the manual
steps used for Animal 9). Then convert.py can point at it.

Given a folder containing an animal's files (any of):
    emg-eeg-N-data.MYD  emg-eeg-N-data.MYI  emg-eeg-N-data.frm
    emg-eeg-N-log.MYD   emg-eeg-N-log.MYI   emg-eeg-N-log.frm
it creates database `emg_eeg_N`, installs the tables as `channel_data` and
`log_data`, rebuilds any missing index, and prints the DSN for convert.py.

Missing `.frm` is tolerated (uses the authoritative Animal-9 schema as a template
— verified identical across the 2006 emg-eeg set).

Usage:
    python scripts/load_animal.py --animal 10 --dir ~/Downloads/ani-emg-eeg-10
"""
from __future__ import annotations

import argparse
import glob
import shutil
import subprocess
import sys
from pathlib import Path

SOCK = "/tmp/hroc_mysql.sock"
DATADIR = Path("/Users/suchithrao/Downloads/hroc-training/.mariadb_data")
TEMPL = Path("/Users/suchithrao/Downloads/ani-emg-eeg-9-full/ani-emg-eeg-9")  # data+log .frm templates


def sql(q, db=""):
    r = subprocess.run(["mariadb", "--no-defaults", "-uroot", f"--socket={SOCK}"]
                       + ([db] if db else []) + ["-N", "-e", q],
                       capture_output=True, text=True)
    if r.returncode and "1050" not in r.stderr:  # ignore "table exists"
        print(r.stderr.strip())
    return r.stdout.strip()


def find(folder: Path, animal: str, kind: str, ext: str):
    hits = glob.glob(str(folder / "**" / f"emg-eeg-{animal}-{kind}.{ext}"), recursive=True)
    return Path(hits[0]) if hits else None


def install(folder: Path, animal: str, dbdir: Path, kind: str, table: str, templ_frm: Path):
    myd = find(folder, animal, kind, "MYD")
    if not myd:
        print(f"  [skip] no {kind} .MYD for animal {animal}"); return False
    shutil.copy(myd, dbdir / f"{table}.MYD")
    frm = find(folder, animal, kind, "frm")
    shutil.copy(frm if frm else templ_frm, dbdir / f"{table}.frm")
    myi = find(folder, animal, kind, "MYI")
    if myi:
        shutil.copy(myi, dbdir / f"{table}.MYI")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--animal", required=True)
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()
    folder = Path(args.dir).expanduser()
    db = f"emg_eeg_{args.animal}"
    dbdir = DATADIR / db

    if sql("SELECT 1") != "1":
        sys.exit("MariaDB not reachable on the socket — start it first "
                 "(see the Animal-9 setup / SETUP.md).")

    sql(f"CREATE DATABASE IF NOT EXISTS {db};")
    dbdir.mkdir(exist_ok=True)
    print(f"[load] animal {args.animal} -> database {db}")

    ok_d = install(folder, args.animal, dbdir, "data", "channel_data", TEMPL / "emg-eeg-9-data.frm")
    ok_l = install(folder, args.animal, dbdir, "log", "log_data", TEMPL / "emg-eeg-9-log.frm")
    if not ok_d:
        sys.exit("no data table found — check --dir and file names")

    sql("FLUSH TABLES;")
    for tbl, ok in [("channel_data", ok_d), ("log_data", ok_l)]:
        if ok:
            sql(f"REPAIR TABLE {tbl} USE_FRM;", db)
    n = sql("SELECT COUNT(*) FROM channel_data WHERE fragment=1;", db)
    print(f"[load] channel_data: {n} ERP (frag1) trials")
    if ok_l:
        n15 = sql("SELECT COUNT(*) FROM log_data WHERE type=15;", db)
        print(f"[load] log_data: {n15} type-15 annotations")

    dsn = f"mysql+pymysql://root@localhost/{db}?unix_socket={SOCK}"
    print(f"\n[load] DONE. Convert with:\n"
          f"  python scripts/convert.py --dsn \"{dsn}\" "
          f"--animal {args.animal} --out data/processed/animal{args.animal}.zarr --config config.yaml")


if __name__ == "__main__":
    main()
