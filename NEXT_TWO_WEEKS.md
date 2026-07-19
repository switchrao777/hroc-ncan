# HROC — Next Two Weeks (expedited toward a write-up)

_Status after the drift-over-time + null-control run (2026-07-08)._

## The pivotal finding — read first
We ran Carp's null control. **The single-animal cortical drift does not survive it.**
- Baseline-only data (no conditioning) split as a "sham experiment" drifts as much
  (~42) as the real conditioning (~17).
- The real drift **rises during baseline, peaks at conditioning onset, and falls
  during the strongest behavioural learning** — it's anti-aligned with the actual
  H/M drop. See `outputs/drift_time/`.
- Removing the M-wave changes nothing, so it isn't the stimulus either. It's slow
  **recording / electrode nonstationarity** over weeks.

**Why this is expected, not a failure:** in ONE animal, conditioning and recording
drift are both slow functions of time, so they are mathematically confounded — no
single-animal analysis can separate them. This is exactly why the null control
exists, and exactly why Carp emphasised the up-vs-down comparison.

**What is solid:** the decode, the pipeline, and the **behaviour** — down-conditioning
worked (H/M 1.17 → ~0.18). That result is real and publishable.

**What this means for the claim:** we cannot claim a conditioning-specific cortical
drift from Animal 9 alone. The cortical question is decided by the **up-vs-down
multi-animal test** — recording drift is direction-independent, so a real
conditioning signal must differ (ideally flip sign) between up- and down-conditioned
animals. That test is now the make-or-break, and the #1 priority.

---

## Strategy: two papers' worth of material, sequenced
1. **Now (solid):** an ML/methods + behaviour result — decode 20-yr-old data at
   scale, learn a self-supervised cortical representation, quantify down-conditioning
   with proper H/M, and demonstrate (via the null control) that naive cortical-drift
   metrics are confounded by recording nonstationarity. That cautionary methods
   contribution is genuinely valuable and defensible today.
2. **Gated on animals (the prize):** the up-vs-down cortical contrast. If cortex
   drifts oppositely for up vs down conditioning, that's the novel neuroscience
   result and the real paper. If it doesn't, we've cleanly shown the cortical effect
   is recording drift — still publishable, still honest.

Set expectations with Carp: a **behaviour + methods** write-up is reachable in ~2
weeks; the **cortical claim** depends on getting ≥1 up-conditioned animal converted.

---

## The plan, in order (each item gates the next)
1. **[DONE] Timestamps in the Zarr** — `time`+`day` arrays; `convert.py` writes them
   every run; `outputs/animal9_trial_time.csv` for anyone without the DB.
2. **[DONE] Daily-waveform QC** — `outputs/drift_time/daily_waveform_qc.png`. Data is
   clean; M-wave grows over days (the confound, visualised).
3. **[DONE] Drift per 5-day block** — `outputs/drift_time/drift_over_time.png`.
4. **[DONE] Null control + shuffle test** — the finding above.
5. **Detrend test (this week):** does the cortical latent track H/M *beyond* the
   shared time trend? Residualise latent and H/M on a smooth `day` trend, test the
   residual link. Expect it to be weak in one animal — but it sets up the multi-animal
   analysis. (New script; ~half a day.)
6. **Tighten windows (this week):** M-wave left edge → 2.6 ms (done in the analysis
   windows), keep H at 6–9 ms. Re-run confound_control + drift with the tightened M.
7. **Pre-stimulus excitability control (this week):** pull `frag0` (the −50→0 ms
   pre-stim fragment already in the DB) and add background excitability as a second
   nuisance regressor alongside the M-wave. Rules out "the animal was just more
   active" as the driver.
8. **Convert a second animal (next week):** ideally an **up-conditioned** one — see
   below. Clean it individually (decode QC → H/M learning curve → null control) before
   any pooling.
9. **Up-vs-down contrast (next week):** run the identical drift pipeline per animal,
   then compare time-courses across directions. This is the decisive test.

---

## What animals to convert next
- **Only Animal 9 (paired EMG+ECoG) is on disk.** The other conditioned animals must
  be downloaded from the Drive. `array-16` is present but it's an ECoG-array set — not
  the paired EMG+H-reflex format we need.
- **Action for Suchith:** confirm with Carp **which conditioned animals are UP vs
  DOWN** (he wasn't sure in the meeting) — this drives everything. Then download, from
  the Drive, the `ani-emg-eeg-N` folder for:
  1. **one UP-conditioned animal** (highest value — enables the opposite-drift test),
  2. the other **down-conditioned** animals (to pool within direction).
  Grab the 6 files per animal (`*-data.{MYD,MYI,frm}`, `*-log.{MYD,MYI,frm}`).
- **Rule:** clean each animal alone, pool only within a direction, never mix up+down.

---

## Publication logistics (from Carp)
- Target presentable: **mid-to-late August**.
- **SfN late-breaking abstracts: Sept 8–15** — the real deadline; feasible for the
  behaviour+methods story, and for the cortical story only if animals are in by then.
- Possible Albany visit ~**Aug 14–21** (avoid Aug 18 — Carp in Texas).
- Longer shot: NeurIPS/ICML for the ML angle.

---

## Immediate next build (say the word)
Item 5 + 6 together: the **detrend / partial-correlation test** (does cortex track the
reflex beyond the time trend?) plus the tightened-M re-run — this is the last
single-animal analysis worth doing before the story hinges on getting animal #2.
