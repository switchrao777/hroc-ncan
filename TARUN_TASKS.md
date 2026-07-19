# Tarun — what we're doing & your tasks this week

## The big picture (read first)
We're testing whether the **cortex changes as the spinal cord learns** a
conditioned H-reflex, using the paired EMG+ECoG animals. Where things stand on
Animal 9 (fully processed on Suchith's machine):

- **Decode + pipeline: done and validated.** 283k trials, clean M-wave/H-reflex.
- **Behaviour: solid.** Down-conditioning worked — H/M ratio falls to ~0.18.
- **Cortical drift: did NOT survive the null control.** When we split *baseline-only*
  data as a fake experiment, it "drifts" as much as the real conditioning. In one
  animal, conditioning and slow recording/electrode drift are both smooth in time,
  so they're confounded. **The cortical claim can only be settled by comparing
  UP- vs DOWN-conditioned animals** (recording drift is direction-independent; a
  real conditioning signal must differ by direction).

So this week is about **getting more animals in** and running the up-vs-down test.
Suchith is downloading animals 10/11/12 and processing them on his machine.

## Important: your earlier run had a decode bug
Your first pass used `decoder_2006.py` as-is, which reads **big-endian** — but this
data is **little-endian** (big-endian gives a ~9,600 µV wall of noise with no
M/H bumps; that's why your R² was 0.12 and your waveform looked wrong). The repo's
`scripts/convert.py` has the fix (little-endian, reads MySQL blobs, real phases,
timestamps). **Use it — don't use the raw-byte decoder.**

---

## Your tasks (in priority order)

### 1. Sync + validate your environment  [~1 hr]
```bash
git pull                       # get the validated pipeline
pip install -r requirements.txt
python scripts/run_all.py --config config.smoke.yaml   # smoke test, must pass
```
Then reproduce Animal 9's decode QC so your machine matches ours: load Animal 9's
MyISAM into your local MySQL, run `scripts/inspect_db.py` and
`scripts/confound_control.py`, and confirm you see **clean M/H bumps** and the
**H/M learning curve falling to ~0.18**. If you get noise, your decode is still
wrong — ping Suchith before going further.

### 2. Draft the paper — Intro + Methods  [main job, ~2-3 days]
This is the highest-value thing you can do in parallel, and it doesn't touch the
data pipeline. Draft two sections (Google Doc is fine):
- **Introduction:** operant H-reflex conditioning background (Wolpaw/Thompson —
  the mini-review PDF in the drive), why the cortical side is unexplored, and our
  question. ~600 words.
- **Methods — Data & Decoding:** the Elizan III dataset, the 2006 MyISAM format,
  how trials decode (little-endian int16, block channels: ch0 = soleus EMG,
  ch1 = ECoG, ad2uV = 2.441406, 150-sample 5 kHz window), and the **H/M** measure
  with the 6–9 ms H window / 2.5–4 ms M window. Pull the exact numbers from
  `REAL_RESULTS.md` and `scripts/convert.py`. ~700 words.

### 3. Help find an UP-conditioned animal  [~1 hr]
The up-conditioned animal is the make-or-break. Download the small **log files**
(`emg-eeg-N-log.MYD`, ~300 KB each) for animals **13, 14, 15** into a folder and
send them to Suchith (or run `scripts/scan_animals.py` if you've set up MariaDB —
note it has Suchith-machine paths at the top you'd edit: `DATADIR`, `TEMPLATE_FRM`,
socket). We read the "Start HRup" / "Start HRdown" marker to classify direction
without downloading the 2.3 GB data files.

### 4. (Stretch) Process one full animal on your machine
Only after task 1 passes. Download one animal's 6 files, then:
```bash
python scripts/load_animal.py --animal <N> --dir <folder>   # edit paths at top for your machine
python scripts/run_animal.py  --animal <N>
```
Check `outputs/animal<N>/confound/learning_curve.png` and `drift/null_control.png`.
Report the direction, whether conditioning worked (H/M), and the null-control result.

---

## What NOT to do
- Don't pool up + down animals together, ever. Per-animal first, then within one
  direction.
- Don't trust raw H-reflex amplitude — always H/M (stimulus control).
- Don't use the big-endian raw-byte decoder.

Questions → Suchith. The plan and current results are in `NEXT_TWO_WEEKS.md` and
`REAL_RESULTS.md`.
