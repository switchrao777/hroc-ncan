# 10-Minute Talk Track — HROC Animal 9 (for Dr. Carp)

**How to use this:** one paragraph per slide. Say the **bold line**, then the
plain sentence under it. Don't read the slide — the slide is for Carp's eyes,
this is for your mouth. Total ~10 min. Time budget in [brackets].

The single sentence to survive on if you blank:
> *"The pipeline runs on real Animal 9, down-conditioning clearly worked, and the
> cortical change survives controlling for the stimulus — but it's modest, so
> this is a validated foundation, not a finished result."*

---

### Slide 1 — Title  [0:15]
"Quick update on the deep-learning side. This week I got the whole thing running
on **real** Animal 9 data, end to end — and I want your read on what's real and
what isn't."

### Slide 2 — The question  [0:40]
"The bet hasn't changed: does the cortex change as the spinal cord learns? Chad
did the simple correlation. Our new angle is watching the cortical
**representation** move across conditioning."

### Slide 3 — Synthetic → real  [0:30]
"Everything before was synthetic, just to prove the machine works. Now it's the
real recordings — 283,000 trials, both channels, decoded and phase-labeled."

### Slide 4 — What one trial is  [0:40]
"Each trial is a 30-millisecond snapshot, two electrodes at once: the leg muscle,
where the H-reflex lives, and the cortex — the brain signal we study."

### Slides 5–7 — How we got to real data  [1:30 total, ~30s each]
- **Decode:** "First I proved we read the raw signal right — the muscle trace
  shows the textbook stimulus → M-wave → H-reflex shape. Real physiology."
- **Phases:** "I recovered the conditioning phases from the experimenter's log.
  One correction: the 'stopped conditioning' note is misleading — the reflex
  keeps dropping after it — so I anchor on the conditioning *onset* instead."
- **Label:** "The measure is the H-reflex at 6–9 ms, and — importantly — we
  always divide by the M-wave. More on why in two slides."

### Slide 8 — The model  [0:45]
"Instead of hand-picking features, the model learns its own 48-number
**fingerprint** of the brain trace — Phase 1, no labels. Then we freeze it and
ask whether that fingerprint can read the reflex. That's Phase 2."

### Slide 9 — Cheat sheet  [0:20]
"Quick vocab for the next three slides — fingerprint, R², drift, and the M-wave
control. I'll refer back to these."  *(Don't linger — let them scan it.)*

---
## THE RESULTS — slow down here [3:00 total]

### Slide 10 — Behaviour: it worked  [1:00]  ← lead with this
"**Down-conditioning clearly worked.** The H/M ratio is flat at baseline, then
drops steadily to about 0.18 — textbook. And this is the key methodological
point: I use H/M, **not raw H**, because the reflex depends on stimulus strength —
and you can see on the right the stimulus drifted up over the same weeks. An
earlier raw-H plot looked backwards for exactly that reason; this fixes it."

### Slide 11 — The cortical drift, controlled  [1:00]  ← the test Carp will demand
"The cortical fingerprint does shift during conditioning. The obvious worry is
that the stimulus drove both. So I **mathematically remove the M-wave from the
brain signal and re-measure** — the two lines sit right on top of each other. So
the cortical change is **not** a stimulus artifact. Honest caveat: it's biggest
at conditioning *onset*, not steadily growing — the cortex reacts to the new
task rather than mirroring reflex size step for step."

### Slide 12 — Can cortex predict the reflex?  [1:00]
"Being honest about strength: the stimulus alone explains 0.20 of the reflex, the
cortex on its own only 0.05, and after removing the stimulus the cortex's unique
piece is 0.04. Small — but it survives the control, so it's real. And note: the
0.17 I might've quoted earlier was inflated by shared stimulus, once you control
for it properly it's modest."

---

### Slide 13 — Scorecard  [0:45]
"So where does that leave us? Infrastructure and behaviour: strong. Cortical
effect: real but modest. A publishable claim: not yet — one animal, one
direction."

### Slide 14 — Roadmap  [0:45]
"Next: add statistics to the drift, then pool more of the ~14 animals in the
Drive — the pipeline is built for it — and bring in up-conditioning animals as a
control that should drift the other way."

### Slide 15 — Discussion  [1:00 + Q&A]
"Where I need your read: how you'd define a clean baseline, whether H/M at 6–9 ms
is the label you want, what controls would convince you the drift is real, and
which animals to prioritize."

---
## If Carp pushes — quick answers

- **"Raw H is meaningless."** → "Agreed — that's why every reflex number here is
  H/M, and I regress the M-wave out of the cortical analysis too."
- **"The drift could be electrode drift over weeks."** → "Fair — I've only ruled
  out the stimulus so far. Session/electrode drift is next; a within-baseline
  split as a null and the up-conditioning animals are the real controls."
- **"Why is the drift bigger early than late?"** → "Honestly not sure yet — looks
  like the cortex responds to task onset rather than tracking reflex magnitude.
  Worth a finer time-resolved look."
- **"Is 0.04 even worth anything?"** → "On its own, barely. The value is that it
  survives the stimulus control and should grow with more animals — it's a
  foundation, and I'm being upfront it's not a result yet."
- **"What's the headline?"** → "Down-conditioning worked, and there's a real
  cortical change that isn't just stimulus. Everything else is future work."
