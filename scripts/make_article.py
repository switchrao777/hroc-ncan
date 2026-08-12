"""Render the project write-up to a formatted PDF handout.

Produces docs/HROC_Report.pdf — a short article-style summary with figures and the
real numbers, suitable to hand out alongside the presentation.

Usage:  python scripts/make_article.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "HROC_Report.pdf"

CSS = """
body { font-family: serif; font-size: 10.2pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 19pt; margin: 0 0 2pt 0; line-height: 1.2; }
h2 { font-size: 12.5pt; margin: 14pt 0 4pt 0; color: #4c1d95; }
h3 { font-size: 10.8pt; margin: 10pt 0 3pt 0; color: #0f172a; }
p  { margin: 0 0 6pt 0; text-align: justify; }
.authors { font-size: 10.5pt; margin: 6pt 0 1pt 0; }
.affil   { font-size: 8.6pt; color: #444; margin: 0 0 2pt 0; }
.meta    { font-size: 8.4pt; color: #666; margin: 2pt 0 10pt 0; }
.abstract { font-size: 9.5pt; background: #f4f4f8; padding: 8pt; margin: 0 0 10pt 0; }
.cap  { font-size: 8.4pt; color: #555; margin: 2pt 0 10pt 0; }
.ref  { font-size: 8.8pt; margin: 0 0 5pt 0; }
.note { font-size: 9pt; background: #fdf6ec; padding: 7pt; margin: 8pt 0; }
th { font-size: 9pt; text-align: left; padding: 3pt 6pt; border-bottom: 1px solid #999; }
td { font-size: 9pt; padding: 3pt 6pt; border-bottom: 1px solid #e2e2e2; }
.num { text-align: right; }
b { color: #0f172a; }
"""

BODY = """
<h1>Single-trial cortical prediction of the H-reflex during operant conditioning</h1>
<p class="authors"><b>Suchith Rao</b><sup>1</sup> and <b>Tarun Senthil</b><sup>1</sup>,
with <b>Dr. Jonathan S. Carp</b><sup>2</sup> and <b>Teresa [surname]</b><sup>2</sup></p>
<p class="affil"><sup>1</sup>Machine-learning analysis &nbsp;·&nbsp;
<sup>2</sup>National Center for Adaptive Neurotechnologies (NCAN), Wadsworth Center,
New York State Department of Health, Albany, NY</p>
<p class="meta">Progress report &nbsp;·&nbsp; August 2026 &nbsp;·&nbsp;
Code and data: github.com/switchrao777/hroc-ncan</p>

<div class="abstract">
<b>Summary.</b> Operant conditioning of the spinal H-reflex produces lasting change in
the spinal cord, and sensorimotor cortex is known to influence the reflex pathway
(Boulay et al., 2015). Whether cortical activity <i>changes</i> as the animal learns
has not been established. We decoded 2.7 million trials of paired soleus EMG and
sensorimotor ECoG from six chronically implanted rats (three down-conditioned, three
up-conditioned) recorded on the Elizan III system, and trained a self-supervised
autoencoder on the cortical waveform. Three results follow. First, conditioning
reproduced in both directions after controlling for stimulus intensity and
motoneuron-pool excitability. Second, the naive measure — drift of the average
cortical state across conditioning — does not survive its own controls and reflects
slow recording nonstationarity rather than learning. Third, using a design in which
decoders are trained and tested <i>within</i> five-day blocks, cortical activity
predicts single-trial H-reflex amplitude above a within-block shuffle null in 99 of
101 blocks across all five animals (animal-level t(4) = 3.81, p = 0.019), contributing roughly 2% of
reflex variance uniquely once stimulus and background are accounted for. The effect is
small in magnitude but near-perfectly reliable. Across animals, the change in this coupling correlates
with how much each animal learned (r = +0.71, n = 5), though the sample is not yet
sufficient for significance.
</div>

<h2>1. Background</h2>
<p>In the operant conditioning paradigm developed in this laboratory, rats are
rewarded for increasing or decreasing the size of the soleus H-reflex, the largely
monosynaptic electrical analogue of the spinal stretch reflex. Over several weeks the
reflex changes, and the change persists in the spinal cord itself; a shift of 20% or
more is the laboratory's criterion for successful conditioning (Thompson and Wolpaw,
2014). Boulay, Chen and Wolpaw (2015) showed that ongoing sensorimotor cortex activity
influences H-reflex size in awake behaving rats, establishing that a cortical–spinal
relationship exists. The question we address is whether that relationship itself is
altered by learning, and whether it is detectable on individual trials.</p>

<h2>2. Data and methods</h2>
<h3>2.1 Dataset and decoding</h3>
<p>Recordings were made on the Elizan III system between 2005 and 2007 and archived as
MyISAM tables. Each stimulus produces one trial containing a 30 ms window sampled at
5 kHz on two channels: soleus EMG and sensorimotor ECoG. We reconstructed the binary
format directly; contrary to the archived decoder documentation, samples are stored
<i>little-endian</i> as 16-bit integers in block channel order, with a conversion
factor of 2.441406 µV per unit. Decoding as documented yields noise. Conditioning
onset and direction were recovered per animal from the experimenters' typed
annotations. Six animals passed quality control, comprising 2.7 million trials over
45 to 210 days each.</p>

<h3>2.2 Reflex measurement</h3>
<p>Raw H-reflex amplitude is not interpretable in isolation because it scales with
stimulus intensity; in these recordings the M-wave drifted from roughly 100 to 450 µV
over the course of an experiment, which alone can reverse the apparent direction of an
effect. We therefore measure, per trial and after background subtraction, the M-wave
(2–4 ms) as a receipt for delivered stimulus, the H-reflex (6–9 ms), and the
pre-stimulus background EMG in the 20 ms preceding the stimulus as an index of
motoneuron-pool excitability. Both the M-wave and the background are removed from
every subsequent measure by regression, including quadratic terms.</p>

<h3>2.3 Cortical representation</h3>
<p>A one-dimensional convolutional autoencoder compresses each 150-sample cortical
window to a 48-dimensional code, trained on 600,000 trials pooled across five animals
with per-animal standardisation and no access to any label. The encoder is then frozen
and used purely as a feature extractor.</p>

<h3>2.4 Controls</h3>
<p>Four controls constrain every cortical claim. A <i>baseline sham</i> splits
pre-conditioning data as though it were an experiment; nothing occurred, so an honest
measure must report approximately zero. A <i>randomised-order</i> null shuffles the
assignment of trials to days, preserving the numbers while destroying time structure.
A <i>direction contrast</i> exploits the fact that electrode drift is independent of
whether an animal was trained up or down, whereas learning is not. Finally, coupling
analyses are cross-validated <i>within</i> five-day blocks, so slow drift displaces
training and test trials together and cancels.</p>

<h2>3. Results</h2>
<h3>3.1 Conditioning reproduces in both directions</h3>
<p>After correction for stimulus and background, corrected H-reflex amplitude rises in
up-conditioned animals and falls in down-conditioned animals, Three of five analysed animals meet the 20% criterion in the trained direction; the two
that do not serve as internal controls below. We report change as log₂ fold change
rather than percentage: percentage change divides by baseline amplitude, and one animal
(A3) has a baseline H of 19.4 µV against 60–167 µV in the others, which inflates its
percentage to +227%. On the log₂ scale its change (+1.71) is comparable in magnitude to
the down-conditioned animals (−1.55, −1.46), and the measure is symmetric for increases
and decreases.</p>
"""

BODY2 = """
<h3>3.2 Average-state drift does not reflect learning</h3>
<p>The intuitive analysis — measuring how far the mean cortical representation moves
from baseline — yields a large apparent effect that does not survive scrutiny. The
baseline sham drifts as much as genuine conditioning in five of six animals; the drift
is largest at conditioning onset and declines during the period of strongest
behavioural change; and there is no dependence on conditioning direction (up 21.9 vs
down 34.6, t = −1.01). The randomised-order null is approximately zero throughout,
indicating the metric is not an artefact of the data values themselves. We conclude
that this drift reflects slow change in the recording rather than learning. Within a
single animal, learning and electrode drift are both smooth functions of time and are
therefore not separable; this is a limitation of the design, not of the data.</p>

<h3>3.3 Cortical activity predicts single-trial reflex amplitude</h3>
<p>Reframing the question removes the confound. Decoders trained and tested within
five-day blocks predict single-trial H-reflex amplitude above a within-block label
shuffle in 99 of 101 blocks and in all five animals (mean cross-validated R² = 0.037,
null = −0.009; treating animal as the unit of analysis, t(4) = 3.81, p = 0.019; the block-level sign test is not quoted because blocks within an animal are not independent). Judged by magnitude the effect is
small; judged by reliability it is close to invariant. Removing
stimulus and background <i>within</i> each block rather than globally is essential: the
global procedure leaves between-block stimulus variance, which cortex tracks, and
inflates the estimate to 0.090. We report the conservative value.</p>

<h3>3.4 Variance partition</h3>
<p>Partitioning variance in H-reflex amplitude clarifies the magnitude of the cortical
contribution.</p>
<table>
<tr><th>Source</th><th class="num">Variance explained</th><th>Interpretation</th></tr>
<tr><td>Stimulus (M-wave)</td><td class="num">47%</td><td>Dominant factor</td></tr>
<tr><td>Background excitability</td><td class="num">1%</td><td>Small but a necessary control</td></tr>
<tr><td>Cortical activity, alone</td><td class="num">21%</td><td>Largely shared with stimulus</td></tr>
<tr><td><b>Cortex, unique</b></td><td class="num"><b>2%</b></td><td>Added once the others are known</td></tr>
<tr><td>Unexplained</td><td class="num">51%</td><td>Residual trial-to-trial variability</td></tr>
</table>
<p class="cap">Cross-validated within blocks, averaged over five animals. Cortex and
stimulus share substantial variance because the stimulus drives both the cortical
evoked response and the reflex; only the non-overlapping portion is counted as unique.</p>

<h3>3.5 The effect is not muscle contamination</h3>
<p>Because both channels are recorded simultaneously, the ECoG electrode could in
principle register muscle activity. Correlating cortical against muscle band power
across trials gives r = +0.057 above 100 Hz, the range in which muscle artefact would
appear, with slightly negative correlations in the lower bands. A lead–lag comparison
places cortical power marginally ahead of muscle power. Contamination is therefore an
unlikely explanation.</p>

<h3>3.6 The effect scales with learning</h3>
<p>Animals differ in how much they learned, and two failed to reach criterion in the
trained direction. Across animals, the change in cortical coupling from baseline to
conditioning correlates with behavioural change (r = +0.709 on log₂ fold change, t = 1.74, n = 5). The two
successful animals for which coupling could be compared gained coupling (+0.023 and
+0.022); the two unsuccessful animals did not (−0.012 and +0.000). The direction is
that predicted if the coupling is tied to conditioning, but the sample is too small for
significance.</p>

<h2>4. Discussion</h2>
<p>Two conclusions are supported. Operant conditioning of the H-reflex is reproducible
in both directions under proper stimulus control, and cortical activity carries a
small, consistent, single-trial signal about reflex amplitude that is not attributable
to stimulus intensity, motoneuron-pool excitability, recording drift, or muscle
crosstalk. This extends Boulay et al. (2015) from a population relationship to a
single-trial one, and situates its magnitude relative to the other contributors.</p>
<p>A third conclusion is methodological and, we suggest, worth reporting. The obvious
analysis — tracking movement of the mean cortical state across weeks — produces a
convincing-looking result that three independent controls reject. Investigators
applying representation-learning methods to long chronic recordings should expect this
confound and test for it directly.</p>

<h3>Limitations</h3>
<p>The sample is five analysed animals, of which two are up-conditioned; a survey of
the archived reward criteria indicates no further successfully up-conditioned animals
with usable cortical recordings exist in this dataset, so the direction contrast cannot
be strengthened. One animal (A12) was excluded because its pre-stimulus cortical signal
was 2.8 µV against 106–128 µV in the others, indicating electrode failure. Whether
coupling strengthens with conditioning is not resolved at this sample size; the
remaining down-conditioned animals would power that test.</p>

<h2>Acknowledgements</h2>
<p>We thank Dr. Jonathan S. Carp and Teresa [surname] of NCAN for guidance throughout,
and in particular for proposing the baseline sham control, the randomised-order
control, the pre-stimulus excitability covariate, and the scaling analysis, each of
which materially changed the conclusions. This work uses recordings collected in the
Laboratory of Neural Injury and Repair at the Wadsworth Center.</p>

<h2>References</h2>
<p class="ref">Boulay CB, Chen XY, Wolpaw JR. Electrocorticographic activity over
sensorimotor cortex and motor function in awake behaving rats.
<i>Journal of Neurophysiology</i> 113: 2232–2241, 2015. doi:10.1152/jn.00677.2014</p>
<p class="ref">Thompson AK, Wolpaw JR. Operant conditioning of spinal reflexes: from
basic science to clinical therapy. <i>Frontiers in Integrative Neuroscience</i> 8: 25,
2014. doi:10.3389/fnint.2014.00025</p>

<div class="note"><b>Reproducibility.</b> All decoding, analysis and figure code, the
per-animal numerical results, and the presentation materials are available at
github.com/switchrao777/hroc-ncan. Raw recordings remain with NCAN.</div>
"""

FIG_HTML = """
<h2>Figures</h2>
<p><img src="outputs/updown/updown_contrast.png" width="480"></p>
<p class="cap">Figure 1. Behaviour and cortical drift, each animal aligned to its own
conditioning onset. Left: corrected H-reflex amplitude rises in up-conditioned animals
(red) and falls in down-conditioned animals (blue). Right: cortical drift shows no
dependence on conditioning direction.</p>
<p><img src="outputs/coupling/coupling_group.png" width="430"></p>
<p class="cap">Figure 2. Cortex-to-reflex coupling over time. Cross-validated R2 within
five-day blocks, after removal of stimulus and background. Coupling exceeds the
within-block shuffle null in every animal.</p>
<p><img src="outputs/verify/verification.png" width="480"></p>
<p class="cap">Figure 3. Left: the conservative within-block estimate against the earlier
global procedure. Right: correlation between cortical and muscle band power; values near
zero above 100 Hz argue against muscle contamination.</p>
<p><img src="outputs/scaling/scaling.png" width="480"></p>
<p class="cap">Figure 4. Cortical coupling against behavioural change. Animals that
learned more show a larger increase in coupling (r = +0.64); the two animals that failed
to reach criterion do not.</p>
"""

_UNUSED = [
    ("outputs/updown/updown_contrast.png",
     "Figure 1. Behaviour and cortical drift, each animal aligned to its own conditioning "
     "onset. Left: corrected H-reflex amplitude rises in up-conditioned animals (red) and "
     "falls in down-conditioned animals (blue). Right: cortical drift shows no dependence "
     "on conditioning direction."),
    ("outputs/coupling/coupling_group.png",
     "Figure 2. Cortex-to-reflex coupling over time. Cross-validated R² within five-day "
     "blocks, after removal of stimulus and background. Coupling exceeds the within-block "
     "shuffle null in every animal."),
    ("outputs/verify/verification.png",
     "Figure 3. Left: the conservative within-block estimate against the earlier global "
     "procedure. Right: correlation between cortical and muscle band power; values near "
     "zero above 100 Hz argue against muscle contamination."),
    ("outputs/scaling/scaling.png",
     "Figure 4. Cortical coupling against behavioural change. Animals that learned more "
     "show a larger increase in coupling (r = +0.64); the two animals that failed to reach "
     "criterion do not."),
]


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    W, H, MARGIN = 595, 842, 54
    mediabox = fitz.Rect(0, 0, W, H)
    where = fitz.Rect(MARGIN, MARGIN, W - MARGIN, H - MARGIN)

    writer = fitz.DocumentWriter(str(OUT))
    arch = fitz.Archive(str(ROOT))
    for html in (BODY, BODY2, FIG_HTML):
        story = fitz.Story(html=html, user_css=CSS, archive=arch)
        more = True
        while more:
            dev = writer.begin_page(mediabox)
            more, _ = story.place(where)
            story.draw(dev)
            writer.end_page()
    writer.close()
    d = fitz.open(str(OUT))
    print(f"wrote {OUT}  ({d.page_count} pages)")


if __name__ == "__main__":
    main()
