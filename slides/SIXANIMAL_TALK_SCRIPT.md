# Talk script — Six-Animal Update (plain language)

For `slides/HROC_SixAnimal_Update.pptx`. Say the **bold line**, then the sentences
under it. ~12 minutes plus discussion.

---

## THE THREE THINGS TO REMEMBER
If you remember nothing else, these carry the whole talk:

1. **"Conditioning worked in both directions."** Up animals' reflexes got bigger,
   down animals' got smaller — after controlling for stimulus strength and muscle
   tone.
2. **"The drift result was a dead end, and we proved it three different ways."**
3. **"So we asked a better question, and got a real answer: the brain predicts the
   reflex trial by trial."**

**Numbers to know:** coupling R² up to **0.35** vs a null of **0**. Group behaviour
difference **+72 points**. Six animals, **2.7 million trials**.

---

## Slide 1 — Title
> "Since last time we doubled the dataset to six animals, including three
> up-conditioned. We built every control you asked for. And by changing the question
> we ended up with a positive result. I'll go in that order."

---

## Slide 2 — Your four asks
> "First, the four things you asked for last time — all four are done."

- **Randomised order:** "You said take the same data in a random order, it shouldn't
  drift. We did. It doesn't — the null is basically zero in every animal. So the
  drift metric isn't something baked into the numbers."
- **Pre-stimulus background:** "You said the reflex depends on how excited the
  motor pool already is. We pulled the 20 milliseconds right before each stimulus and
  it's now a control in every analysis."
- **Last 10 baseline days:** "You said only the last 10 days before training are
  stable. You were right — you can see it in the data. That's our reference now."
- **A strong up animal:** "Animal 12 was weak, so we went looking. Found two good
  ones."

---

## Slide 3 — The dataset, and how we found the up animals
> "Six animals now, 2.7 million trials, three down and three up."

**The trick worth explaining (he'll like this):**
> "We didn't want to download 40 gigabytes hunting for a good up animal. So we read
> just the log files, which are tiny. The reward criterion tells you who succeeded —
> whoever set it up raises the bar when the rat is beating it, and lowers it when the
> rat is struggling. Animal 4's bar went from 150 up to 220, and animal 3's from 90
> to 190. Those two genuinely learned. Animals 1 and 6 had the bar lowered, so they
> failed. Then we only downloaded the good ones."

---

## Slide 4 — Behaviour works, both directions
> "Start with behaviour, because it's the check that has to pass before anything else
> counts."

> "Every animal is lined up to its own training start day. Red is up-conditioned,
> blue is down. Red goes up, blue goes down. That's a 72-point difference between the
> groups. Animals 9, 11 and 3 clear your 20 percent bar."

**Say this part clearly:**
> "And this is after we take out stimulus strength and muscle background. So it isn't
> the stimulus creeping up — it's real learning."

---

## Slide 5 — The drift question, answered
> "Now the cortical drift, and I think we can actually close this one."

**The logic, in one line:**
> "Electrode drift doesn't care whether you trained the rat up or down. Learning does.
> So if the drift were learning, up and down animals would have to look different."

> "They don't — 22 versus 35, not significant. Put that together with the sham test
> failing in five of six animals, and your randomised-order test passing, and three
> independent controls all say the same thing: the drift is the recording slowly
> changing over weeks, not the brain learning."

**Don't apologise for this.** It's a clean answer, and it's why the next slide exists.

---

## Slide 6 — Why we changed the question
> "Rather than keep fighting that confound, we changed what we were asking."

- Old: *"Did the average brain state move over weeks?"*
- New: ***"Can the brain signal predict the reflex on a trial-by-trial basis?"***

**The key idea — say it slowly, it's the cleverest part of the talk:**
> "We train and test the prediction inside a single five-day block. Slow drift moves
> the training data and the test data together, so it cancels out. Drift simply can't
> create the thing we're measuring. The confound that killed the last analysis is
> mathematically unable to fake this one."

Plus: "we take out stimulus and muscle tone first, and we compare against a shuffled
version of the same block."

---

## Slide 7 — The positive result
> "And here it is. The brain signal predicts the reflex, trial by trial, in every
> single animal."

> "R-squared reaches 0.35, against a shuffle null of essentially zero. Plain English:
> if you show the model the cortical activity on a given trial, it can tell you
> something real about how big that reflex is going to be — and that isn't stimulus
> strength, isn't muscle tone, and isn't drift."

**Be upfront about the limit:**
> "What I can't tell you yet is whether that coupling gets *stronger* with training.
> That's a power problem — five animals isn't enough. Animal 11 shows a big increase,
> but it's not consistent yet."

---

## Slide 8 — Is it really cortical?
> "The obvious objection is that the ECoG electrode is just picking up muscle
> activity, since both are recorded at the same time. So we tested that."

> "We looked at cortical activity measured entirely *before* the stimulus — it can't
> contain a muscle response that hasn't happened yet. It does predict the reflex, but
> weakly."

**The bit he'll appreciate:**
> "And interestingly, pre-stimulus *muscle* activity predicts better than pre-stimulus
> cortex — which is exactly what you told us would happen with motoneuron pool
> excitability. That's a good sign our measurement is working."

---

## Slide 9 — Honest scorecard
> "So three findings. Behaviour is solid. The coupling result is real and it's our
> positive finding. And the drift-equals-learning question is answered no — which is
> a useful negative, not a failure."

---

## Slide 10 — Plan for the last few weeks
> "Four things. Add the remaining down animals — 7, 8, 13, 14, 15 are already scanned
> and ready, and going from five to ten animals is what settles whether the coupling
> changes with training. Finish the crosstalk test. Look at which frequency bands
> carry the signal. And start writing."

> "The paper is: conditioning works both directions, cortex predicts the reflex trial
> by trial, plus the control methodology showing why the obvious analysis fails."

---

## Slide 11 — Questions for him
Lead with these two:
1. **"Is the coupling result interesting enough to build the paper around?"**
2. **"How would you rule out the ECoG picking up muscle?"**

Then: which animals next, and is the negative worth publishing as a caution.

---

## IF HE PUSHES — plain answers

**"What does R-squared 0.35 actually mean?"**
> "Of everything that makes the reflex vary from trial to trial, the cortical signal
> accounts for about a third of it in the best blocks. It's not the whole story, but
> it's a lot more than nothing — and the shuffled control gives zero."

**"Couldn't the coupling just be the electrode picking up muscle?"**
> "That's the main thing left to rule out and I don't want to overclaim. The
> pre-stimulus test argues against it, but the proper test is showing which frequency
> bands carry it — muscle artefact lives at high frequency. That's next."

**"Why did the drift analysis fail?"**
> "Because in one animal, learning and slow electrode change both happen gradually
> over weeks. There's no way to tell them apart mathematically. That's not a data
> problem, it's a study-design limit — which is exactly why the trial-by-trial version
> works."

**"Is five animals enough?"**
> "For the coupling existing, yes — it's in every animal. For whether it *changes*
> with training, no. That's why the next five animals matter."

**"What about animal 12?"**
> "We dropped it from cortical analyses. Its pre-stimulus cortical signal is 2.8
> microvolts versus 106 to 128 in the others — that electrode was effectively dead.
> Its weak up-conditioning was a recording failure, not the animal."
