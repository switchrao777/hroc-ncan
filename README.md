# HROC — Cortical Correlates of H-Reflex Operant Conditioning

NCAN / Wolpaw-lab project. Decodes the 2006 Elizan III paired EMG+ECoG recordings
at scale, quantifies operant H-reflex conditioning with proper stimulus control,
and tests whether cortical activity changes as the spinal cord learns.

**Status (Aug 2026):** six animals processed (~2.7M trials), all controls built.

---

## Findings

| finding | status |
|---|---|
| **Conditioning works in both directions** | **Solid.** Up-conditioned animals' corrected H rises, down-conditioned falls (group difference +72 pts). Animals 9, 11 (down) and 3 (up) clear the lab's 20% criterion, with M-wave and pre-stimulus background regressed out. |
| **Cortex predicts the reflex trial-by-trial** | **Real.** Cross-validated *within* 5-day blocks (so slow drift cancels): R² up to 0.35 against a ~0 shuffle null, present in every animal. Not stimulus intensity, muscle tone, or drift. |
| Average-state cortical drift = learning? | **Answered: no.** Three independent controls agree it is recording nonstationarity — sham null fails in 5/6 animals, randomised-order null ≈ 0, and no up-vs-down direction dependence (t = −1.01). |

Open: whether the coupling *changes* with conditioning (t = 0.69, n = 5 — a power
problem), and an EMG→ECoG crosstalk test for the post-stimulus coupling.

Key documents: [REAL_RESULTS.md](REAL_RESULTS.md) ·
[ANIMAL_ROSTER.md](ANIMAL_ROSTER.md) · [NEXT_TWO_WEEKS.md](NEXT_TWO_WEEKS.md) ·
slides in [`slides/`](slides/).

---

## Signal facts (confirmed empirically — some correct the lab docs)

- **Little-endian** int16. `decoder_2006.py`'s "big-endian" docstring is wrong for
  these files (big-endian decodes to noise).
- Block channel layout: **ch0 = SOLR soleus EMG, ch1 = ECoG**. `ad2uV = 2.441406`.
- Fragments per trial: **frag0** = 1000 samples @ 1 kHz (1 s pre-stimulus),
  **frag1** = 150 samples @ 5 kHz (the M/H response), **frag2** = late.
- **M-wave 2–4 ms, H-reflex 6–9 ms** — from the experimenters' own type-15 log
  entries, not the 8–10 ms the pipeline originally assumed.
- Never use raw H amplitude: it scales with stimulus. Use H/M, or better, compare H
  within matched M bins, always after background subtraction.

---

## Pipeline

```bash
pip install -r requirements.txt

# 1. load one animal's MyISAM tables into a local MariaDB
python scripts/load_animal.py --animal 9 --dir ~/Downloads/ani-emg-eeg-9

# 2. convert -> Zarr, timestamps, QC, confound control, drift (one command)
python scripts/run_animal.py --animal 9

# 3. covariates Dr Carp asked for
python scripts/add_prestim.py       --dsn "<dsn>" --zarr data/processed/animal9.zarr
python scripts/add_prestim_bands.py --dsn "<dsn>" --zarr data/processed/animal9.zarr

# 4. pooled encoder across animals, then the analyses
python scripts/train_pooled.py      --zarrs data/processed/animal*.zarr
python scripts/final_analysis.py    --ckpt outputs/encoder_pooled.pt --zarrs ...
python scripts/coupling_analysis.py --ckpt outputs/encoder_pooled.pt --zarrs ...
python scripts/updown_contrast.py   --ckpt outputs/encoder_pooled.pt --zarrs ...
python scripts/prestim_coupling.py  --zarrs ...
```

`scripts/scan_animals.py` reads the tiny log files alone to classify an animal's
conditioning direction (and, via the reward criterion, its strength) *before*
downloading gigabytes of signal.

---

## Controls implemented

1. **M-wave** — stimulus efficacy, regressed out of every measure.
2. **Pre-stimulus background** — motoneuron-pool excitability, 20 ms before the
   stimulus, from frag0.
3. **Baseline sham null** — split baseline-only data as a fake experiment.
4. **Randomised trial-order null** — breaks real time structure, keeps the numbers.
5. **Last-10-days baseline** — early baseline had settings changes.
6. **Within-block cross-validation** — makes the coupling result drift-immune.
7. **Up-vs-down direction contrast** — recording drift is direction-independent.

---

## Zarr schema (per animal)

```
animalN.zarr/
  ecog              (N, 150)  float32   cortical window — model input
  emg               (N, 150)  float32   soleus EMG — label source
  hreflex           (N,)      float32   mean rectified amplitude, matched window
  phase             (N,)      int64     0 = baseline, 1 = conditioning
  time              (N,)      int64     unix seconds
  day               (N,)      int64     day index (drift-per-day)
  prestim_emg       (N,)      float32   pre-stimulus background
  prestim_bands     (N, 6)    float32   pre-stimulus cortical log band power
  prestim_emg_bands (N, 6)    float32   same for EMG (crosstalk control)
  attrs: direction ("up"/"down"), animal
```

Raw `.MYD`/`.MYI`/`.frm`, Zarr stores, and the local MariaDB datadir are
gitignored — never commit data.

---

## Repo map

```
scripts/    load_animal, convert, run_animal, add_timestamps, add_prestim,
            add_prestim_bands, scan_animals, reflex_measures, confound_control,
            drift_over_time, final_analysis, coupling_analysis, prestim_coupling,
            updown_contrast, train_pooled, validate_zarr, inspect_db
src/        config, seed, data loaders, preprocessing, models (conv_ae + brainbert),
            two-phase trainers, latent/UMAP + neuro figure analysis
slides/     decks and talk scripts for the Carp meetings
outputs/    figures, per-animal results, verdicts
decoders/   original lab decoders (2006 / 2013) — see signal facts above
```
