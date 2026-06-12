# HROC Neural Data Pipeline
**NCAN / Wolpaw Lab, Wadsworth Center — NIH-funded**  
Suchith Rao · NIH ML Engineer · Under Dr. Jonathan Carp

---

## What this project is

Rats can learn to control their own spinal H-reflex through operant conditioning — a process called **H-Reflex Operant Conditioning (HROC)**. We've known for 30+ years that the spinal cord physically changes during this process. But nobody has ever published what the **brain** is doing at the same time.

This project's goal: **be the first to identify cortical correlates of spinal reflex conditioning** by analyzing simultaneous EMG (muscle) and ECoG (brain surface) recordings from the same rat.

The data exists. It's stored in 20-year-old legacy binary files from a system called **Elizan III** — a MySQL-based acquisition system with no documentation and no existing Python tooling. Everything in this repo was built from scratch.

---

## What has been done so far (Suchith)

### 1. Binary format reverse-engineering
Two completely different undocumented binary formats were cracked via hex inspection:

| | 2013 Format (Animals 16/17) | 2006 Format (Animal 9) |
|---|---|---|
| Encoding | int16, little-endian | int16, **big-endian** |
| Record size | 1,444 bytes | 8,536 bytes |
| Fragments/record | 3 | 1 |
| ERP window | frag1: 250 samples @ 5kHz | frag1: 150 samples @ 5kHz |
| Channels | Block layout: ch1 = first half, ch2 = second half | Same |
| ad2uV factor | 2.441406 | 2.441406 |

### 2. EMG signal validation (Animals 6, 16, 17)
- Ch1 = SOLR (soleus): ~430µV peak
- Ch2 = QDR (quadriceps): ~110µV peak  
- M-wave confirmed at 2–4ms post-stimulus
- H-reflex confirmed at 8–10ms (correct spinal latency)
- 4× amplitude ratio matches Wolpaw lab literature
- All **6 conditioning phase labels** recovered from type-15 log annotations
- ~923,000 trials decoded, Jul 2013 – Jan 2014

**Conditioning phases:**
```
Baseline → Down-Conditioning 1 → Up-Conditioning 1 → Freely Running → Down-Conditioning 2 → Up-Conditioning 2
```
Animal 17 (up): H-reflex → 135% baseline | Animal 16 (down): H-reflex → 28.5% baseline

### 3. ML pipeline (`hroc_full_pipeline.py`)
Full end-to-end pipeline built on the decoded data:
- Binary decoder → 25-feature extraction → PCA → KMeans (silhouette-scored) → Hierarchical clustering → Isolation Forest anomaly detection
- Outputs: 7 figures, 3 CSVs (trial-level, phase-summary, anomalies)

### 4. ECoG decoding
- **Animal 12** (unpaired): array_12new/channel_030.MYD — zlib-compressed blocks, 78,960 trials, ~2µV peak-to-peak, time-locked cortical response confirmed. ~34ms drop = reward delivery artifact (Elizan §4.8.5).
- **Animal 9** (paired — first real data): Ch1 = SOLR EMG, Ch2 = ECoG cortical surface — same animal, same session. ~95,450 trials, ECoG confirmed real at ±300µV. Format fully reverse-engineered.

**Known bug:** Animal 9 baseline subtraction is off — fix requires reading frag0 from the *preceding* record (format difference from 2013).

---

## What Tarun is here to build

Based on a conversation with **Chadwick Boulay** (CB Neurotech, former Wolpaw Lab PhD), the next phase of the project is:

### Phase A — Data pipeline upgrade
1. Load the MySQL `.MYD` files using **SQLAlchemy** (ORM-based, cleaner than raw binary for new animals)
2. Convert all trial data to **Zarr or Parquet** format — fast columnar storage for cloud-based model training
3. Each trial needs: raw neural signal + H-reflex amplitude label + M-wave amplitude label + phase label

### Phase B — Autoencoder
Chad's recommendation:
> "Train a deep model to encode the ECoG signal into a latent space, then attach a multi-layer perceptron decoder on top that predicts H-reflex magnitude."

Two-phase training:
1. **Phase 1 — Autoencoder:** Input ECoG signal → encode to latent space → decode back to ECoG. Loss = reconstruction error. Use ALL data including intermittent ("i") trials.
2. **Phase 2 — MLP decoder:** Freeze encoder, attach MLP head, predict H-reflex amplitude from latent representation. Use only stimulus trials with known H-reflex labels.

Goal: Show that the latent space shifts over the conditioning timeline — i.e., the brain is changing as the spinal cord is conditioned. That's the novel result.

### Visualization
- UMAP or t-SNE on latent space colored by conditioning phase
- Track latent space centroid over time across the 6 phases

---

## Repo structure

```
hroc-ncan/
├── decoders/
│   ├── decoder_2013.py        # Animal 16/17 format (little-endian, 3 frags/record)
│   ├── decoder_2006.py        # Animal 9 format (big-endian, 1 frag/record)
│   └── utils.py               # Shared: ad2uV conversion, channel split, phase label parsing
├── pipeline/
│   ├── hroc_full_pipeline.py  # Full ML pipeline (25 features, PCA, KMeans, Isolation Forest)
│   └── feature_extraction.py  # 25-feature extractor (amplitude, temporal, baseline, spectral, shape)
├── data/
│   ├── raw/                   # .MYD files go here (not committed — too large)
│   └── processed/             # Zarr/Parquet outputs go here
├── notebooks/
│   ├── 01_decode_animal9.ipynb
│   ├── 02_emg_validation.ipynb
│   ├── 03_ecog_validation.ipynb
│   └── 04_autoencoder_starter.ipynb   ← Tarun starts here
├── utils/
│   └── sqlalchemy_loader.py   # SQLAlchemy ORM for loading from MySQL (in progress)
├── docs/
│   ├── FORMAT_2013.md         # Full 2013 binary format spec (reverse-engineered)
│   ├── FORMAT_2006.md         # Full 2006 binary format spec (reverse-engineered)
│   └── CHAD_MEETING_NOTES.md  # Key decisions from Chadwick Boulay coffee chat
└── README.md
```

---

## Setup

```bash
git clone <repo-url>
cd hroc-ncan
pip install -r requirements.txt
```

**requirements.txt:**
```
numpy
pandas
scipy
matplotlib
scikit-learn
sqlalchemy
pymysql
zarr
umap-learn
torch
jupyter
```

---

## Key numbers to know

| Parameter | Value |
|---|---|
| ad2uV conversion | 2.441406 |
| Sample rate (ERP window) | 5,000 Hz |
| ERP window length (2013) | 250 samples = 50ms |
| ERP window length (2006) | 150 samples = 30ms |
| M-wave latency | 2–4ms |
| H-reflex latency | 8–10ms |
| SOLR peak amplitude | ~430µV |
| QDR peak amplitude | ~110µV |
| Total trials (Animal 16/17) | ~923,000 |
| Total trials (Animal 9) | ~95,450 |

---

## Data files (Google Drive)

```
ani-emg-eeg data/       ← HIGHEST PRIORITY — paired EMG+ECoG same animal
  ani-emg-eeg-9/        ← decoded ✅
  ani-emg-eeg-9i/       ← intermittent data (no stimulus) — use for autoencoder training
  ani-emg-eeg-10/       ← not yet decoded
  ani-emg-eeg-10i/
  ...
array data/             ← 32-channel Blackrock ECoG array
ani-ap data/            ← Chad's older combined experiments
Alessandro's data/      ← EMG only, lower priority
```

Raw `.MYD` files are **not committed to git** — they're large and on Google Drive. Ask Suchith for access.

---

## Papers to read

1. **Chadwick Boulay's dissertation** — the foundational analysis this project extends. Has the MATLAB code logic and the frequency band correlations (alpha, beta, low gamma, high gamma vs H-reflex magnitude).
2. **The published ECOG-H-reflex correlation paper** (Wolpaw lab) — what's already been shown.
3. **Boulay's neurofoundation model paper** — the architecture Chad recommended for the autoencoder (links in `docs/CHAD_MEETING_NOTES.md`).

---

## Contact

- **Suchith Rao** — rsuchith2@gmail.com — project lead, pipeline architecture
- **Dr. Jonathan Carp** — supervisor, Wolpaw Lab
- **Chadwick Boulay** — CB Neurotech — technical advisor (autoencoder direction)
