# Animal 9 — FIRST REAL-DATA RUN (2026-07-07)

This is the first end-to-end run of the pipeline on **real Animal 9 data**, not
synthetic. It replaces the synthetic smoke-test numbers. The figures in
`outputs/` are now real (no `SYNTHETIC` watermark).

## What was done tonight
1. Loaded the real `emg-eeg-9-data.MYD` (2.3 GB MyISAM) into a local MariaDB.
   Recovered the log table too (borrowed `array-16-log.frm` as schema template).
2. **Decoded the real signal and confirmed the format** (corrects the docs):
   - LITTLE-endian int16 (decoder_2006's "big-endian" is wrong — big = noise).
   - Block channel layout: chan A = SOLR soleus EMG, chan B = ECoG.
   - ad2uV = 2.441406 (confirmed by log type-5 entry).
   - frag1 = 150 samples @ 5 kHz = the M/H response window.
3. **Recovered real phase labels** from the type-15 experimenter log. Animal 9 ran
   **Baseline → Down-conditioning → Post**, NOT the full 6-phase protocol.
   Boundaries from log markers "Start HRdown" and "Stopped conditioning".
4. **Verified the H-reflex latency from the log**: experimenter wrote
   "MR interval: 2-4; HR interval: 6-9" — so the H-reflex is at **6–9 ms**, not
   the 8–10 ms the pipeline assumed. Config updated; empirical M peak ≈3.8 ms,
   H ≈6.8 ms match the log exactly.
5. Converted all **283,315 trials** to `data/processed/animal9.zarr` and trained
   the two-phase autoencoder on the real ECoG.

## Trial counts (real, per phase)
| phase | trials |
|---|---|
| Baseline | 149,064 |
| Down-conditioning | 55,397 |
| Post-conditioning | 78,854 |

## Results (REAL)
- **Phase 1 reconstruction:** val MSE 0.0134 → **0.0035** (encoder learns to
  compress + rebuild the real cortical window).
- **Phase 2 H-reflex regression (frozen encoder): val R² = 0.172.** The
  unsupervised cortical latent explains ~17% of H-reflex-amplitude variance,
  with the encoder never having seen a label. Modest but real and well above
  chance. (Synthetic was 0.90 only because the synthetic ECoG was *built* to
  encode the H-reflex — real cortex is far noisier, so 0.17 is the honest number.)
- **Latent drift across phases (`centroid_drift.png`):**
  Baseline 0.00 → **Down-conditioning 28.48** → Post-conditioning 4.98.
  The average cortical representation shifts substantially during conditioning
  and **returns toward baseline after conditioning stops** — a coherent,
  interpretable trajectory.
- **Per-trial separation is weak** (`umap_by_phase.png`, phase silhouette
  −0.069): individual trials from different phases overlap heavily. So the drift
  is a real *population mean shift*, not a clean per-trial reclassification.

## Behavioral ground truth (H-reflex amplitude by phase) — READ THIS
Mean rectified H-reflex (6–9 ms) per phase:
| phase | n | mean µV | median µV |
|---|---|---|---|
| Baseline | 149,064 | 182.3 | 127.2 |
| Down-conditioning | 55,397 | 246.2 | 205.3 |
| Post-conditioning | 78,854 | 170.2 | 120.3 |

**The H-reflex is HIGHER during down-conditioning, not lower.** Down-conditioning
trains the animal to *suppress* the reflex, so naively this looks backwards. Most
likely explanation: the "Baseline" block here is really the **setup /
characterization period** — the type-15 log shows constant `TARG:` (stimulus
intensity) adjustments throughout it, so stimulus wasn't yet at a fixed operating
point and evoked responses are smaller/inconsistent. During active conditioning
the stimulus is fixed, giving larger, steadier responses.

**Why this matters for the cortical result:** the cortical latent drifts MOST
during down-conditioning, and so does raw H-reflex amplitude / background EMG.
So part of the 28.48 cortical drift may track overall session state (fixed-stim,
active recording, arousal) rather than the conditioning learning per se. This is
the single most important thing to resolve before claiming "cortical correlates
of conditioning." Ways to disentangle: restrict Baseline to post-setup trials
only; regress out raw EMG/M-wave amplitude; use within-phase splits as a null.

## Honest read for the slides
The machine now runs on real Animal 9 end to end. The headline is the
**centroid-drift trajectory**: cortical representation moves during
down-conditioning and recovers post — exactly the "does the brain change as the
cord learns?" signal. Caveats to state plainly: (a) R²=0.17 and negative
silhouette mean the effect is a subtle mean shift, not dramatic; (b) single
animal, single conditioning direction (no up-conditioning), so no negative
control yet; (c) needs statistics (is 28.48 vs 4.98 significant vs
within-phase variability?) before it's a claim.

## Open items
- **Statistics / negative control:** bootstrap the centroid distances; a
  within-baseline split should drift ~0. Freely-Running / up-conditioning animals
  would be the real negative/positive controls.
- **Baseline-subtraction refinement:** label baseline currently uses the quiet
  20–30 ms tail; the "frag0 from preceding record" cross-trial correction is not
  applied (was a known open bug) — worth testing whether it changes the drift.
- **More animals:** pool 6/10/11/12/13 once each converts; watch the
  batch-effect check (animal vs phase silhouette).

## How to reproduce
```bash
# MariaDB already loaded at socket /tmp/hroc_mysql.sock, db emg_eeg_9
# (to restart the DB, see the convert command's DSN)
python scripts/convert.py --dsn "mysql+pymysql://root@localhost/emg_eeg_9?unix_socket=/tmp/hroc_mysql.sock" \
    --animal 9 --out data/processed/animal9.zarr --config config.yaml
python scripts/validate_zarr.py --zarr data/processed/animal9.zarr
python scripts/run_all.py --config config.yaml    # use_synthetic already false
```
