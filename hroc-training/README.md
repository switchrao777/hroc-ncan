# HROC Autoencoder Training Pipeline

The end-to-end model-training machine for the NCAN / Wolpaw-lab HROC project —
the two-phase autoencoder Chad recommended, built so it runs **today** on
synthetic data and needs **one config flag** to switch to the real Animal-9 Zarr
store.

Built by Suchith. Tarun: this doc is your starting point. Read it top to bottom,
run the smoke test, then pick up the "Your tasks" section.

---

## What this is (and what it isn't)

**Is:** the full training stack — data loading, both encoder paths, Phase 1
unsupervised pretraining, Phase 2 supervised H-reflex regression, and the
latent-space drift analysis that is the scientific point of the project.

**Isn't:** trained on real signals yet. The real `.MYD` / Zarr data lives on the
lab Google Drive and isn't in this repo. So the pipeline currently runs on
**synthetic Animal-9-like data** (see `src/data/synthetic.py`) that mimics the
decoded signal statistics — 150-sample 5 kHz windows, M-wave/H-reflex EMG bumps,
an ECoG channel driven by latent factors that drift across the six conditioning
phases. Every synthetic figure is watermarked `SYNTHETIC`. Nothing here is a
scientific result — it's proof the machine works, so plugging in real data is a
one-line change.

---

## The scientific bet (why any of this matters)

Does the **brain** change as the **spinal cord** learns to control the H-reflex?
Chad already published the simple ECoG↔H-reflex correlation — that juice is
squeezed. The novel angle: train an autoencoder on the cortical signal, then ask
whether its **latent space shifts across the six conditioning phases**
(Baseline → Down-cond 1 → Up-cond 1 → Freely Running → Down-cond 2 → Up-cond 2).
If it does, that's cortical correlates of HROC — never published.

The `centroid_drift.png` and `umap_by_phase.png` figures are exactly that test.

---

## Run it

```bash
pip install -r requirements.txt
python scripts/run_all.py --config config.yaml
```

That runs the whole thing on synthetic data (~1.5 min CPU) and drops everything
in `outputs/`:

| file | what |
|---|---|
| `encoder_phase1.pt` | pretrained encoder checkpoint |
| `hreflex_head.pt` | Phase-2 regression head |
| `phase1_loss.png` | reconstruction loss curve |
| `phase2_loss.png` | H-reflex regression MSE + R² curve |
| `umap_by_phase.png` | latent UMAP colored by conditioning phase |
| `centroid_drift.png` | latent centroid distance from Baseline per phase |
| `phase_separation.txt` | silhouette score + drift numbers |
| `run_summary.json` | full config + results |

### Synthetic validation results (current run)
- Phase 1 reconstruction MSE: 0.285 → **0.075**
- Phase 2 H-reflex regression (frozen encoder): **val R² = 0.90**
- Phases visibly separate in UMAP; down-cond vs up-cond land on opposite sides.

The R²=0.90 from a *frozen* encoder is the thing to internalize: it means the
unsupervised latent captured H-reflex-relevant structure without ever seeing a
label. That's the behavior we want to reproduce on real data.

---

## Architecture

Two interchangeable encoder paths (set `model.encoder` in `config.yaml`):

**`conv_ae`** — 1-D convolutional autoencoder, trained from scratch on waveform
reconstruction MSE. Fast, no external dependencies. Good default.

**`brainbert`** — a BrainBERT-style masked-spectrogram transformer
(Wang et al. 2023, arxiv 2302.14367). Takes the STFT of the window, masks random
time-frequency frames, reconstructs them. This is the **external / pretrained
path**: the architecture is ported faithfully so you can load the real BrainBERT
checkpoint via `BrainBERTEncoder.load_pretrained(path)` once the weights are
downloaded. BrainBERT is channel-count-agnostic, which is why it can transfer
from human sEEG to our rat ECoG.

**Two-phase training (both paths):**
1. **Phase 1 (unsupervised):** reconstruct the ECoG signal over ALL trials,
   including intermittent (`i`) trials with no H-reflex label. → frozen encoder.
2. **Phase 2 (supervised):** freeze the encoder, attach an MLP head, regress
   per-trial H-reflex amplitude. Report R² on held-out trials.

---

## Switching to real data (the one change that matters)

Once you've written the SQLAlchemy → Zarr converter, produce a store with this
layout:

```
animal9.zarr/
  ecog     (N, 150)  float32   # cortical channel — the AE input
  emg      (N, 150)  float32   # EMG channel (optional, validation)
  hreflex  (N,)      float32   # per-trial H-reflex amplitude label
  phase    (N,)      int64     # conditioning phase 0..5
```

Then in `config.yaml`:
```yaml
data:
  use_synthetic: false
  zarr_path: data/processed/animal9.zarr
```
Nothing else changes. `src/data/zarr_dataset.py` already reads that schema.

---

## Repo map

```
config.yaml                     all hyperparameters + data paths (edit here, not code)
scripts/run_all.py              end-to-end orchestrator
src/
  utils/config.py               typed config + the 6 PHASES definition
  utils/seed.py                 reproducibility
  data/synthetic.py             synthetic Animal-9-like generator
  data/preprocessing.py         z-scoring + STFT (for brainbert)
  data/zarr_dataset.py          Dataset + Zarr loader / synthetic fallback  <-- real-data hook
  models/autoencoder.py         conv_ae encoder+decoder
  models/brainbert.py           BrainBERT-style encoder (+ load_pretrained)  <-- external weights hook
  models/heads.py               Phase-2 MLP head + model factory
  train/phase1_pretrain.py      unsupervised pretraining
  train/phase2_finetune.py      frozen-encoder H-reflex regression
  train/trainer.py              checkpoint/logging helpers
  analysis/latent_umap.py       UMAP + centroid drift (the novel result)
```

---

## Your tasks, Tarun (in order)

1. **SQLAlchemy → Zarr converter.** The one missing piece. Read trials via the
   ORM stub (`utils/sqlalchemy_loader.py` in the main `hroc-ncan` repo), decode
   blobs with `decoder_2006.py`, and write the Zarr schema above. Start with
   Animal 9.
2. **Run on real Animal 9.** Flip `use_synthetic: false`, point at the store,
   run. See if the frozen-encoder R² and the phase drift survive on real signal.
3. **Try the `brainbert` path** and download the real pretrained checkpoint;
   wire it through `load_pretrained` and compare latent quality vs `conv_ae`.
4. **Phase labels for Animal 9.** The drift figure needs real phase labels; right
   now those come from parsing type-15 log annotations (still open — Suchith).
5. **Expand to ani-emg-eeg-10** once the Animal 9 run is clean.

Open blockers Suchith still owns: Animal 9 baseline-subtraction bug (frag0 from
preceding record) and phase-label recovery. Those feed task 1 and 4.

---

## Design choices worth knowing
- Per-trial z-scoring in the dataset removes DC/gain differences that would
  otherwise dominate the latent space and hide phase structure.
- The conv encoder infers its own flatten size, so changing `window_samples`
  (150 for Animal 9, 250 for Animals 16/17) just works.
- Both encoders share one interface (`encode`, `pretrain_step`) so the trainer
  is identical regardless of path — swap encoders freely.
