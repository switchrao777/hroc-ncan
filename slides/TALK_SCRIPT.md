# Presentation script — NCAN group talk

**Deck:** `HROC_Team_Presentation.pptx` · 34 slides · about 40 minutes
**Presenters:** Suchith Rao and Tarun Senthil

---

## Before you start

**The one sentence the talk is built around:**
> "The brain carries a small but very reliable signal about the size of each individual reflex — and getting to that took throwing away a result that looked better."

**Five numbers to know cold:**
| | |
|---|---|
| 2.7 million | trials decoded |
| 99 of 101 | five-day windows where the real data beat its own shuffle |
| t(4) = 3.81, p = 0.019 | counting the animal as the unit of analysis |
| 2% | variance the brain adds uniquely, once stimulus and muscle tone are known |
| r = +0.71 | between how much an animal learned and how much its coupling changed |

**Suggested split**
- **Suchith:** slides 1–9 (question and data), 16–26 (results), 31–34 (close)
- **Tarun:** slides 10–15 (how it was built), 27–30 (what's next and what we'd write)

Hand over explicitly — "Tarun's going to take you through how we actually built it" — so the room tracks the change.

**Three places to slow down:** slide 7 (the decoder), slide 11 (the autoencoder), slide 19 (the within-window idea). Everything else can move.

---


## Slide 1 — Title   [SUCHITH]

Thanks for having us. We're the machine-learning side of this project. Over the summer we took the archived paired EMG and ECoG recordings and asked one question: on any given trial, does the brain signal tell us anything about how big the reflex is going to be? I'll walk through what the data is, how we built the analysis, what we found — including one thing that didn't work — and where we think it goes.


## Slide 2 — Roadmap   [SUCHITH]

Five parts. What the question is and what was already known. What the data actually is. How we built the analysis, including the model and the workflow, since I gather that part is of interest. What we found, which includes one result that didn't survive. And where we think it goes from here.


## Slide 3 — What the animals are doing   [SUCHITH]

For anyone not close to this work: a small shock to the leg nerve produces a reflex in the soleus. The rat is rewarded when that reflex is bigger, or smaller, than a threshold. Over weeks it shifts, and twenty percent counts as success. What's already known from Chad Boulay's paper is that cortical activity influences reflex size. Our question is whether you can see that on a single trial, and whether the relationship itself changes with learning.


## Slide 4 — Why bring machine learning to this   [SUCHITH]

Why bring machine learning to this at all. The usual approach is to decide in advance which features of the trace might matter and measure those — but whatever you didn't think of, you don't measure. Instead we let a network learn its own description of each trace with no labels, then test what it can predict. The precedent is BrainBERT, out of MIT and used widely for human intracranial work: learn a general representation of neural signal first, then apply it downstream. Ours is a much smaller model because we have one channel and a thirty millisecond window rather than a full array.


## Slide 5 — What a single trial looks like   [SUCHITH]

Orientation before anything else. Every shock gives one trial — thirty milliseconds at five kilohertz, two channels recorded simultaneously. The spike at zero is the stimulus artifact. The bump at two to four milliseconds is the M-wave, the nerve firing the muscle directly. The bump at six to nine is the H-reflex, which went down to the spinal cord and back. That's the one conditioning changes. This particular figure is the average of two hundred eighty thousand trials from one animal.


## Slide 6 — First problem: the archive would not decode   [SUCHITH]

First problem, and it took a while. We were given the tables and a decoder script that documented the byte order as big-endian. Decoded that way every trial is noise — no M-wave, no reflex. The files are actually little-endian. It's one flag. But the reason we trusted the fix wasn't that the output looked plausible; it's that the M-wave and H-reflex landed at exactly the latencies the experimenter had typed into the log back in 2006 — MR interval two to four, HR interval six to nine. The data confirmed the notes and the notes confirmed the data.


## Slide 7 — The same 8,000 trials, decoded two ways   [SUCHITH]

This is what it actually looked like. Left: decoded the way the documentation says, averaged over eight thousand trials. Amplitudes in the tens of thousands of microvolts, which is ten times anything physiological, and no structure at all. Right: the identical file with the byte order flipped. Stimulus artifact, then the M-wave in the orange band, then the H-reflex in the blue band. This is real data, not an illustration — and it's the moment the project actually started.


## Slide 8 — Six animals, 2.7 million trials   [SUCHITH]

Six animals, three trained down and three up, forty-five to two hundred ten days each. Worth explaining how we chose them, because it saved us a lot of time. The log files are a few hundred kilobytes; the signal data is four gigabytes an animal. The experimenter raises the reward threshold whenever the rat starts beating it — so the threshold history is a written record of how the animal was doing. We read only the logs, then downloaded signal data for the ones that had learned. We also dropped animal twelve: its pre-stimulus cortical signal is under three microvolts against a hundred-plus in the others, so that electrode was dead.


## Slide 9 — Who is in the study   [SUCHITH]

Here's the roster. Six animals, three trained to increase the reflex and three to decrease it, with trial counts from two hundred eighty thousand up to six hundred thirty thousand. Three met the twenty percent criterion. Two changed less than that — and those two turn out to be useful, because they act as a negative control later. One had a failed electrode and is excluded from anything cortical.


## Slide 10 — The pipeline, end to end   [TARUN]

This is the whole data flow. Recover the old tables into a local database. Decode each trial into two channels of microvolts. Store as Zarr, which is a chunked array format that lets us read two point seven million trials without loading them into memory. Measure the physiology. Learn the representation. Then test it against controls. Four gigabytes in per animal, about three hundred megabytes out, and once it's set up it's two commands per animal.


## Slide 11 — What the model actually is   [TARUN]

This is the model, and it's simpler than it sounds. On the left, one trial of brain signal — a hundred and fifty numbers. The encoder squeezes that down to forty-eight numbers. The decoder tries to rebuild the original from just those forty-eight. We train it by penalising the difference between the rebuild and the original. The important part is the bottleneck: to rebuild the trace from only forty-eight numbers, those numbers have to capture the trace's real structure rather than its noise. And crucially, nobody tells it what to look for. We never show it an H-reflex, a label, or a training phase. So the forty-eight numbers are whatever the signal's own structure demands, not the features we assumed mattered. After training we freeze it and use it purely as a description.


## Slide 12 — Training it, and the one trap we avoided   [TARUN]

Training details. Six hundred thousand trials pooled across five animals, twelve passes, about four minutes on a laptop GPU — these are small models. Reconstruction error halves and flattens. The trap we had to avoid: if you pool animals naively, the model learns to tell the animals apart, because they have different electrodes and different amplitudes. That's a recording artefact wearing a biology costume. So we standardise each animal separately before pooling. And the reason we train one model across all animals rather than one each: separate models would describe each brain in its own private vocabulary and you could never compare them. One shared model means a given pattern means the same thing in animal three as in animal eleven — which is what makes the group comparisons later legitimate.


## Slide 13 — Tech stack and daily workflow   [TARUN]

The stack, in case it's useful. MariaDB for the archives, Zarr and NumPy for the arrays, PyTorch for the model running on Apple Silicon, scikit-learn and SciPy for the statistics, and matplotlib for figures. All Python, all open source, nothing exotic. Day to day the loop was: read the animal's log, load it, convert, look at the averaged trace to check the decode, run the analyses, commit the figures. Every figure in this talk regenerates from a single command — none of them were hand-edited, which matters when a number changes and six figures have to change with it.


## Slide 14 — How the summer actually went   [TARUN]

Roughly how the summer went, because the shape of it matters. Two weeks reverse-engineering the format. Two building the converter and validating one animal. Two training the model and getting first results, which looked good. Then week seven, when the controls failed and we had to rethink the question — that was the most useful week of the project. It cost us the result we thought we had and produced the design the current finding rests on. Then the new design and five more animals.


## Slide 15 — Why reflex size alone tells you nothing   [TARUN]

This slide matters because getting it wrong cost us a result. A bigger shock makes a bigger reflex with no learning involved, and across these recordings the delivered stimulus roughly quadrupled. Early on that made one of our findings come out backwards. The fix is that the M-wave sits in the same trace and reflects only the stimulus, so it's a per-trial receipt. Dr Carp added the second one: the reflex also depends on how active the muscle already was, so we measure the twenty milliseconds before each shock. Every number from here on has both corrections applied.


## Slide 16 — Conditioning works, in both directions   [SUCHITH]

We lead with behaviour because it's the check that has to pass before anything else counts. Each animal is aligned to its own training start day. Up-trained animals rise, down-trained fall. Three of five clear the twenty percent criterion in the trained direction, and the two that don't come back later as a negative control. And again — this is after removing stimulus and background, so it isn't the stimulus creeping up.


## Slide 17 — Two things change slowly over the same weeks   [SUCHITH]

Now the hard part, and I want to be direct about it. Two things change slowly over the same weeks: the animal's learning, and the chronically implanted electrode. On the left, both curves go up. On the right is what the recording actually gives you — one curve, with no way to split it. Inside a single animal both are smooth functions of time, so no amount of analysis separates them. That's a limitation of the design rather than the data, and it shaped everything we did next.


## Slide 18 — Our first approach did not survive its controls   [SUCHITH]

Our first approach was the obvious one: measure how far the average brain state moves across training. It does move, and it looked convincing. But three tests say that movement is the recording rather than the animal. If you take baseline-only data and pretend half of it was training, it moves just as much, in five of six animals. If you shuffle which trial belongs to which day, nothing moves — so the measure itself is fine. And electrode drift doesn't care which direction you trained the animal, and there's no difference between the up and down groups. Two of those three were Dr Carp's suggestions, and they changed our conclusion. I'd rather show you this than not.


## Slide 19 — So we asked a question drift cannot fake   [SUCHITH]

So rather than keep fighting that confound, we changed the question. Instead of asking whether the average moved, we ask whether the brain can predict this particular trial's reflex. Here's the design, and it's the part I'd most like your reaction to. The top bar is the whole recording, with colour showing the electrode slowly changing. We chop it into five-day windows. Inside one window we train on four fifths of the trials and test on the held-out fifth. Within five days the electrode is essentially fixed, and whatever drift remains moves the training and test trials together, so it cancels. Drift can move an average. It cannot invent a trial-by-trial relationship inside five days.


## Slide 20 — And each window is judged against itself   [SUCHITH]

And we don't just look at whether the prediction is good in absolute terms, because there's no natural yardstick for that. Instead each window is judged against itself: take the same trials, shuffle which reflex goes with which brain signal, and run the identical analysis. Same numbers, wrong pairings, so any real relationship is destroyed. If the real version doesn't beat the shuffled one, there was nothing there. We do that in all hundred and one windows.


## Slide 21 — The brain does carry a signal about the reflex   [SUCHITH]

And here's the finding. In ninety-nine of a hundred and one windows the real data beat its own shuffled version, and it holds in all five animals. On the statistics I want to be careful. Counting each window as independent would badly overstate it, because windows within an animal share an electrode and an animal. Counting the animal as the unit of analysis gives t of three point eight one on four degrees of freedom, p equals nought point nought one nine. So the effect is small in size but almost never absent — and I'd argue reliability is the more meaningful property here.


## Slide 22 — How much does the brain actually explain?   [SUCHITH]

Dr Carp asked us to split the variance up, and this is the answer. The stimulus dominates at forty-seven percent. Background is one. About half is still unexplained, which is normal for single-trial physiology. The brain on its own looks like twenty-one percent, but almost all of that overlaps with the stimulus, because the stimulus drives both the cortical response and the reflex. Only the part that survives once the other two are in the model — about two percent — counts as a genuine cortical contribution. That's a small number and I don't want to oversell it.


## Slide 23 — All five animals, all three measures   [SUCHITH]

This is everything on one slide. On the left, behaviour: every animal moved in the direction it was trained, three of them past the twenty percent line. In the middle, the prediction score against its shuffled control — real in blue, shuffled in grey — and the real bar is higher in every animal. On the right, how many five-day windows beat their own shuffle: nine of nine, fifteen of seventeen, and three animals at a hundred percent. Ninety-nine of a hundred and one overall.


## Slide 24 — Everything we tried to kill it with   [SUCHITH]

This is everything we tried to kill the result with. Five it survives, two it fails, and the two failures are what told us the average-state approach was the wrong question. Most of these were suggested by Dr Carp. If anyone here can think of something we haven't tried, that's genuinely the most useful thing I could take away from this meeting.


## Slide 25 — Is the brain electrode just picking up muscle?   [SUCHITH]

The obvious objection is that both channels are recorded simultaneously, so maybe the cortical electrode is just picking up muscle. Dr Carp suggested the test: correlate cortical power against muscle power and see how much they move together. Muscle artefact lives at high frequency, so that's where contamination would show. Above a hundred hertz the correlation is plus nought point nought six — essentially zero. The low bands are slightly negative. And the cortical signal marginally leads the muscle, which is the acceptable direction. So we don't think this is contamination, though I'd welcome a better test.


## Slide 26 — Does it scale with how much they learned?   [SUCHITH]

This is the thread I think is most promising, and it was Dr Carp's suggestion. Animals differ in how much they learned, and two failed outright — those become a built-in negative control. The correlation between how much an animal learned and how much its cortical coupling changed is plus nought point seven one, and the two that failed show no increase. With five animals that's a direction rather than a result. Five more animals are downloaded and ready to process, and that's what would settle it.


## Slide 27 — The metadata may be a measurement   [TARUN]

One new thread, which came out of talking with Dr Carp. The reward threshold is adjusted by hand, day by day — raised when the rat is beating the task, lowered when it's struggling. That's effectively a staircase procedure, and it's a record of how hard the task was for that animal, written down independently of anything we measure from the electrodes. Right now our scaling result correlates two things measured from the same electrodes, which share noise. If cortical coupling instead tracks a behavioural record kept by hand at the time, that's a much harder result to dismiss. We'd like to build that next.


## Slide 28 — Three things worth writing up   [TARUN]

If this becomes a paper, we think there are three pieces. The method — a reproducible pipeline that recovers a twenty-year-old archive and learns a representation from it on a laptop, which is useful to anyone with old chronic recordings on a shelf. The finding — cortical activity carries a small but highly reliable single-trial signal about reflex size, which extends Chad's work from a population relationship to a single-trial one. And the warning — the intuitive drift analysis produces a convincing result that three controls reject, and we'd want to save the next group from spending months on it. We'd aim at a machine-learning venue, framed as an extension of the existing cortical-spinal work.


## Slide 29 — Where a single-trial cortical readout could help   [TARUN]

Why this might matter, and I want to be careful not to oversell. If cortex predicts the reflex before the fact, conditioning protocols could in principle adapt trial by trial rather than day by day. Roughly a third of animals, and of people, don't respond to conditioning — a cortical readout might show why, early. And reflex conditioning is already used clinically after spinal cord injury, so any handle on the cortical side is a handle on individualising it. All three depend on the effect being bigger and more reliable than what we can currently show. We're not there. But that's the direction that makes it worth getting there.


## Slide 30 — What happens next   [TARUN]

What happens next. Five more animals are downloaded and ready, which takes us from five to about ten and is what powers the scaling test. Then frequency-resolved coupling, to see which bands carry the information — that sharpens both the finding and the contamination argument. The reward-criterion measure as an independent behavioural record. And then writing it up.


## Slide 31 — What we can say   [SUCHITH]

To summarise. Conditioning reproduces in both directions with full stimulus control — that's solid. Cortex carries a small single-trial signal about reflex size that beats its own shuffled control in ninety-nine of a hundred and one windows and in every animal — that's real, and small. And the average-state drift analysis is a useful negative: it looks convincing and three controls reject it. Every number is corrected for stimulus and muscle activity.


## Slide 32 — What we know we haven't settled   [SUCHITH]

And the things we know we haven't settled. Whether the coupling grows with learning — the correlation points the right way but five animals can't settle it, and five more are processed and waiting. Which frequencies carry the signal. Whether two percent of variance is biologically meaningful, which is honestly a question for this room more than for us. And what else could produce it that we haven't excluded — we'd genuinely like to know what we're missing.


## Slide 33 — Code, data pipeline, figures and write-up   [SUCHITH]

Everything is public. There's a project page with the findings and figures, the repository with the full pipeline — two commands per animal and it runs end to end — and a six-page write-up. The repository has every script, the trained encoder, all the figures, per-animal results, a starter notebook and setup instructions. No raw recordings; those stay with NCAN. If anyone wants to run it on their own data, it should be straightforward.


## Slide 34 — Thank you   [SUCHITH]

Thank you. And genuinely — the sham control, the randomised order test and the pre-stimulus covariate were all Dr Carp's suggestions, and each one changed what this project concluded. Happy to take questions.


---

## Questions you should expect

**"Is 2% of variance actually meaningful?"**
> "On size alone, modest. What makes it a result is that it's there in every animal and in 99 of 101 windows, after four separate controls. And this is single-trial physiology in an awake animal, where that's a normal effect size. Whether it's biologically meaningful is genuinely a question we'd like your view on."

**"How do I know the within-window design really removes drift?"**
> "Because drift moves the training trials and the test trials together, so it cancels in the cross-validation. Drift can shift an average — it can't create a trial-by-trial relationship inside five days. And the sham control confirms it: on baseline-only data, where nothing happened, the within-window analysis gives essentially zero."

**"Why is your R² so much lower than what you reported earlier?"**
> "Because Dr. Carp asked us to check whether we'd removed the stimulus properly, and we hadn't. We were removing it across all trials at once and then measuring within windows, which leaves stimulus variance behind — and the brain signal tracks the stimulus. Doing it inside each window gives 0.037. That's the number we stand behind."

**"Couldn't the cortical electrode just be picking up muscle?"**
> "That's the first thing we checked. Muscle artefact lives above 100 Hz, and up there the correlation between the cortical and muscle signals is +0.06 — essentially zero. The low bands are slightly negative, and the cortical signal marginally leads the muscle rather than following it."

**"Why an autoencoder rather than just measuring features?"**
> "Because measuring features means deciding in advance what matters. The autoencoder learns its own description with no labels, so it isn't limited to what we thought to look for. It also gives every animal the same vocabulary, which is what lets us compare across them."

**"Why only five animals?"**
> "Five are fully processed. Five more are downloaded and waiting — the pipeline is two commands per animal now, so that's days rather than weeks. Ten is what would settle whether the coupling grows with learning."

**"What would change your mind?"**
> "If the coupling didn't survive in the next five animals, or if someone identified a confound we haven't controlled. That second one is the most useful thing we could take away from today."

**If you don't know an answer:**
> "I don't want to guess at that — let me check and come back to you."
That answer costs nothing and is better than improvising in front of this group.

---

## Timing

| Part | Slides | Target |
|---|---|---|
| Question and data | 1–9 | 10 min |
| How we built it | 10–15 | 9 min |
| Results | 16–26 | 14 min |
| Where it goes and close | 27–34 | 7 min |

If you're running long, compress slides 13 (tech stack) and 14 (timeline) — they're context, not argument. Never compress 7, 11, 19, or 21.
