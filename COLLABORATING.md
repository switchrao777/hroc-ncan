# Collaborating on GitHub (Suchith + Tarun)

Short version: **code goes on GitHub, data never does.**

## What goes where
- **GitHub:** all the code in this repo (`src/`, `scripts/`, configs, docs).
- **NOT GitHub:** the raw `.MYD` files (~50 GB) and the `.zarr` stores. These are
  large and are research data. `.gitignore` already blocks `data/`, `*.MYD`,
  `*.zarr/`, and checkpoints. Keep raw data on the SSD, share the small Zarrs via
  the shared Google Drive folder.
- **Model checkpoints** (`outputs/*.pt`): also kept out of git. Share via Drive if
  needed, or re-train (it's fast).

## First push (Suchith, once)
```bash
cd hroc-training
git init
git add .
git commit -m "HROC training pipeline: two-phase AE, multi-animal, converter"
git branch -M main
git remote add origin <your-repo-url>.git
git push -u origin main
```

## Day-to-day (both)
Work on branches, merge with pull requests so nothing clobbers:
```bash
git checkout -b tarun-converter        # or suchith-analysis, etc.
# ...make changes...
git add -p && git commit -m "what changed"
git push -u origin tarun-converter
# open a PR on GitHub, review, merge into main
```
Pull main before starting each session: `git checkout main && git pull`.

## Suggested branch split for now
- `suchith-*`: phase-label recovery, baseline fix, analysis.
- `tarun-*`: the converter HOOKs (`scripts/convert.py`), per-animal runs.
Keeps you out of each other's files while both moving.
