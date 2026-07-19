"""Scan animal LOG files to determine up- vs down-conditioning (no big data needed).

Each `emg-eeg-N-log.MYD` is tiny (~300 KB) and contains the type-15 experimenter
annotations — including the "Start HRdown" / "Start HRup" marker that tells us the
conditioning DIRECTION. So we can triage every animal from logs alone, then only
download the 2.3 GB data files for the ones we actually want (need >=1 up-cond).

Drop the downloaded `*-log.MYD` files (and `-log.frm`/`-log.MYI` if you have them)
in one folder and run:
    python scripts/scan_animals.py --dir ~/Downloads/hroc-logs

Uses the running MariaDB (socket /tmp/hroc_mysql.sock) and, for any animal missing
its own log.frm, the authoritative Animal-9 log schema as a template.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

SOCK = "/tmp/hroc_mysql.sock"
DB = "emg_eeg_9"
DATADIR = Path("/Users/suchithrao/Downloads/hroc-training/.mariadb_data") / DB
TEMPLATE_FRM = Path("/Users/suchithrao/Downloads/ani-emg-eeg-9-full/ani-emg-eeg-9/emg-eeg-9-log.frm")

UP = re.compile(r"\bHR\s*up\b|start\s*hrup|up-?cond", re.I)
DOWN = re.compile(r"\bHR\s*down\b|start\s*hrdown|down-?cond", re.I)


def sql(q, db=DB):
    r = subprocess.run(["mariadb", "--no-defaults", "-uroot", f"--socket={SOCK}", db,
                        "-N", "-e", q], capture_output=True, text=True)
    return r.stdout.strip()


def scan_one(myd: Path, template_frm: Path):
    m = re.search(r"emg-eeg-(\d+i?)-log", myd.name)
    if not m:
        return None
    animal = m.group(1)
    tbl = f"scan_{animal}".replace("i", "_i")
    # place files in the datadir
    shutil.copy(myd, DATADIR / f"{tbl}.MYD")
    own_frm = myd.with_name(myd.name.replace(".MYD", ".frm"))
    shutil.copy(own_frm if own_frm.exists() else template_frm, DATADIR / f"{tbl}.frm")
    own_myi = myd.with_name(myd.name.replace(".MYD", ".MYI"))
    if own_myi.exists():
        shutil.copy(own_myi, DATADIR / f"{tbl}.MYI")
    sql("FLUSH TABLES;")
    sql(f"REPAIR TABLE {tbl} USE_FRM;")
    rows = sql(f"SELECT time, text FROM {tbl} WHERE type=15 ORDER BY time")
    up_t = down_t = None
    first_txt = ""
    for line in rows.splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        t, txt = int(parts[0]), parts[1]
        if not first_txt:
            first_txt = txt[:60]
        if DOWN.search(txt) and down_t is None:
            down_t = t
        if UP.search(txt) and up_t is None:
            up_t = t
    if up_t and not down_t:
        direction = "UP"
    elif down_t and not up_t:
        direction = "DOWN"
    elif up_t and down_t:
        direction = "BOTH?" + (" up-first" if up_t < down_t else " down-first")
    else:
        direction = "unclear"
    n15 = sql(f"SELECT COUNT(*) FROM {tbl} WHERE type=15")
    return animal, direction, n15, first_txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="folder holding the downloaded *-log.MYD files")
    ap.add_argument("--template-frm", default=str(TEMPLATE_FRM))
    args = ap.parse_args()

    logs = sorted(Path(args.dir).expanduser().glob("*-log.MYD"))
    if not logs:
        print(f"no *-log.MYD files in {args.dir}"); return
    template = Path(args.template_frm)
    print(f"scanning {len(logs)} logs...\n")
    print(f"{'animal':8s} {'direction':14s} {'#type15':>8s}  first-note")
    print("-" * 78)
    rows = []
    for myd in logs:
        res = scan_one(myd, template)
        if res:
            a, d, n, txt = res
            rows.append(res)
            print(f"{a:8s} {d:14s} {n:>8s}  {txt}")
    ups = [r[0] for r in rows if r[1] == "UP"]
    downs = [r[0] for r in rows if r[1] == "DOWN"]
    print("\nSUMMARY")
    print(f"  UP-conditioned   : {ups or '(none found — need at least one!)'}")
    print(f"  DOWN-conditioned : {downs}")
    print("\nNext: download the big -data.{MYD,MYI,frm} files for 1 UP + 1-2 DOWN.")


if __name__ == "__main__":
    main()
