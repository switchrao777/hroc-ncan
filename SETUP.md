# SETUP — run this project with Claude Code (local Mac/PC + external SSD)

This is the runbook for getting real HROC data trained. It's written to be handed
to **Claude Code** on the machine that has the data. Claude Code should follow it
top to bottom and STOP at each checkpoint to show the human output before going on.

No cloud needed. The models are small and train fine on an Apple-Silicon Mac
(MPS) or any GPU. The only heavy part is decoding ~50 GB of raw MySQL data, which
is done ONCE, ideally on an external SSD.

---

## The hardware plan (cheapest that works)

- **Raw data (~50 GB):** download from Drive onto a fast external SSD (USB-C /
  Thunderbolt NVMe). Keep it off the laptop's internal disk. The MySQL data
  directory and the raw `.MYD` files live here.
- **Decode once:** run MySQL + the converter (Steps 2-4) on whichever machine has
  the SSD attached. Output = small Zarr files (a few GB total).
- **Share the small stuff:** put the Zarr files in the shared Google Drive folder.
  Both people pull the Zarrs and train locally. Nobody moves 50 GB again.
- **Train:** on either M-series Mac (uses the Mac GPU via MPS automatically) or the
  Windows/NVIDIA box.

---

## Step 0 — environment (once per machine)

```bash
python -m venv .venv && source .venv/bin/activate    # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
python scripts/run_all.py --config config.smoke.yaml  # synthetic; confirms install + GPU
```
The smoke test should finish in ~1-2 min and write figures to `outputs/`. If it
does, the pipeline works on this machine. (`config.smoke.yaml` uses fake data;
`config.yaml` is for the real Zarrs.)

**CHECKPOINT 0 — show the human:** "synthetic smoke test passed, device = <mps/cuda/cpu>".

---

## Step 1 — get one animal's data onto the SSD

Download from the Drive `ani-emg-eeg data` folder into `/<SSD>/hroc_raw/animal9/`:
`emg-eeg-9-data.MYD`, `.MYI`, `.frm`, and the three `emg-eeg-9-log.*` files.
Start with **Animal 9 only** — don't download all 14 yet.

---

## Step 2 — load into MySQL and decode ONE trial (the critical gate)

1. Install MariaDB/MySQL. Create a db `emg_eeg_9`. Drop-in the MyISAM files:
   copy the 6 files into the server's data dir under `emg_eeg_9/`, then
   `FLUSH TABLES;`. (Claude Code: if drop-in is fiddly, use `mysqlimport` or a
   MyISAM reader — whatever gets the tables queryable.)
2. Inspect + decode one trial:
   ```bash
   python scripts/inspect_db.py --dsn mysql+pymysql://root@localhost/emg_eeg_9
   ```
3. Claude Code: use the printed schema to complete the 3 HOOKs in
   `scripts/convert.py` (`fetch_one_raw`, `decode_trial`, `iter_raw_trials`),
   importing the lab's real `decoder_2006.py` if present in the `hroc-ncan` repo.
   Verify the reference decode against the real one on this single trial.

**CHECKPOINT 2 — STOP. Show the human `outputs/inspect/decoded_trial.png`.** The
EMG trace must show the M-wave (~2-4 ms) and H-reflex (~8-10 ms) bumps. If it's
noise, the decode is wrong — do NOT mass-convert. Also confirm with the human
whether the baseline-subtraction (frag0 from the preceding record) is handled.

---

## Step 3 — recover phase labels from the log table

Complete `parse_phases()` in `convert.py`: parse the type-15 annotations in
`emg-eeg-9-log`, derive the 6 phase boundaries, assign each trial by timestamp.

**CHECKPOINT 3 — STOP. Show the human the per-phase trial counts and the boundary
timestamps.** Phase recovery is unresolved and scientifically important — the
human (Suchith/Carp) must confirm before continuing.

---

## Step 4 — convert Animal 9 and validate

```bash
python scripts/convert.py --dsn mysql+pymysql://root@localhost/emg_eeg_9 \
    --animal 9 --out /<SSD>/hroc_zarr/animal9.zarr --config config.yaml
python scripts/validate_zarr.py --zarr /<SSD>/hroc_zarr/animal9.zarr
```

**CHECKPOINT 4 — show the human** the validation report (trial counts, NaN check,
label distribution, averaged-EMG bump check).

---

## Step 5 — set the H-reflex window from the REAL average, then train

1. Run `suggest_window_from_average` on the real EMG, set `signal.hreflex_window_ms`
   in `config.yaml`.
2. Point `data.animals` at `animal9.zarr`, then:
   ```bash
   python scripts/run_all.py --config config.yaml
   ```

**CHECKPOINT 5 — STOP. Show the human** the Phase-2 R² and the figures:
`hreflex_by_phase`, `umap_by_phase`, `centroid_drift`, `cortex_vs_behavior`.
This is the first real result. Human decides if it's good before scaling up.

---

## Step 6 — scale to all animals (only after Step 5 is approved)

Repeat Steps 1-4 per animal (6, 10, 11, 12, 13, 14, 15, ...), copy each Zarr to
shared Drive, add it to `data.animals`, and re-run. Watch the **batch-effect
check** in the analysis output — if animal identity dominates phase, turn on
per-animal normalization before trusting the pooled drift.

**Human-in-the-loop rule:** Checkpoints 2, 3, and 5 always stop for a human. The
rest Claude Code can run on its own.
