# Chad Boulay Meeting Notes
**Date:** June 5, 2026  
**Attendees:** Suchith Rao, Chadwick Boulay (CB Neurotech, former Wolpaw Lab PhD)

---

## Key decisions

### Architecture: Autoencoder + MLP decoder
Chad's recommendation for the ML phase:

**Phase 1 — Autoencoder (unsupervised):**
- Input: raw ECoG signal (150 samples @ 5kHz)
- Architecture: multi-layer perceptron encoder
- Output: latent vector (32–64 dim) → reconstructed ECoG
- Loss: MSE reconstruction
- Use ALL data including intermittent ("i") trials — no H-reflex needed

**Phase 2 — MLP decoder (supervised):**
- Freeze the encoder
- Attach a new MLP head on top of the latent vector
- Predict H-reflex amplitude per trial
- Use only stimulus trials with known labels

### Data pipeline
- Load MySQL data using **SQLAlchemy** ORM
- Convert all trials to **Zarr or Parquet** format for fast cloud training
- Each trial record needs: raw neural signal + H-reflex amp + M-wave amp + phase label

### Visualization
- **UMAP or t-SNE** on latent space to visualize clustering
- Color by conditioning phase — if clusters separate = brain is tracking conditioning
- Track latent centroid over time across the 6 phases

---

## Key insights from Chad

- He already published the simple ECOG↔H-reflex correlation — the low hanging fruit is gone
- The novel angle is **tracking the latent space over the conditioning timeline** — does the brain change as the spinal cord is conditioned?
- The "i" (intermittent) data has no H-reflex but is still useful for autoencoder training
- Use as much data as possible across all ani-emg-eeg animals
- Run training on **AWS / Google Cloud / Azure** — local GPU is too slow
- **Zarr** is the right format for cloud-based neural data training

## On the 34ms ECoG artifact
Chad's hypothesis: the sharp drop at ~34ms is likely a **discontinuity artifact** from a high-pass filter encountering a gap in the sampling. If the Elizan system stitches together fragments with a small gap, the filter exaggerates the jump. Not biological.

## On the format difference (2006 vs 2013)
Chad believes there were Elizan III software updates AND animals had different recording setups (different numbers of channels). He couldn't confirm the specific format change details — this was reverse-engineered from hex inspection.

## On neurofoundation models
Chad mentioned a neurofoundation model paper (human ECoG, epilepsy monitoring data) that is channel-count-agnostic — could work for single/dual channel rat data. Links to be added.

---

## Action items
- [ ] Tarun: implement SQLAlchemy loader
- [ ] Tarun: convert data to Zarr
- [ ] Tarun: train Phase 1 autoencoder on Animal 9 ECoG
- [ ] Suchith: fix Animal 9 baseline subtraction bug
- [ ] Suchith: recover phase labels for Animal 9
- [ ] Both: expand to ani-emg-eeg-10 once Animal 9 pipeline is clean
