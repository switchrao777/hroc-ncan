# Cortical correlates of H-reflex operant conditioning

Machine-learning analysis of paired soleus EMG and sensorimotor ECoG recordings
from the operant H-reflex conditioning paradigm, in collaboration with the
National Center for Adaptive Neurotechnologies (NCAN), Wadsworth Center.

**Project page:** [docs/index.html](docs/index.html) ·
**Report:** [docs/HROC_Report.pdf](docs/HROC_Report.pdf) ·
**Slides:** [slides/](slides/)

---

## The question

Rats are rewarded for making the soleus H-reflex larger or smaller. Over weeks
the spinal cord itself changes; a 20% shift is the criterion for success. Boulay,
Chen and Wolpaw (2015) showed that cortical activity influences reflex size. We
ask whether that relationship is altered by learning, and whether it is visible
on a single trial.

## Findings

| | |
|---|---|
| **Conditioning reproduces in both directions** | Corrected H-reflex amplitude rises in up-conditioned animals and falls in down-conditioned animals. Three of five clear the 20% criterion. |
| **Cortex predicts the reflex trial by trial** | Decoders cross-validated *within* five-day blocks beat a shuffle of their own block's labels in 99 of 101 blocks. R² = 0.037; animal-level t(4) = 3.81, p = 0.019. |
| **Average-state drift is not learning** | The intuitive analysis fails three separate controls and reflects slow recording nonstationarity. |

Cortex contributes about 2% of H-reflex variance uniquely, once stimulus
intensity (47%) and pre-stimulus excitability (1%) are accounted for. Animals
that learned more show a larger increase in coupling (r = +0.71, n = 5), which
the remaining recordings would be needed to confirm.

## Controls

Every cortical claim had to survive: a baseline sham split, a randomised trial-order
null, regression on the M-wave, regression on pre-stimulus background EMG,
within-block cross-validation, a cortex-versus-muscle band-power crosstalk test,
and an up-versus-down direction contrast.

---

## Repository

```
scripts/     decoding, conversion, covariates, and every analysis
src/         config, data loading, preprocessing, models, training, figures
decoders/    original archive decoders (2006 / 2013 formats)
notebooks/   starter notebook for loading and training
outputs/     figures and per-animal results
docs/        project page and report
slides/      presentations
```

Setup and per-animal instructions are in [SETUP.md](SETUP.md). The animal
inventory and conditioning directions are in [ANIMAL_ROSTER.md](ANIMAL_ROSTER.md).

Raw recordings are not included; they remain with NCAN. `.MYD`/`.MYI`/`.frm`
archives, Zarr stores and the local database directory are gitignored.

## Data format notes

Samples are little-endian 16-bit integers in block channel order (soleus EMG
first, then ECoG), at 2.441406 µV per unit. The archived decoder documents
big-endian, which decodes to noise. Fragment 1 carries the 150-sample, 5 kHz
response window used throughout; fragment 0 is one second of pre-stimulus signal
at 1 kHz.

## References

Boulay CB, Chen XY, Wolpaw JR. Electrocorticographic activity over sensorimotor
cortex and motor function in awake behaving rats. *J Neurophysiol* 113:2232–2241,
2015.

Thompson AK, Wolpaw JR. Operant conditioning of spinal reflexes: from basic
science to clinical therapy. *Front Integr Neurosci* 8:25, 2014.
