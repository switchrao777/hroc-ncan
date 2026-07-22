# Talk Notes — HROC Four-Animal Findings Deck

For `slides/HROC_Findings_4Animals.pptx`. One section per slide: what's on it,
what to say, and what to answer if pushed. Aim ~12-15 min plus discussion.

**The one line to survive on if you blank:**
> "We ran the control that could have killed our own result, and in three of four
> animals it did. That's why I trust the one that survived, and it tells us exactly
> which experiment to run next."

**Three numbers to memorize:**
- Animal 9 null control: **sham 42 vs real 17** (fails)
- Animal 10 null control: **real 30.6 vs sham 6.7** (passes, 4.6x)
- Behaviour: **H/M falls to ~0.6** in animals 9 and 11 (down-conditioning worked)

---

## Slide 1 — Title: "Four animals in. What's real, and what isn't."
**Say:** "Since last time we went from one animal to four, and we ran the null
control you suggested. Headline: the behaviour is solid, but the cortical drift did
not survive its own control. I'll show you what happened and what I think it means."

**Tone:** Confident, not apologetic. You are delivering rigor, not bad news.

---

## Slide 2 — What changed
**On it:** three items — 4 animals processed, per-day analysis, the null control.
~1.6 million trials decoded.

**Say:** "Three things changed. We went to four animals and confirmed their
conditioning directions straight from the experimenters' logs. We got timestamps in,
so we can measure drift per day instead of per phase. And we ran your null control,
which turned out to be the most important thing we did."

**If asked how directions were determined:** the type-15 log entries — "Start HRdown"
for 9/10/11, "Started HRup conditioning" for 12. Read from the logs, not assumed.

---

## Slide 3 — Plain English (H/M, drift, null control)
**Say:** "Quick vocabulary. H over M is the reflex normalised by stimulus strength,
which is the only valid way to measure it. Drift is how far the cortical
representation moved from baseline. And the null control is the sham test."

**Don't linger** — 20 seconds, let them scan it. It exists so the later slides land.

**Why H/M matters (if asked):** raw H depends steeply on how hard you stimulate. Our
M-wave drifts substantially over weeks, so raw H would be measuring stimulus, not
learning. Every reflex number in this deck is H/M.

---

## Slide 4 — Result 1: Down-conditioning worked (Animal 11)
**On it:** animal 11's H/M learning curve, flat at baseline then falling.

**Say:** "Start with what works. Animal 11: H over M is flat around 0.87 through
baseline, then drops steadily to about 0.60 once conditioning starts. Animal 9 does
the same thing. This is the textbook curve and it's the most solid result we have."

**This is your foundation.** Lead with it so the null-control discussion doesn't read
as "nothing worked."

**If asked about animals 10 and 12:** 10 has a 40-day recording gap that splits it
into two regimes and complicates the readout; 12's up-conditioning was a weak
responder. Both are on the scorecard slide.

---

## Slide 5 — The null control: what it is and why it matters
**Say:** "This is the test you suggested and it was the right call. Take baseline-only
data, before any conditioning. Pretend the first part is baseline and the rest is
conditioning. Run the identical analysis. Nothing happened in that data, so an honest
method must report about zero drift. It doesn't. In three of four animals the sham
drifts as much as the real thing."

**The point to land:** most of what we were calling a cortical effect is slow drift in
the recording itself over weeks, not learning.

---

## Slide 6 — The figure (Animal 9 fails)
**On it:** red = sham on baseline-only data, purple = real conditioning. They overlap.

**Say:** "Red is the fake experiment on baseline-only data. It climbs as high as the
purple real-conditioning line. And look at the purple line itself — it rises during
baseline and falls during the period when the animal was learning most. It runs
opposite to the behaviour, which is the giveaway that it isn't tracking conditioning."

**That opposite-direction detail is your strongest evidence** that the drift isn't a
learning signal. Point at it.

---

## Slide 7 — The scorecard (all four animals)
**On it:** table — animal, direction, behaviour, null control.

**Say:** "All four side by side. Behaviour is reproducible: down-conditioning works in
9 and 11. Animal 10 is complicated by the recording gap, animal 12's up-conditioning
is a weak responder. The cortical drift is the opposite story — only animal 10
survives the null control. That inconsistency is the finding."

**Key framing:** behaviour replicates, cortex doesn't. That contrast is the honest
summary of where we are.

---

## Slide 8 — Animal 10, the exception
**On it:** animal 10's null control — real 30.6 vs sham 6.7.

**Say:** "One animal bucks the trend. In animal 10 the real drift is about four and a
half times the sham, so the cortical change there isn't explained by recording drift.
That's worth chasing. But one out of four is a lead, not a result, and I don't want to
build a story on it yet."

**Why this matters (say it):** a pass means something *because* three others failed.
If everything passed, the metric would be suspect.

---

## Slide 9 — Why one animal can't settle this
**Say:** "In a single animal, conditioning and recording drift are both slow changes
over weeks. They're mathematically tangled, so no single-animal analysis can pull them
apart. What's solid is the pipeline, the behaviour, and the control methodology.
What's not solid is a conditioning-specific cortical effect, the up-versus-down
contrast, or pooling animals."

**This is the intellectual core.** It reframes the failures as a *design* limitation
rather than a biological answer — which sets up the next slide.

---

## Slide 10 — The bar: what would make a cortical claim believable
**On it:** five controls — null, M-wave, pre-stimulus, direction contrast, tracks behaviour.

**Say:** "This is the bar I want to hold us to. Five controls. We clearly pass the
M-wave one. The null control passes in only one animal. Pre-stimulus excitability
isn't built yet, we need a strong up-conditioned animal for the direction contrast,
and nothing yet tracks the behavioural curve. Clear all five and it's a real result."

**Say this out loud:** we haven't yet given the hypothesis a fair test — the decisive
design is the direction contrast, and we can't run it while our only up animal is a
weak responder.

---

## Slide 11 — The plan
**On it:** per-animal cleanup, pooled encoder, pre-stimulus control, chase animal 10,
get a strong up animal.

**Say:** "Clean up per animal — gaps and per-animal M/H windows. Retrain the encoder on
all animals instead of just animal 9. Add the pre-stimulus control. Chase animal 10.
And get a strongly conditioned up animal, which is the highest-value thing we can add.
We're deliberately not rushing a draft — better to clear the bar than publish a
confounded effect."

**Timeline if asked:** roughly 4-6 weeks to a definitive answer either way. A behaviour
plus methods paper is reachable in about 3 weeks regardless of how the cortical
question falls.

---

## Slide 12 — Discussion (four questions)
Hand it over. Don't read all four — lead with the two that matter:

1. **"Does the null-control result convince you the drift is recording, not learning?"**
2. **"Which animals in the drive were your strongest up-conditioning responders?"**
   ← *This is the most valuable question in the room. It decides whether the cortical
   paper is reachable. Do not leave without an answer.*

Then if there's time: is animal 10 worth chasing, and are the five controls the right bar.

---

## If Carp pushes — quick answers

- **"So the cortical effect isn't real?"** → "We've shown the naive version is
  confounded. We haven't yet run the design that can actually answer it, which is the
  up-versus-down contrast. That needs a well-conditioned up animal."
- **"Why did three fail and one pass?"** → "Could be genuine, could be that our
  per-animal cleanup isn't done — single encoder trained on animal 9, no per-animal
  M/H windows, recording gaps unhandled. All fixable, and that's the next work."
- **"Is this worth continuing?"** → "Yes, with a kill criterion: after per-animal
  cleanup, a pooled encoder, and about six animals with both directions well
  conditioned, if the direction contrast shows nothing then it isn't there, and we
  write the methods and behaviour paper."
- **"How much is publishable now?"** → "The pipeline, the behavioural quantification,
  and the control methodology — that's a real paper, roughly three weeks out. The
  cortical claim is not there yet."
- **"Electrode drift over months — isn't that expected?"** → "Yes, and that's exactly
  what we think we're seeing. Which is why the direction contrast is the way out:
  electrode drift doesn't care which direction you conditioned."
