# Setup

Getting the HROC recordings decoded and a model trained, from a clean machine.

Nothing here needs a cluster. The models are small and train on an Apple-Silicon
Mac (MPS) or any GPU in minutes. The heavy step is decoding the raw MySQL
archives, which is done once per animal.

---

## Hardware

- **Raw archives (~4 GB per animal):** keep them on an external SSD if internal
  space is tight. The MySQL data directory and the `.MYD` files live together.
- **Decode once per animal.** Output is a Zarr store of a few hundred MB.
- Once converted, the raw archives are no longer needed for analysis.

## Software

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
brew install mariadb          # or any MySQL-compatible server
```

Start a local server on its own data directory so it does not disturb an existing
MySQL install:

```bash
mariadb-install-db --no-defaults --datadir=.mariadb_data
mariadbd --no-defaults --datadir=.mariadb_data --socket=/tmp/hroc_mysql.sock --port=3307 &
```

---

## Per animal

Each animal needs six files from the archive: `emg-eeg-N-data.{MYD,MYI,frm}` and
`emg-eeg-N-log.{MYD,MYI,frm}`. A missing `.MYI` can be rebuilt; a missing `.frm`
can be substituted from another animal, since the schema is shared.

```bash
# 1. load the MyISAM tables into the local server
python scripts/load_animal.py --animal 9 --dir /path/to/ani-emg-eeg-9

# 2. convert, add timestamps, validate, and run the standard analyses
python scripts/run_animal.py --animal 9

# 3. add the pre-stimulus covariates
DSN="mysql+pymysql://root@localhost/emg_eeg_9?unix_socket=/tmp/hroc_mysql.sock"
python scripts/add_prestim.py       --dsn "$DSN" --zarr data/processed/animal9.zarr
python scripts/add_prestim_bands.py --dsn "$DSN" --zarr data/processed/animal9.zarr
```

**Check before trusting the output.** `outputs/animal9/validate/avg_emg.png` should
show a stimulus artifact followed by an M-wave near 2–4 ms and an H-reflex near
6–9 ms. If it looks like noise, the decode is wrong and nothing downstream is
meaningful.

### Choosing which animals to convert

The log files are small and can be read without downloading the signal data.
`scripts/scan_animals.py` reads them to report each animal's conditioning
direction, and the reward-criterion trajectory indicates whether the animal
actually learned:

```bash
python scripts/scan_animals.py --dir /path/to/logs
```

---

## Across animals

```bash
Z="data/processed/animal9.zarr data/processed/animal10.zarr ..."

python scripts/train_pooled.py      --zarrs $Z                                # shared encoder
python scripts/final_analysis.py    --ckpt outputs/encoder_pooled.pt --zarrs $Z
python scripts/coupling_analysis.py --ckpt outputs/encoder_pooled.pt --zarrs $Z
python scripts/verify_coupling.py   --ckpt outputs/encoder_pooled.pt --zarrs $Z
python scripts/scaling_analysis.py  --ckpt outputs/encoder_pooled.pt --zarrs $Z
python scripts/updown_contrast.py   --ckpt outputs/encoder_pooled.pt --zarrs $Z
```

Figures and per-animal summaries are written under `outputs/`.

---

## Notes on the archive format

- Samples are **little-endian** 16-bit integers, despite the archived decoder
  documenting them as big-endian. Decoding as documented produces noise.
- Channel layout is block, not interleaved: the first half of each fragment is
  soleus EMG, the second half is cortical ECoG.
- Conversion factor is 2.441406 µV per unit, confirmed by the type-5 log entry.
- Fragment 1 carries the response window used throughout: 150 samples at 5 kHz.
  Fragment 0 is one second of pre-stimulus signal at 1 kHz.
