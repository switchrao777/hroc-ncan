# Talk script — HROC_Weekly_Update.pptx (10 slides, ~10 min)

Say the **bold line**, then the sentences under it. Don't read the slide.

**The one line to survive on:**
> "The cortical effect is small, but it shows up in 99 of 101 blocks, in every animal.
> A small effect that appears every single time isn't noise."

**Three numbers to memorise:** 99/101 · p = 2×10⁻²⁷ · r = +0.64

---

## 1 — Title
> **"Good week. Four things you asked for, all four done."**
>
> "The headline is that the cortical effect is small in size but extremely consistent —
> above the null in 99 of 101 five-day blocks, in every animal. I'll also show you one
> number I had to revise down after you asked me to check it."

*Sets the tone: confident, and flags the correction up front so it's not a surprise.*

---

## 2 — Four things you asked for
> **"Quick map of where we got to."**
>
> "Partition the variance — done, next slide. Re-check the 0.35 — done, and the number
> moved. Test for crosstalk using your correlation method — done, and it's clean. And
> whether the effect scales with how much each animal learned — done, and that one is
> the most promising thing we have."

*20 seconds. It's a roadmap, not a slide to dwell on.*

---

## 3 — The variance partition
> **"You asked what each factor explains. Here it is."**
>
> "Stimulus dominates at 47%. Background is 1%. Cortex on its own is 21% — but most of
> that overlaps with stimulus, because the stimulus drives both the cortical evoked
> response and the reflex. Once stimulus and background are already in the model,
> cortex adds about 2% uniquely. And roughly half is still unexplained."

**If he asks why they don't sum:** "That's exactly the shared variance you flagged in
the meeting — cortex and stimulus aren't independent, so you can't just add them."

---

## 4 — THE HEADLINE (slow down here)
> **"This is the number I actually want you to take away."**
>
> "Instead of judging the effect by its size alone, ask how *often* it's there. For
> every five-day block we test cortex against a shuffle of that block's own labels. It
> beats the shuffle in 99 of 101 blocks, across all five animals. A sign test gives p
> of two times ten to the minus twenty-seven."
>
> "So the effect is small — but it is almost never absent. And a small effect that
> shows up every time, in every animal, is not noise."

*This is your strongest slide. Pause after the p-value. Let the per-animal row
(9/9, 35/35, 15/17, 20/20, 20/20) do the rest.*

---

## 5 — The correction
> **"You asked whether I'd removed the stimulus properly. I hadn't."**
>
> "I was removing stimulus and background across all trials at once, then measuring
> cortex block by block. If the stimulus–reflex relationship shifts between blocks,
> that leaves stimulus variance behind — and cortex tracks stimulus. So the number was
> inflated."
>
> "Doing it inside each block gives 0.04. That's what we'll quote from now on. The
> magnitude moved; the finding didn't — still above the null in every animal, and in
> 99 of 101 blocks."

*Say it plainly and move on. Don't apologise, don't linger — you found it because he
asked the right question, and that's the story.*

---

## 6 — Crosstalk
> **"Your test, and it comes back clean."**
>
> "You suggested correlating the cortical signal against the muscle signal to see how
> much coordination there is. Muscle artefact lives at high frequency, so that's where
> contamination would show. Above 100 hertz the correlation is plus 0.06 — essentially
> zero. The low bands are slightly negative. And cortex marginally leads muscle, which
> you said would be the acceptable direction."
>
> "So we don't think the ECoG is just reproducing the EMG."

---

## 7 — Scaling (the promising one)
> **"This was your idea and I think it's the best thing we have."**
>
> "The animals differ in how much they learned, and two of them failed outright —
> those become the built-in negative control. The correlation between learning and the
> *change* in coupling is plus 0.64. The two that succeeded gained coupling; the two
> that failed didn't."
>
> "With five animals it's not significant. But it's the right direction, and it's
> exactly the analysis more animals would power."

---

## 8 — The constraint
> **"One new finding, and it's a limit rather than a result."**
>
> "I went back through every animal's log using the reward criterion as a success
> readout. For up-conditioning, raising the bar means the rat is beating it. Animals 3
> and 4 had theirs raised — they learned. Animals 1 and 6 had theirs lowered — they
> struggled. And animal 12's cortical electrode was dead, under three microvolts."
>
> "So the up group is capped at two, permanently. There isn't another good
> up-conditioned animal in this dataset. The down group can still grow."

*This matters strategically — it's why slide 10 asks him a question.*

---

## 9 — Deliverables
> **"One more thing from this week."**
>
> "We put everything behind a single page so the code, the write-up and the slides
> stay in sync and are easy to hand to anyone. The repository has the whole pipeline —
> one command per animal, reproducible end to end. There's a six-page write-up
> formatted as a handout with the figures and the real numbers, and the citations
> checked against the actual papers. And the decks live there too."
>
> "Two blanks I deliberately left: Theresa's surname, and what Tarun and I should be
> listed as. I didn't want to guess on a write-up."

---

## 10 — Plan, and the question
> **"Between now and the 21st."**
>
> "Download and process the remaining animals — the five down ones plus the two failed
> up animals, which are useful as negative controls. That takes us from five to about
> twelve, and it's what powers the scaling correlation. Then re-run everything, build
> the presentation for your group, and preview it with you first."
>
> **"One question for you: given the up group is capped at two, should we build the
> paper around the scaling analysis rather than the up-versus-down contrast?"**

*Stop there. That question is the most valuable thing you can get out of the meeting.*

---

## If he pushes

**"Is 2% unique variance enough to publish?"**
> "On magnitude alone, it's modest. What makes it a result is the reliability — 99 of
> 101 blocks, every animal, after four independent controls. And it's single-trial
> physiology in an awake behaving animal, where that's a normal effect size."

**"Why should I believe the within-block design?"**
> "Because slow drift moves the training and test trials together, so it cancels.
> Drift can shift a mean; it can't manufacture trial-by-trial predictive structure
> inside a five-day window. That's the whole reason we switched to this question."

**"What else could produce it?"**
> "We've ruled out stimulus intensity, motoneuron excitability, recording drift, and
> muscle crosstalk. The one I'd still like to close is which frequency bands carry it —
> that's next."

**"How many animals do you need?"**
> "Ten would settle the scaling result. We can get the down group there. The up group
> can't grow, which is why I'm asking about the framing."

**"Is the negative worth reporting?"**
> "I think so. The obvious analysis produces a convincing-looking result that three
> controls reject. Anyone applying these methods to long chronic recordings will hit
> the same thing."
