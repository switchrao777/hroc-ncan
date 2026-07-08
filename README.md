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

**H-reflex label definition (Dr. Carp, 2026-07-01):** the label is the **mean
rectified amplitude** in a matched window around the H-reflex — NOT peak-to-peak
(a single peak gets corrupted by background activity). Baseline-correct, rectify,
average over a window that encompasses the burst. The window must be identical
across every trial and phase, and should be set by eyeballing the trial-averaged
waveform. This lives in one place, `src/data/hreflex_label.py::compute_hreflex_label`,
which both the synthetic generator and the real converter call. Window bounds are
in `config.yaml` under `signal.hreflex_window_ms`.

---

## Real data — pooling ALL animals (the default path)

We are NOT using synthetic data for results. The plan is to decode every animal
(6, 9, 10, 11, 12, 13, 16, ...) and pool them into one autoencoder.

Write one Zarr store per animal (same schema, window length is whatever that
animal's format is — 150 for 2006, 250 for 2013):

```
animal9.zarr/
  ecog     (N, win)  float32   # cortical channel — the AE input
  emg      (N, win)  float32   # EMG channel (validation + label source)
  hreflex  (N,)      float32   # per-trial H-reflex label (compute_hreflex_label, NATIVE signal)
  phase    (N,)      int64     # conditioning phase 0..5
```

Then list every animal in `config.yaml`:
```yaml
data:
  animals:
    - {id: "9",  zarr_path: "data/processed/animal9.zarr"}
    - {id: "16", zarr_path: "data/processed/animal16.zarr"}
    # ...add each as its converter finishes
  common_window_samples: 200   # all animals resampled to this before pooling
```

The loader resamples every animal to `common_window_samples` (so 150- and
250-sample formats pool cleanly), tags each trial with its animal id, and pools.
The H-reflex label is computed per-animal on the NATIVE signal in the converter,
so resampling never touches it.

**Watch the batch-effect check.** Pooling animals risks the latent separating by
*animal identity* instead of *conditioning phase*. Every run now reports a phase
silhouette AND an animal silhouette, plus `umap_by_animal.png`. If the animal
silhouette is higher than the phase silhouette, the report prints a WARNING — the
latent is dominated by which animal a trial came from, and you need per-animal
normalization / batch correction (e.g. per-animal z-scoring, or an animal-
adversarial term) before the drift result means anything. Start by running each
animal ALONE to get a clean per-animal drift, THEN pool.

Workflow order: (1) one animal alone → clean result, (2) add animals one at a
time, watching the batch-effect check, (3) pool all with correction if needed.

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
   Animal 9. For the `hreflex` array, call
   `compute_hreflex_label(emg, cfg.signal)` — don't invent your own amplitude
   measure; that function is Carp's agreed spec (mean rectified amplitude in a
   matched window). Set `signal.hreflex_window_ms` from the trial average first.
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
