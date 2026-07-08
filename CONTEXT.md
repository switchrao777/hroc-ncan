# HROC Project — Context Pack

Condensed reference pulled from the NIH prep chats. For the slides tomorrow and
for onboarding Tarun. This is background; the README is the how-to.

## One-line
NIH-funded Wolpaw-lab (NCAN, Wadsworth Center) project asking whether the
**cortex changes as the spinal cord learns** to control the H-reflex — via an
autoencoder over rat ECoG across six conditioning phases. Supervisor: Dr.
Jonathan Carp. Technical advisor: Chadwick Boulay (CB Neurotech, original
pipeline author). Attends weekly: Theresa Vaughan.

## The six conditioning phases (temporal order)
Baseline → Down-cond 1 → Up-cond 1 → Freely Running → Down-cond 2 → Up-cond 2

## Signal / format facts (reverse-engineered)
| item | value |
|---|---|
| ad2uV conversion | 2.441406 |
| ERP-window sample rate | 5,000 Hz |
| window length — Animal 9 (2006 fmt) | 150 samples = 30 ms |
| window length — Animals 16/17 (2013 fmt) | 250 samples = 50 ms |
| M-wave latency | 2–4 ms (direct motor) |
| H-reflex latency | 8–10 ms (spinal reflex) |
| SOLR (soleus) peak | ~430 µV |
| QDR (quadriceps) peak | ~110 µV |
| channel storage | **block** order: chan1{samp1..N} chan2{samp1..N} |
| trials, Animals 16/17 | ~923,000 across 6 phases |
| trials, Animal 9 | ~95,450 (first paired EMG + ECoG, same animal) |

- 2013 format (Animals 16/17): little-endian, 1444-byte records, 3 frags,
  frag1 = 250 samples @ 5 kHz. Fully decoded.
- 2006 format (Animal 9): big-endian, 8536-byte records, 1 frag, 150 samples
  @ 5 kHz. Known bug: baseline subtraction needs frag0 from the *preceding*
  record (not yet fixed).
- Animal 9: Ch1 = SOLR EMG, Ch2 = ECoG cortical surface.

## Decisions from Dr. Carp (2026-07-01)
- **H-reflex label = mean rectified amplitude** in a matched window that
  encompasses the H-reflex. NOT peak-to-peak (single peak corrupted by ongoing
  background). Baseline-correct → rectify → average over the window.
- Window must be **matched** across all trials and phases.
- **Set the window from the trial-averaged waveform** (the grand-average H-reflex
  bump, ~8-10 ms). Implemented in `src/data/hreflex_label.py`; config bounds in
  `signal.hreflex_window_ms`. `suggest_window_from_average()` recovered 8.2-9.8 ms
  from the synthetic average, confirming the method.

## Chad's recommendations (the plan this pipeline implements)
- Load MySQL via **SQLAlchemy**, convert to **Zarr** for fast cloud training.
- Train from cloud (AWS/GCP/Azure) — local GPU too slow.
- **Two-phase autoencoder:** Phase 1 unsupervised reconstruction on all data
  (incl. intermittent `i` trials, no H-reflex needed); Phase 2 freeze encoder,
  MLP head predicts H-reflex amplitude.
- Visualize latent with **UMAP/t-SNE**, color by phase, track centroid over time.
- Consider **BrainBERT** (arxiv 2302.14367, github.com/czlwang/BrainBERT) — a
  pretrained, channel-count-agnostic ECoG encoder from human epilepsy sEEG.
- The 34 ms ECoG artifact is likely a high-pass filter discontinuity at a
  sampling gap — not biological.

## People
- **Dr. Jonathan Carp** — supervisor (carp@neurotechcenter.org)
- **Chadwick Boulay** — technical advisor, CB Neurotech (chad@cbneurotech.com)
- **Theresa Vaughan** — NCAN admin director, 25 yrs BCI, weekly meetings
- **Suchith** — binary decoding, pipeline, ML lead (GitHub switchrao777)
- **Tarun** — intern, CE sophomore (GitHub tarunsenthil123, branch tarun-dev)

## Repos
- Main: `github.com/switchrao777/hroc-ncan` (private) — decoders, pipeline,
  SQLAlchemy stub, autoencoder starter notebook.
- This package (`hroc-training/`) — the full training machine to fold into it.

## CONFIRMED Drive catalog (ani-emg-eeg data, browsed 2026-07-08)
Folder "ani-emg-eeg data" = the paired EMG+ECoG set. Each animal is a MyISAM
MySQL DB: `emg-eeg-N-data.MYD` (the trials, GBs) + `.MYI` + `.frm`, plus a
`emg-eeg-N-log.MYD` (holds the type-15 phase annotations).

Conditioned animals: 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15  (no 5)
Intermittent (i, for Phase-1 unsupervised): 7i, 8i, 9i, 10i, 11i, 12i, 13i, 14i, 15i

ALL file dates are 2006 -> all are the 2006 big-endian / 150-sample format, same
as Animal 9. One decoder path (decoder_2006.py) covers the whole set; no
per-format branching needed. (Animals 16/17 = 2013/250-sample are a SEPARATE
array-data folder, not in this set.)

Per-animal data.MYD sizes are ~2.4-3.7 GB (9: 2.44 GB, 11: 3.23 GB, 14: 3.68 GB,
15: 3.40 GB). Full set raw ≈ 45-70 GB. Decoded Zarr (ERP windows only) is far
smaller. Implication for Carp's storage q: raw is tens of GB (keep on the
lab/cloud machine that runs MySQL), but the trained-on Zarr is small.

IMPORTANT: this data lives in Drive and needs MySQL + the decoder. The training
sandbox in these chats CANNOT reach Drive or run MySQL, so real conversion +
training runs on Tarun's machine / a cloud VM that mounts the Drive, not in-chat.

## Data on Google Drive (priority order)
1. `ani-emg-eeg data/` — paired EMG+ECoG same animal (HIGHEST). `-9` decoded,
   `-9i` intermittent (autoencoder training), `-10`/`-10i` not yet decoded.
2. `array data/` — 32-channel Blackrock ECoG array.
3. `ani-ap data/` — Chad's older combined experiments.
4. `Alessandro's data/` — EMG only, lower priority.

## Status snapshot
Done: both binary formats decoded, EMG validated (correct M-wave/H-reflex
timing + amplitude ratios), 25-feature classical pipeline (PCA/KMeans/Isolation
Forest), and now the **full two-phase training machine validated on synthetic
data (R²=0.90 frozen-encoder, phases separate in UMAP)**.

Not done: SQLAlchemy→Zarr converter, Animal 9 baseline-subtraction fix, Animal 9
phase labels, real-data training run, ani-emg-eeg-10.
