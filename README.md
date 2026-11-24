# ARC: Autoencoder for Reflex Conditioning

**A self-supervised pipeline relating sensorimotor cortex activity to single-trial H-reflex size in rats**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24489072.svg)](https://doi.org/10.5281/zenodo.24489072)

> Presented at **Neuroscience 2026 (Society for Neuroscience)**, Washington, D.C. — Late-Breaking Poster **LBP066.07**, Board C25, Session F.05 Brain-Machine Interface, November 17, 2026.
> S. Rao, T. Senthil, C. Boulay, J. R. Wolpaw, T. M. Vaughan, J. S. Carp
> [Poster (Zenodo, DOI 10.5281/zenodo.24489072)](https://doi.org/10.5281/zenodo.24489072) · [Abstract](https://www.abstractsonline.com/pp8/#!/21503/presentation/34791) · [Citation](#citation)

Machine-learning analysis of paired soleus EMG and sensorimotor ECoG recordings
from the operant H-reflex conditioning paradigm, in collaboration with the
National Center for Adaptive Neurotechnologies (NCAN), Stratton VA Medical Center, Albany, NY.

**Project page:** [docs/index.html](docs/index.html) ·
**Report:** [docs/HROC_Report.pdf](docs/HROC_Report.pdf) ·
**Slides:** [slides/](slides/)

---

## The question

Rats are rewarded for making the soleus H-reflex larger or smaller. Over weeks
the spinal cord itself changes; a 20% shift is the criterion for success. Boulay,
Chen and Wolpaw (2015) showed that cortical activity influences reflex size. We
ask whether cortical state predicts reflex size on a single trial, and whether
that relationship changes with conditioning.

## Findings (as presented at SfN 2026)

Five rats, 2.3 million trials, 80 five-day blocks from the control and conditioning periods.

| | |
|---|---|
| **Conditioning worked in 3 of 5 rats** | H-reflex size changed in the rewarded direction past the 20% criterion in three of five animals. |
| **Pre-stimulus power predicts the reflex** | Within each five-day block, a learned representation of the 1-s pre-stimulus ECoG spectrum and six conventional band powers both beat a shuffle of that block's own trials (72 and 74 of 80 blocks, p = 0.006 for each). Waveform shape did not (34 of 80, p = 0.56). |
| **Small but consistent cortical contribution** | M-response size explains 51.1% of trial-to-trial H-reflex variance; background EMG adds 0.4 points; the post-stimulus ECoG representation adds 2.1 points uniquely (above zero in every rat, 0.5% to 6.0%); 46.4% is unexplained. |
| **The intuitive drift analysis fails its own control** | With no conditioning at all, the sham's largest distance exceeded the conditioning mean in 4 of 5 rats. Claims about conditioning-related cortical change need within-block tests. |

Post-stimulus ECoG predicts the reflex most strongly, but mostly through variance
shared with M-response size, since both follow stimulus intensity.

## Controls

Every cortical claim had to survive: within-block cross-validation, a per-block
shuffle null with the rat as the unit of analysis, regression on the M-response,
regression on pre-stimulus background EMG, and a pre-conditioning sham.

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

## Next

Rats 7, 8, 13 and 14 are being processed to test whether coupling tracks how
much each rat learned, followed by a full paper.

## Citation

If you use this pipeline, please cite:

> Rao S, Senthil T, Boulay C, Wolpaw JR, Vaughan TM, Carp JS (2026). ARC--Autoencoder for Reflex Conditioning: A self-supervised pipeline relating sensorimotor cortex activity to single-trial H-reflex size in rats. Program No. LBP066.07. *Neuroscience 2026*. Washington, DC: Society for Neuroscience. Poster: https://doi.org/10.5281/zenodo.24489072

```bibtex
@inproceedings{rao2026arc,
  title     = {ARC--Autoencoder for Reflex Conditioning: A self-supervised pipeline relating sensorimotor cortex activity to single-trial H-reflex size in rats},
  author    = {Rao, Suchith and Senthil, Tarun and Boulay, Chadwick and Wolpaw, Jonathan R. and Vaughan, Theresa M. and Carp, Jonathan S.},
  booktitle = {Neuroscience 2026},
  publisher = {Society for Neuroscience},
  address   = {Washington, DC},
  note      = {Program No. LBP066.07},
  doi       = {10.5281/zenodo.24489072},
  year      = {2026}
}
```

## References

Boulay CB, Chen XY, Wolpaw JR. Electrocorticographic activity over sensorimotor
cortex and motor function in awake behaving rats. *J Neurophysiol* 113:2232–2241,
2015.

Thompson AK, Wolpaw JR. Operant conditioning of spinal reflexes: from basic
science to clinical therapy. *Front Integr Neurosci* 8:25, 2014.

Wang C et al. BrainBERT: Self-supervised representation learning for intracranial recordings. *ICLR* 2023. arXiv:2302.14367.

## Support

Stratton VA Medical Center, NIH P41 EB018783, and NYS SCIRB C38338GG. Some Python
code was generated with Claude (Anthropic), reviewed and validated by SR and TS.
