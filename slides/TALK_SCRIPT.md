# Presentation script — NCAN group talk

**Deck:** `HROC_Team_Presentation.pptx` · 34 slides · about 40 minutes
**Presenters:** Suchith Rao and Tarun Senthil

---

## Before you start

**The sentence the talk is built around:**
> "The cortex carries a small but very reliable signal about the size of each individual reflex, and getting there meant setting aside a result that looked better."

**Five numbers to know**

| | |
|---|---|
| 2.7 million | trials decoded |
| 99 of 101 | five-day windows where the real data beat its own shuffle |
| t(4) = 3.81, p = 0.019 | the test, counting each animal once |
| 2% | reflex variation the brain explains on its own, once stimulus and background are accounted for |
| r = +0.64 | how much an animal learned vs how much its coupling changed (five animals) |

**Split:** Suchith 1–9, 16–26, 31–34 · Tarun 10–15, 27–30. Hand over out loud: "Tarun will take you through how we built it."

**Slow down on:** 4 (what Boulay et al. found), 11 (the model), 19 (the within-window idea), 26 (the scaling graph).

## How to present every graph

Carp got lost on graphs in the last meeting when the result came before the axes. On every graph slide, in this order:
1. **What the horizontal axis is.**
2. **What the vertical axis is.**
3. **What one dot, line or bar is**, and what the colours mean.
4. **Then** the result.

Point at the slide while you do it. The notes below already follow this order.

## Say it this way

| Instead of | Say |
|---|---|
| Zarr, chunked array format | "one file per animal, stored in small pieces so we can read any part without loading all of it" |
| MyISAM / MySQL tables | "the lab's 2006 database files" |
| big-endian / little-endian | "each number is stored as two bytes; the old script had their order backwards" |
| R² | "the fraction of the trial-to-trial variation in reflex size the brain signal predicts" |
| cross-validated | "always tested on trials the model did not see" |
| residualise | "remove the influence of" |
| permutation / shuffle null | "the same data with the pairings scrambled" |
| latent / embedding | "the model's 48-number summary" |
| RW | "the reward criterion: the value the reflex has to pass to earn a pellet" |
| shock | **stimulus** or **stimulation** |
| beat the criterion | **exceed** the criterion |
| dead electrode | **failed** electrode |

Avoid slang and colourful metaphors. Don't credit individual controls to Dr. Carp on stage. Thank him and Theresa Vaughan together at the end.

---

## Slide 1 — how big the reflex will be?   [SUCHITH]

Thanks for having us. Tarun and I are the machine-learning side of this project. We worked with recordings from rats trained to change a spinal reflex: EMG, the electrical signal from the leg muscle, and ECoG, the signal from an electrode on the surface of the brain over sensorimotor cortex, both recorded on every trial. There are 2.7 million trials. Our one question: on any single trial, does the brain signal tell you anything about how big the reflex is going to be? I'll go through the data, how we built the analysis, what we found, including one result that did not hold up, and where it goes next.

## Slide 2 — Roadmap   [SUCHITH]

Five parts: the question, the data, how we built it, what we found, and where it goes. About forty minutes. The results start around slide sixteen.

## Slide 3 — What the animals are doing   [SUCHITH]

For anyone not close to this work: a small electrical stimulus to the leg nerve produces a reflex in the soleus muscle. The rat is rewarded when that reflex is bigger, or smaller, than a threshold. Over weeks it shifts in the trained direction, and a twenty percent change counts as success. The long-term change is in the spinal cord itself.

## Slide 4 — What this builds on: Boulay, Chen & Wolpaw, 2015   [SUCHITH]

This project builds on a 2015 paper from this laboratory by Chad Boulay, Xiang Yang Chen and Jonathan Wolpaw. Their question was how ongoing activity in sensorimotor cortex affects the H-reflex. In forty-one awake rats they recorded ECoG over sensorimotor cortex together with soleus EMG and the H-reflex. The cortical signal fell into three frequency bands: mu-beta, low gamma and high gamma. Background muscle activity tracked cortical state, and H-reflex size related to the same bands in the opposite direction, but only once background EMG was included in the model. Their interpretation was that an activated cortex both excites the motoneurons and reduces the efficacy of the afferent input. So a cortical-spinal relationship was already established, from band power across many trials. Our question is whether it is visible on a single trial, and whether it changes as the animal learns.

## Slide 5 — Why bring machine learning to this   [SUCHITH]

Why bring machine learning to this at all. The usual approach is to decide in advance which features of the recording might matter and measure those — but whatever you didn't think of, you don't measure. Instead we let a network learn its own description of each trace with no labels, then test what it can predict. The precedent is BrainBERT, a model from MIT published at ICLR in 2023: it is trained on human intracranial recordings, learns a general representation of the signal first without labels, and is then applied to downstream questions. Ours is a much smaller model because we have one channel and a thirty-millisecond window rather than a full electrode array.

## Slide 6 — What a single trial looks like   [SUCHITH]

Orientation before anything else. Every stimulus produces one trial — thirty milliseconds at five kilohertz, recorded from a pair of EMG electrodes in the soleus muscle. The spike at zero is the stimulus artifact; it is clipped here so it doesn't dominate. The bump at two to four milliseconds is the M-wave, the nerve activating the muscle directly. The bump at six to nine is the H-reflex, which went to the spinal cord and back. That's the one conditioning changes. This figure is the average of about two hundred eighty thousand trials from one animal.

## Slide 7 — First problem: the archive would not decode   [SUCHITH]

The first problem took a couple of weeks. The recordings were saved in 2006 in an old database format, with a script that was supposed to read them. Every number in the file is stored as two bytes, and the script had the order of those two bytes backwards. Read that way, every trial came out as noise. Read the other way round, the muscle response appears. The reason we trust it is not that it looked right. The M-wave and the H-reflex appeared at exactly the times the experimenter had typed into the log in 2006: two to four milliseconds and six to nine milliseconds. The data matched the notes, and the notes matched the data.

## Slide 8 — 6   [SUCHITH]

Six animals, three trained down and three up, forty-five to two hundred ten days each. Worth explaining how we chose them, because it saved us a lot of time. The log files are a few hundred kilobytes; the signal data is four gigabytes an animal. The experimenter raises the reward threshold whenever the rat exceeds it — so the threshold history is a written record of how the animal was doing. We read only the logs, then downloaded signal data for the ones that responded. We also dropped animal twelve: its pre-stimulus cortical signal is under three microvolts against a hundred-plus in the others, so that electrode had failed.

## Slide 9 — Who is in the study   [SUCHITH]

This is who is in the study. Each card is one animal. The coloured bar at the top says which way it was trained: blue down, orange up. Under the name is how many trials it has, from about two hundred eighty thousand to six hundred thirty thousand. The dot at the bottom says how it did. Three met the lab's twenty percent criterion: 9, 11 and 3. Two did not, 10 and 4. Their reflexes actually moved against their training, and they come back later as a comparison group. Animal 12's brain electrode had failed, so it is left out of anything involving the brain signal.

## Slide 10 — The pipeline, end to end   [TARUN]

This is the whole process, left to right. First we load the 2006 files into a database on a laptop. Then we read each trial into two traces in microvolts, one for muscle and one for brain. Then we save each animal as one file in a format called Zarr. All that means is the data is stored in small pieces, so we can pull out any part of 2.7 million trials without loading all of it into memory. Then we measure the M-wave, the H-reflex and the background muscle activity. Then the model learns its summary of the brain signal, and finally everything is tested against the controls. The small grey labels are just the software used at each step; you do not need them to follow the talk. It is about four gigabytes in per animal and three hundred megabytes out, and once set up it is two commands per animal.

## Slide 11 — What the model actually is   [TARUN]

This is the model, and it's simpler than it sounds. On the left, one trial of brain signal — a hundred and fifty numbers. The encoder squeezes that down to forty-eight numbers. The decoder tries to rebuild the original from just those forty-eight. We train it by penalising the difference between the rebuild and the original. The important part is the bottleneck: to rebuild the trace from only forty-eight numbers, those numbers have to capture the trace's real structure rather than its noise. And crucially, nobody tells it what to look for. We never show it an H-reflex, a label, or a training phase. So the forty-eight numbers are whatever the signal's own structure demands, not the features we assumed mattered. After training we freeze it and use it purely as a description.

## Slide 12 — Training it, and the one trap we avoided   [TARUN]

Some numbers on training. The model saw six hundred thousand brain-signal trials from five animals and went through them twelve times. That took about four minutes on a laptop, because this is a small model. The reconstruction error, meaning how far the rebuilt trace is from the real one, roughly halved and then levelled off, which is what you want to see. The trap is this: if you mix animals together without care, the easiest thing for the model to learn is which animal a trace came from, because each electrode has its own size and character. That is a property of the recording, not the biology. So we scale each animal's data to the same range before mixing. And we use one model for all animals rather than one each, so a given pattern means the same thing in every animal. That is what makes it fair to compare animals later.

## Slide 13 — Tech stack and daily workflow   [TARUN]

Very briefly, the software. Everything is free, open-source Python, and it all runs on a laptop. The names on the slide are for anyone who wants to repeat the work; you do not need them to follow the results. The daily routine was: read the animal's log, load its data, convert it, look at the average trace to check it decoded correctly, run the analyses, and save the figures. Every figure in this talk is produced by the code with one command. None were edited by hand, so when a number changed, every figure that used it changed too.

## Slide 14 — How the summer actually went   [TARUN]

Roughly how the summer went, because the shape of it matters. Two weeks reverse-engineering the format. Two building the converter and validating one animal. Two training the model and getting first results, which looked good. Then week seven, when the controls failed and we had to rethink the question — that was the most useful week of the project. It cost us the result we thought we had and produced the design the current finding rests on. Then the new design and five more animals.

## Slide 15 — Why reflex size alone tells you nothing   [TARUN]

This slide matters because getting it wrong cost us a result. Reflex size depends on two things besides learning: how strong the stimulus was — a stronger stimulus gives a bigger reflex — and how active the muscle already was. That is what Boulay and colleagues found: H-reflex size varied with M-wave size and background EMG as well as with cortical activity. And the stimulus is not constant: in one of our animals it nearly quintupled over the recording, and early on that made one of our findings come out backwards. The corrections: the M-wave in the same trace is a per-trial receipt for how much stimulus arrived, and the twenty milliseconds before each stimulus measures background muscle activity. We remove both from every measure. Every number from here on has both corrections applied.

## Slide 16 — Conditioning works, in both directions   [SUCHITH]

First, the check that has to pass before anything else counts: did the animals learn? How to read the left graph: the horizontal axis is days, lined up so that zero is the day each animal's training began. Left of zero is baseline, right of zero is training. The vertical axis is the size of the H-reflex as a percent change from that animal's own baseline, after correcting for stimulus strength and background muscle activity. Thin lines are single animals, thick lines are group averages, red for up-trained and blue for down-trained. The dashed lines mark plus and minus twenty percent. Animals 9 and 11 fall and animal 3 rises, so three of five meet the twenty percent criterion in the direction they were trained. Animals 10 and 4 moved the other way; they serve as a comparison group later. One caution: this is a percent of baseline, so an animal with a small baseline looks bigger than it is. Animal 3's baseline is about nineteen microvolts, against sixty to a hundred and sixty in the others. The right-hand graph is the brain measure, which we come to next.

## Slide 17 — Two things change slowly over the same weeks   [SUCHITH]

Now the central difficulty. Two things change slowly over the same weeks: what the animal has learned, and the implanted brain electrode itself, as tissue settles around it and the signal slowly shifts. These two graphs are a sketch of the idea, not data. On the left, both rise together over the weeks. On the right is what we actually record: one curve that mixes the two, with no way to pull them apart. Within one animal, learning and electrode change are both slow and steady, so no analysis can separate them. That is a limit of how the study was designed, not of the data, and it shaped everything we did next.

## Slide 18 — Our first approach did not survive its controls   [SUCHITH]

Our first approach was the obvious one. Take the model's summary of the brain signal, average it for each day, and measure how far that average moves from baseline as training goes on. It does move, and at first it looked convincing. But three checks say the movement comes from the recording, not the animal. First, take only baseline days, before any training, and pretend the second half was training. Nothing happened in those days, yet the average moves just as much, in five of six animals. Second, shuffle which trial belongs to which day: then nothing moves, so the measure is not inventing movement. Third, electrode change does not depend on which way an animal was trained, but learning does, and the up-trained and down-trained groups do not differ. Those checks changed our conclusion, and we would rather show you that than leave it out.

## Slide 19 — So we asked a question that drift cannot fake   [SUCHITH]

So rather than keep fighting that confound, we changed the question. Instead of asking whether the average moved, we ask whether the brain can predict this particular trial's reflex. Here's the design, and it's the part I'd most like your reaction to. The top bar is the whole recording, with colour showing the electrode slowly changing. We chop it into five-day windows. Inside one window we train on four fifths of the trials and test on the held-out fifth. Within five days the electrode is essentially fixed, and whatever drift remains moves the training and test trials together, so it cancels. Drift can move an average. It cannot invent a trial-by-trial relationship inside five days.

## Slide 20 — And each window is judged against itself   [SUCHITH]

And we don't just look at whether the prediction is good in absolute terms, because there's no natural yardstick for that. Instead each window is judged against itself: take the same trials, shuffle which reflex goes with which brain signal, and run the identical analysis. Same numbers, wrong pairings, so any real relationship is destroyed. If the real version doesn't beat the shuffled one, there was nothing there. We do that in all hundred and one windows.

## Slide 21 — 99 of 101   [SUCHITH]

This is the main finding. The graph first: the horizontal axis is days relative to the start of training. The vertical axis is the prediction score, R squared: the fraction of the trial-to-trial variation in reflex size that the brain signal predicts, always measured on trials the model did not see. Zero means no prediction. Each thin line is one animal; the thick lines are the up and down group averages. The number to take away is on the right. In 99 of 101 five-day windows, the real data beat its own shuffled version. If there were no real signal, real versus shuffled would be a coin flip in each window, so you would expect about half, not 99 of 101. It holds in all five animals. On the statistics: windows from the same animal share an electrode, so they are not independent, and we do not count them as if they were. The test we report counts each animal once: t equals 3.81 with four degrees of freedom, p equals 0.019. So the effect is small, but it almost never disappears.

## Slide 22 — How much does the brain actually explain?   [SUCHITH]

How much does the brain actually explain? The bar is all of the trial-to-trial variation in reflex size, a hundred percent from left to right. Stimulus strength, measured by the M-wave, accounts for forty-seven percent. Background muscle activity before the stimulus adds one percent. About half is unexplained, which is normal for single trials in an awake animal. The thin blue sliver is the brain's own contribution: two percent. The brain signal on its own seems to explain twenty-one percent, but almost all of that overlaps with the stimulus, because the stimulus drives both the brain response and the reflex. Only what is left after stimulus and background are accounted for counts as the brain's own contribution. Two percent is small, and we do not want to oversell it.

## Slide 23 — All five animals, all three measures   [SUCHITH]

All five animals and all three measures side by side. Left panel, behaviour: each bar is one animal, showing how much its reflex changed in the direction it was trained. Positive means it moved the way it was trained, up for an up-trained animal and down for a down-trained one. The dashed line is the twenty percent criterion. Animals 9, 11 and 3 pass it; animal 3's bar is cut off at the edge and labelled, because its small baseline makes its percentage very large. Animals 10 and 4 are negative: they moved against their training. Middle panel: each animal's prediction score, blue for the real data and grey for the same data shuffled. Blue is higher in every animal, and the grey bars sit at or just below zero, which is what a fair shuffle should give. Right panel: how many five-day windows beat their shuffle. Nine of nine, fifteen of seventeen, and the other three animals at every window: 99 of 101 in total.

## Slide 24 — Every control we applied   [SUCHITH]

These are the controls we applied. Five it survives, two it fails, and the two failures are what told us the average-state approach was the wrong question. If anyone here can think of something we haven't tried, that's genuinely the most useful thing I could take away from this meeting.

## Slide 25 — Is the brain electrode just picking up muscle?   [SUCHITH]

The obvious objection: both electrodes record at the same moment, so maybe the brain electrode is simply picking up the muscle. How to read this: the left graph compares each animal's prediction score under the earlier and the stricter correction, next to the shuffle. The right graph shows, for each frequency band from low on the left to high on the right, how closely brain-signal power and muscle power rise and fall together; near zero means they are independent. Muscle interference shows up at high frequencies, so that is where contamination would appear. Above a hundred hertz the correlation is plus 0.06, essentially zero. The low bands are slightly negative. And the brain signal slightly leads the muscle rather than following it, which is the direction you would expect if it is not contamination.

## Slide 26 — Does it scale with how much they learned?   [SUCHITH]

This is the thread we think is most promising, and it is the graph that needs the most explaining, so let me go slowly. Each dot is one animal, red for up-trained and blue for down-trained. The horizontal axis is how much the animal learned: the percent change in its reflex in the direction it was trained. The dotted vertical line is twenty percent, so dots to the right of it met the criterion. In the left graph, the vertical axis is how well the brain signal predicts the reflex during training. In the right graph, the vertical axis is the change in that prediction from baseline to training, training minus baseline, so above zero means the brain became more predictive once training started. The right graph is the one that matters. The line slopes upward, with a correlation of plus 0.64: animals that learned more tended to gain more coupling. The two that did not meet criterion, 10 and 4, show no increase; 10 went down and 4 stayed flat. The exception is animal 9, which met criterion but did not gain. And animal 3 sits far to the right partly because of its small baseline. With five animals this points in a direction but does not settle it; that is what the remaining animals are for.

## Slide 27 — The metadata may be a measurement   [TARUN]

A new thread. First, what the reward criterion is, because in the lab's logs it is written as RW. It is the value the reflex has to pass to earn a food pellet: above it for an up-trained animal, below it for a down-trained one. The experimenter resets it every day so the rat is rewarded on roughly thirty to forty percent of trials, the ones furthest in the trained direction. So the reward rate stays about the same while the requirement moves as the animal changes. In effect it is a staircase. That makes its history a record of how demanding the task was for each animal: effort and engagement, not just success, written down by a person at the time, independently of anything we measure from the electrodes. At the moment our scaling result compares two things measured from the same electrodes. If brain coupling also tracks a record kept by hand, that is a much harder result to dismiss. We would like to build this next.

## Slide 28 — Three things worth writing up   [TARUN]

If this becomes a paper, we think there are three pieces. The method — a reproducible pipeline that recovers a twenty-year-old archive and learns a representation from it on a laptop, which is useful to anyone with old chronic recordings on a shelf. The finding — cortical activity carries a small but highly reliable single-trial signal about reflex size, which extends Chad's work from a population relationship to a single-trial one. And the warning — the intuitive drift analysis produces a convincing result that three controls reject, and we'd want to save the next group from spending months on it. We'd aim at a machine-learning venue, framed as an extension of the existing cortical-spinal work.

## Slide 29 — Where a single-trial cortical readout could help   [TARUN]

Why this might matter, and I want to be careful not to oversell. If cortex predicts the reflex before the fact, conditioning protocols could in principle adapt trial by trial rather than day by day. Roughly a third of animals, and of people, don't respond to conditioning — a cortical readout might show why, early. And reflex conditioning is already used clinically after spinal cord injury, so any handle on the cortical side is a handle on individualising it. All three depend on the effect being bigger and more reliable than what we can currently show. We're not there. But that's the direction that makes it worth getting there.

## Slide 30 — What happens next   [TARUN]

What happens next. The remaining down-conditioned animals, seven, eight, thirteen and fourteen, are next through the pipeline, which takes us from five to nine and is what powers the scaling test. Then frequency-resolved coupling, to see which bands carry the information — that sharpens both the finding and the contamination argument. The reward-criterion measure as an independent behavioural record. And then writing it up.

## Slide 31 — What we can say   [SUCHITH]

To summarise. Conditioning reproduces in both directions with full stimulus control — that's solid. Cortex carries a small single-trial signal about reflex size that beats its own shuffled control in ninety-nine of a hundred and one windows and in every animal — that's real, and small. And the average-state drift analysis is a useful negative: it looks convincing and three controls reject it. Every number is corrected for stimulus and muscle activity.

## Slide 32 — What we know we haven't settled   [SUCHITH]

And the things we know we haven't settled. Whether the coupling grows with learning — the correlation points the right way but five animals can't settle it, and four more are next. Which frequencies carry the signal. Whether two percent of variance is biologically meaningful, which is honestly a question for this room more than for us. And what else could produce it that we haven't excluded — we'd genuinely like to know what we're missing.

## Slide 33 — Code, data pipeline, figures and write-up   [SUCHITH]

Everything is public. There's a project page with the findings and figures, the repository with the full pipeline — two commands per animal and it runs end to end — and a six-page write-up. The repository has every script, the trained encoder, all the figures, per-animal results, a starter notebook and setup instructions. Raw recordings are available through NCAN. If anyone wants to run it on their own data, it should be straightforward.

## Slide 34 — Thank you   [SUCHITH]

Thank you, and our thanks to Dr. Carp and Theresa Vaughan for their guidance throughout this project. Happy to take questions.

---

## Questions to expect

**"This sounds like bootstrap statistics."** (Carp raised this last time)
> "It's the same family of methods, but a different test. A bootstrap resamples to put error bars on an estimate. We scramble the pairing of brain signal and reflex, which destroys any real relationship, and ask whether the real data does better. Because windows from the same animal aren't independent, we don't test on the 99 of 101 count. The test counts each animal once: t(4) = 3.81, p = 0.019."

**"Is the behavioural change a difference or a ratio?"** (Carp raised this last time)
> "It's a percent change from each animal's own baseline, so it's a ratio. An animal with a small baseline looks bigger than it is: animal 3's is about 19 microvolts, against 60 to 160 in the others. The direction of change isn't affected."

**"What does positive mean on the behaviour axis?"**
> "Positive means the reflex moved the way that animal was trained: up for an up-trained animal, down for a down-trained one. Animals 10 and 4 are negative, so they moved against their training."

**"Which animals were trained up and which down?"**
> "Down: 9, 10 and 11. Up: 3, 4 and 12, and 12's brain electrode had failed. No other up-trained recording in the archive is usable, so the up group stays at two."

**"What is the reward criterion?"**
> "It's the value the reflex has to pass for a pellet. It's reset daily so the rat is rewarded on about 30 to 40 percent of trials, so its history tracks how demanding the task was for that animal. We read it as effort and engagement, not success."

**"Is 2% of variance meaningful?"**
> "On size alone, it's modest. It's in every animal and in 99 of 101 windows after every control we could apply, and this is single-trial physiology in an awake animal. Whether it's biologically meaningful is a question we'd like this group's view on."

**"Why is the prediction score lower than in earlier updates?"**
> "Stimulus and background were first removed across all trials at once, which leaves stimulus variation inside each window, and the brain signal tracks the stimulus. Removing them inside each window gives 0.037. That's the number we stand behind."

**"Couldn't the brain electrode be recording muscle?"**
> "Muscle interference is high-frequency. Above 100 Hz the correlation between brain and muscle power is +0.06, the low bands are slightly negative, and the brain signal slightly leads the muscle."

**"Why only five animals?"**
> "Five are processed. Animals 7, 8, 13 and 14, all down-trained, are next."

**If you don't know:**
> "I don't want to guess at that. Let me check and come back to you."

---

## Timing

| Part | Slides | Target |
|---|---|---|
| Question and data | 1–9 | 10 min |
| How we built it | 10–15 | 8 min |
| Results | 16–26 | 15 min |
| Where it goes and close | 27–34 | 7 min |

If you run long, shorten 13 (software) and 14 (timeline). Never rush 11, 19, 21 or 26.
