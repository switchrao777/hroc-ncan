// HROC Carp Update — real Animal 9 results deck.
// Run:  NODE_PATH=$(npm root -g) node slides/build_deck.js   (from repo root)
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";               // 13.3 x 7.5
p.author = "Suchith Rao";
p.title = "HROC — Cortical Correlates of H-reflex Conditioning (Animal 9)";

const W = 13.333, H = 7.5;
// palette (tied to the figures: violet drift line, teal EMG, green ECoG)
const DARK = "0F172A", INK = "1E293B", MUTED = "64748B", FAINT = "94A3B8";
const VIOLET = "6D28D9", TEAL = "0D9488", AMBER = "D97706", GREEN = "16A34A";
const CARD = "F1F5F9", CARDLINE = "E2E8F0", WHITE = "FFFFFF";
const SERIF = "Cambria", SANS = "Calibri";
const IMG = (f) => "outputs/" + f;

const shadow = () => ({ type: "outer", color: "0F172A", blur: 9, offset: 3, angle: 90, opacity: 0.14 });

// ---- helpers ----------------------------------------------------------------
function bg(s, c){ s.background = { color: c }; }
function title(s, t, sub){
  s.addText(t, { x:0.7, y:0.5, w:12, h:0.7, fontFace:SERIF, fontSize:30, bold:true, color:INK, margin:0 });
  if (sub) s.addText(sub, { x:0.72, y:1.18, w:12, h:0.45, fontFace:SANS, fontSize:15, color:VIOLET, margin:0 });
}
function kicker(s, t, color){
  s.addText(t.toUpperCase(), { x:0.72, y:0.42, w:12, h:0.3, fontFace:SANS, fontSize:12.5, bold:true,
    color:color||TEAL, charSpacing:3, margin:0 });
}
function card(s, x, y, w, h, fill){
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius:0.09,
    fill:{ color: fill||WHITE }, line:{ color:CARDLINE, width:1 }, shadow: shadow() });
}
function numCircle(s, x, y, n, color){
  const d=0.5;
  s.addShape(p.shapes.OVAL, { x, y, w:d, h:d, fill:{ color: color }, line:{ type:"none" } });
  s.addText(String(n), { x, y, w:d, h:d, align:"center", valign:"middle", fontFace:SANS,
    fontSize:18, bold:true, color:WHITE, margin:0 });
}
function img(s, f, x, y, w, h){ s.addImage({ path: IMG(f), x, y, w, h, sizing:{ type:"contain", w, h } }); }
function imgFit(ratio, maxW, maxH){ // returns [w,h] preserving ratio inside box
  let w=maxW, h=w/ratio; if (h>maxH){ h=maxH; w=h*ratio; } return [w,h];
}

// ============================================================ 1 · TITLE (dark)
(() => {
  const s = p.addSlide(); bg(s, DARK);
  // motif: three soft dots (baseline -> cond -> post)
  s.addShape(p.shapes.OVAL, { x:11.0, y:0.9, w:1.5, h:1.5, fill:{color:VIOLET, transparency:55}, line:{type:"none"} });
  s.addShape(p.shapes.OVAL, { x:11.7, y:1.7, w:1.0, h:1.0, fill:{color:TEAL, transparency:45}, line:{type:"none"} });
  s.addText("HROC · NCAN · Deep-Learning Track", { x:0.8, y:1.5, w:10, h:0.4, fontFace:SANS,
    fontSize:14, bold:true, color:TEAL, charSpacing:3, margin:0 });
  s.addText("Does the cortex change as the\nspinal cord learns?", { x:0.8, y:2.05, w:11.4, h:2.0,
    fontFace:SERIF, fontSize:46, bold:true, color:WHITE, lineSpacingMultiple:0.98, margin:0 });
  s.addText("First real-data results — Animal 9 through the full pipeline, end to end.",
    { x:0.82, y:4.15, w:11, h:0.5, fontFace:SANS, fontSize:18, color:"CBD5E1", margin:0 });
  s.addText([
    { text:"Suchith Rao", options:{ bold:true, color:WHITE } },
    { text:"    •    prepared for Dr. Carp    •    July 2026", options:{ color:FAINT } },
  ], { x:0.82, y:6.4, w:11, h:0.4, fontFace:SANS, fontSize:15, margin:0 });
  s.addNotes("This week I got the whole deep-learning pipeline running on REAL Animal 9 data, end to end. I'll walk through what it does, show the first real results, and get your read on a few neuro calls. Everything before this was a synthetic proof-of-concept; this is the real signal.");
})();

// ============================================================ 2 · THE QUESTION
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "The scientific bet");
  title(s, "The question, in one line");
  // left: the paradigm as 3 steps
  card(s, 0.7, 1.9, 6.0, 4.9);
  s.addText("The paradigm", { x:1.0, y:2.15, w:5.4, h:0.4, fontFace:SANS, fontSize:16, bold:true, color:INK, margin:0 });
  const steps = [
    ["Baseline","Record the spinal H-reflex (a leg-muscle reflex) without training."],
    ["Down-conditioning","Reward the animal for making the reflex smaller. The spinal cord slowly learns."],
    ["The brain?","We record cortex (ECoG) at the same time — and ask if IT changes too."],
  ];
  let y=2.75;
  steps.forEach((st,i)=>{
    numCircle(s, 1.0, y, i+1, i===2?VIOLET:TEAL);
    s.addText(st[0], { x:1.65, y:y-0.03, w:4.8, h:0.35, fontFace:SANS, fontSize:15, bold:true, color:INK, margin:0 });
    s.addText(st[1], { x:1.65, y:y+0.33, w:4.85, h:0.7, fontFace:SANS, fontSize:12.5, color:MUTED, margin:0 });
    y+=1.3;
  });
  // right: the novel angle
  card(s, 7.0, 1.9, 5.6, 4.9, "F5F3FF");
  s.addText("What's new here", { x:7.35, y:2.2, w:5, h:0.4, fontFace:SANS, fontSize:16, bold:true, color:VIOLET, margin:0 });
  s.addText([
    { text:"Chad already published the simple link — ", options:{ color:INK } },
    { text:"when the reflex goes down, ECoG activity shifts. That correlation is done.", options:{ color:INK } },
  ], { x:7.35, y:2.75, w:4.95, h:1.1, fontFace:SANS, fontSize:15, lineSpacingMultiple:1.05, margin:0 });
  s.addText("Our new question:", { x:7.35, y:4.0, w:5, h:0.4, fontFace:SANS, fontSize:14, bold:true, color:MUTED, margin:0 });
  s.addText("Does the brain's internal representation drift across conditioning — a cortical fingerprint of learning that's never been shown?",
    { x:7.35, y:4.4, w:4.95, h:1.5, fontFace:SERIF, fontSize:19, bold:true, italic:true, color:VIOLET, lineSpacingMultiple:1.03, margin:0 });
  s.addNotes("Reground everyone in the science. The bet hasn't changed: does the cortex change as the cord learns. Chad squeezed the simple correlation dry. The novel angle is watching the cortical representation MOVE across phases. Animal 9 is the first paired dataset that lets us even ask this.");
})();

// ============================================================ 3 · WHAT CHANGED
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "This week");
  title(s, "From a synthetic demo to real data");
  // before / after
  card(s, 0.7, 1.95, 5.75, 2.2, CARD);
  s.addText("BEFORE", { x:1.0, y:2.2, w:5, h:0.3, fontFace:SANS, fontSize:12.5, bold:true, color:MUTED, charSpacing:2, margin:0 });
  s.addText("The pipeline ran on synthetic (fake) data shaped like Animal 9 — enough to prove the machine works, but not a scientific result.",
    { x:1.0, y:2.6, w:5.2, h:1.4, fontFace:SANS, fontSize:15, color:INK, lineSpacingMultiple:1.05, margin:0 });
  card(s, 6.85, 1.95, 5.75, 2.2, "F5F3FF");
  s.addText("NOW", { x:7.15, y:2.2, w:5, h:0.3, fontFace:SANS, fontSize:12.5, bold:true, color:VIOLET, charSpacing:2, margin:0 });
  s.addText("The exact same pipeline is trained on the real Animal 9 recordings — decoded, phase-labeled, and run end to end.",
    { x:7.15, y:2.6, w:5.2, h:1.4, fontFace:SANS, fontSize:15, color:INK, lineSpacingMultiple:1.05, margin:0 });
  // three big stats
  const stats = [["283,315","real trials decoded"],["3","conditioning phases recovered"],["2","brain + muscle channels"]];
  let x=0.7;
  stats.forEach(([n,l])=>{
    card(s, x, 4.5, 3.87, 2.15);
    s.addText(n, { x:x, y:4.8, w:3.87, h:0.95, align:"center", fontFace:SERIF, fontSize:44, bold:true, color:TEAL, margin:0 });
    s.addText(l, { x:x, y:5.75, w:3.87, h:0.6, align:"center", fontFace:SANS, fontSize:14.5, color:MUTED, margin:0 });
    x+=4.08;
  });
  s.addNotes("The honest framing: everything I showed before was synthetic, proving the machine works. This week it's real. Same code, real Animal 9 — 283k trials, both channels, three phases. From here on, every number is real data.");
})();

// ============================================================ 4 · THE DATA
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "Orientation");
  title(s, "What one trial actually is");
  s.addText("Animal 9's recordings live in a 2006 lab database. Each stimulus creates one trial — a 30-millisecond snapshot, sampled 5,000 times a second, on two electrodes at once:",
    { x:0.7, y:1.75, w:11.9, h:0.9, fontFace:SANS, fontSize:16, color:INK, lineSpacingMultiple:1.05, margin:0 });
  // two channel cards
  card(s, 0.7, 2.9, 5.85, 3.5);
  s.addShape(p.shapes.OVAL, { x:1.0, y:3.2, w:0.55, h:0.55, fill:{color:TEAL}, line:{type:"none"} });
  s.addText("A", { x:1.0, y:3.2, w:0.55, h:0.55, align:"center", valign:"middle", fontFace:SANS, fontSize:18, bold:true, color:WHITE, margin:0 });
  s.addText("Muscle — EMG (soleus)", { x:1.7, y:3.22, w:4.6, h:0.5, fontFace:SANS, fontSize:17, bold:true, color:INK, margin:0 });
  s.addText([
    { text:"The leg-muscle response to the stimulus. This is where the ", options:{color:INK} },
    { text:"H-reflex", options:{bold:true, color:TEAL} },
    { text:" lives — the thing conditioning trains.", options:{color:INK} },
  ], { x:1.0, y:4.0, w:5.25, h:1.2, fontFace:SANS, fontSize:14.5, color:INK, lineSpacingMultiple:1.05, margin:0 });
  s.addText("→ our prediction target", { x:1.0, y:5.75, w:5, h:0.4, fontFace:SANS, fontSize:13.5, bold:true, italic:true, color:TEAL, margin:0 });

  card(s, 6.75, 2.9, 5.85, 3.5, "F5F3FF");
  s.addShape(p.shapes.OVAL, { x:7.05, y:3.2, w:0.55, h:0.55, fill:{color:VIOLET}, line:{type:"none"} });
  s.addText("B", { x:7.05, y:3.2, w:0.55, h:0.55, align:"center", valign:"middle", fontFace:SANS, fontSize:18, bold:true, color:WHITE, margin:0 });
  s.addText("Brain — ECoG (cortex surface)", { x:7.75, y:3.22, w:4.6, h:0.5, fontFace:SANS, fontSize:17, bold:true, color:INK, margin:0 });
  s.addText("Electrical activity from the surface of the motor cortex, recorded at the very same moment as the muscle. This is the brain signal we study.",
    { x:7.05, y:4.0, w:5.25, h:1.4, fontFace:SANS, fontSize:14.5, color:INK, lineSpacingMultiple:1.05, margin:0 });
  s.addText("→ the model's input", { x:7.05, y:5.75, w:5, h:0.4, fontFace:SANS, fontSize:13.5, bold:true, italic:true, color:VIOLET, margin:0 });
  s.addNotes("Ground Carp in the raw data. Each trial is a 30ms window at 5kHz with two simultaneous channels: the leg EMG (where the H-reflex is) and the cortical ECoG (the brain signal we model). Everything downstream is about relating these two.");
})();

// ============================================================ 5 · STEP 1 DECODE
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "Step 1 of 3 · getting to real data");
  title(s, "First: prove we're reading the signal right");
  const [w,h] = imgFit(2.80, 8.2, 3.3);
  img(s, "inspect/emg_reflexes.png", 0.7, 2.05, w, h);
  s.addText("The raw data is a 20-year-old binary format. We confirmed the decode by averaging the muscle channel: it shows the textbook shape — a stimulus artifact, then the M-wave (2–4 ms), then the H-reflex (~6–7 ms). Real physiology, not noise.",
    { x:0.72, y:5.5, w:8.0, h:1.3, fontFace:SANS, fontSize:14.5, color:INK, lineSpacingMultiple:1.05, margin:0 });
  // side note card
  card(s, 9.1, 2.15, 3.5, 3.9, CARD);
  s.addText("What this took", { x:9.35, y:2.4, w:3, h:0.35, fontFace:SANS, fontSize:14, bold:true, color:VIOLET, margin:0 });
  s.addText([
    { text:"Loaded the 2.3 GB database locally", options:{ bullet:true, breakLine:true } },
    { text:"Cracked the byte format (it was mislabeled in the lab docs)", options:{ bullet:true, breakLine:true } },
    { text:"Confirmed channel A = muscle, B = brain", options:{ bullet:true, breakLine:true } },
    { text:"Verified against textbook M / H timing", options:{ bullet:true } },
  ], { x:9.35, y:2.85, w:3.05, h:3.0, fontFace:SANS, fontSize:13, color:INK, lineSpacingMultiple:1.05, paraSpaceAfter:6, margin:0 });
  s.addNotes("Before trusting anything, we had to prove the decode. The averaged muscle trace shows the classic stimulus -> M-wave -> H-reflex sequence. We also corrected the lab's own format notes (they said big-endian; it's actually little-endian). This is the gate: if this looked like noise, nothing else would mean anything.");
})();

// ============================================================ 6 · STEP 2 PHASES
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "Step 2 of 3 · getting to real data");
  title(s, "Recover the conditioning phases");
  s.addText("We read the experimenter's own typed log from 2006 to find when each phase began — then tagged all 283k trials by time.",
    { x:0.7, y:1.75, w:11.9, h:0.7, fontFace:SANS, fontSize:16, color:INK, lineSpacingMultiple:1.05, margin:0 });
  // phase cards with counts
  const ph = [["Baseline","149,064","Setup + characterize the reflex", MUTED],
              ["Down-conditioning","55,397","Cord trained to shrink the reflex", VIOLET],
              ["Post","78,854","After conditioning stopped", TEAL]];
  let x=0.7;
  ph.forEach(([name,n,desc,col])=>{
    card(s, x, 2.75, 3.87, 2.4);
    s.addText(name, { x:x+0.05, y:3.0, w:3.77, h:0.5, align:"center", fontFace:SANS, fontSize:16, bold:true, color:col, margin:0 });
    s.addText(n, { x:x+0.05, y:3.5, w:3.77, h:0.8, align:"center", fontFace:SERIF, fontSize:34, bold:true, color:INK, margin:0 });
    s.addText(desc, { x:x+0.15, y:4.4, w:3.57, h:0.6, align:"center", fontFace:SANS, fontSize:12.5, color:MUTED, margin:0 });
    x+=4.08;
  });
  // arrow-ish flow dots
  card(s, 0.7, 5.5, 11.9, 1.25, "F5F3FF");
  s.addText([
    { text:"Key detail:  ", options:{ bold:true, color:VIOLET } },
    { text:"Animal 9 ran Baseline → Down-conditioning → Post — NOT the full 6-phase protocol. We verified the phase boundaries against the authoritative database schema, so these labels are trustworthy.", options:{ color:INK } },
  ], { x:1.0, y:5.72, w:11.3, h:0.9, fontFace:SANS, fontSize:14.5, valign:"middle", lineSpacingMultiple:1.03, margin:0 });
  s.addNotes("The phase labels were listed as an open blocker. I recovered them from the type-15 entries in the experimenter's log — markers like 'Start HRdown' and 'Stopped conditioning' — and mapped every trial by timestamp. Important: Animal 9 only ran Baseline, down-conditioning, and post. And I later verified against the real schema file, so the boundaries are solid.");
})();

// ============================================================ 7 · STEP 3 LABEL
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "Step 3 of 3 · getting to real data");
  title(s, "Define what we predict: the H-reflex size");
  const [w,h] = imgFit(2.0, 7.4, 3.6);
  img(s, "validate/avg_emg.png", 0.7, 2.0, w, h);
  card(s, 8.5, 2.1, 4.1, 4.2, CARD);
  s.addText("The measure", { x:8.75, y:2.35, w:3.6, h:0.35, fontFace:SANS, fontSize:14, bold:true, color:VIOLET, margin:0 });
  s.addText([
    { text:"Where: ", options:{ bold:true, color:INK } },
    { text:"6–9 ms — the experimenter's log says exactly that, and it matches what we measured.", options:{ color:INK } },
  ], { x:8.75, y:2.8, w:3.65, h:1.15, fontFace:SANS, fontSize:14, lineSpacingMultiple:1.05, margin:0 });
  s.addText([
    { text:"How: ", options:{ bold:true, color:INK } },
    { text:"mean rectified amplitude in that window — your spec, not a single fragile peak.", options:{ color:INK } },
  ], { x:8.75, y:4.05, w:3.65, h:1.2, fontFace:SANS, fontSize:14, lineSpacingMultiple:1.05, margin:0 });
  s.addText("Green band = the H-reflex window on the real grand-average.",
    { x:8.75, y:5.5, w:3.65, h:0.7, fontFace:SANS, fontSize:12.5, italic:true, color:MUTED, margin:0 });
  s.addNotes("The H-reflex amplitude is the number Phase 2 predicts. Two things I want your read on later: the window (I'm using 6-9ms, which the log itself specifies and the data confirms) and the measure (mean rectified amplitude, which is your spec — robust to background activity, unlike a single peak).");
})();

// ============================================================ 8 · THE MODEL
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "The model, in plain words", VIOLET);
  title(s, "A 'cortical fingerprint' of each trial");
  s.addText("Instead of hand-picking features, the model learns its own compact summary of the brain signal — call it a fingerprint (48 numbers per trial). It's trained in two stages:",
    { x:0.7, y:1.75, w:11.9, h:0.85, fontFace:SANS, fontSize:16, color:INK, lineSpacingMultiple:1.05, margin:0 });
  // phase 1 card
  card(s, 0.7, 2.85, 5.85, 3.75);
  numCircle(s, 1.0, 3.15, 1, VIOLET);
  s.addText("Learn the fingerprint", { x:1.65, y:3.18, w:4.7, h:0.4, fontFace:SANS, fontSize:17, bold:true, color:INK, margin:0 });
  s.addText("The model compresses each brain trace down to 48 numbers, then rebuilds the original from them. To succeed, those numbers must capture the real structure of the signal.",
    { x:1.0, y:3.85, w:5.35, h:1.5, fontFace:SANS, fontSize:14.5, color:INK, lineSpacingMultiple:1.05, margin:0 });
  s.addText("No labels used here — it never sees the H-reflex.", { x:1.0, y:5.9, w:5.3, h:0.5, fontFace:SANS, fontSize:13.5, bold:true, italic:true, color:VIOLET, margin:0 });
  // phase 2 card
  card(s, 6.75, 2.85, 5.85, 3.75, "F5F3FF");
  numCircle(s, 7.05, 3.15, 2, TEAL);
  s.addText("Test what it captured", { x:7.7, y:3.18, w:4.7, h:0.4, fontFace:SANS, fontSize:17, bold:true, color:INK, margin:0 });
  s.addText("We freeze the fingerprint so it can't change, then attach a small predictor and ask: can you read the leg's H-reflex size from the brain fingerprint alone?",
    { x:7.05, y:3.85, w:5.35, h:1.5, fontFace:SANS, fontSize:14.5, color:INK, lineSpacingMultiple:1.05, margin:0 });
  s.addText("If yes → the brain signal genuinely carries H-reflex information.", { x:7.05, y:5.85, w:5.3, h:0.6, fontFace:SANS, fontSize:13.5, bold:true, italic:true, color:TEAL, margin:0 });
  s.addNotes("This is the concept everything hangs on. The autoencoder replaces hand-picked features: it learns its own 48-number fingerprint of the cortical trace by having to compress and then rebuild the signal. Phase 1 is unsupervised — it never sees an H-reflex label. Phase 2 freezes that fingerprint and tests whether the H-reflex can be read off it. Think nonlinear PCA that discovers its own axes.");
})();

// ============================================================ 8.5 · HOW TO READ
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "Plain English — a quick cheat sheet");
  title(s, "How to read the next three slides");
  const cells = [
    ["The fingerprint", VIOLET, "48 numbers the model invents to summarize each brain trace. Nobody tells it what to look for — it finds its own summary."],
    ["R²  (a 0-to-1 score)", TEAL, "How much of the reflex's trial-to-trial change the fingerprint can explain. 0 = nothing, 1 = perfect. We get 0.17 — weak but real, above chance."],
    ["Drift", VIOLET, "How far the average brain state has moved from where it started at Baseline. A bigger number means the representation changed more."],
    ["The catch", AMBER, "Some of that movement might come from the recording setup changing, not from learning. That's the one thing we still have to rule out."],
  ];
  const boxW=5.85, boxH=2.15, gapX=0.35, gapY=0.35, x0=0.7, y0=1.95;
  cells.forEach((c,i)=>{
    const cx = x0 + (i%2)*(boxW+gapX), cy = y0 + Math.floor(i/2)*(boxH+gapY);
    card(s, cx, cy, boxW, boxH, i===3 ? "FEF3E2" : WHITE);
    s.addShape(p.shapes.OVAL, { x:cx+0.32, y:cy+0.34, w:0.22, h:0.22, fill:{color:c[1]}, line:{type:"none"} });
    s.addText(c[0], { x:cx+0.68, y:cy+0.26, w:boxW-1.0, h:0.45, fontFace:SANS, fontSize:18, bold:true, color:INK, margin:0 });
    s.addText(c[2], { x:cx+0.35, y:cy+0.9, w:boxW-0.7, h:1.1, fontFace:SANS, fontSize:14.5, color:MUTED, lineSpacingMultiple:1.06, margin:0 });
  });
  s.addNotes("Quick cheat sheet before the results. Fingerprint = the model's self-invented 48-number summary of the brain signal. R-squared = how much of the reflex it can explain, 0 to 1, we get 0.17. Drift = how far the average brain state moved from baseline. And the catch: some of that drift might be recording-setup, not learning. Keep these four in mind for the next three slides.");
})();

// ============================================================ 9 · RESULT 1 (R2)
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "Result 1", TEAL);
  title(s, "The fingerprint really does carry the reflex");
  const [w,h] = imgFit(1.56, 6.6, 3.9);
  img(s, "phase2_loss.png", 0.7, 2.0, w, h);
  // big stat + read
  card(s, 7.7, 2.1, 4.9, 2.05, CARD);
  s.addText("R² = 0.17", { x:7.7, y:2.28, w:4.9, h:0.95, align:"center", fontFace:SERIF, fontSize:46, bold:true, color:TEAL, margin:0 });
  s.addText("brain fingerprint → H-reflex, frozen encoder", { x:7.7, y:3.25, w:4.9, h:0.7, align:"center", fontFace:SANS, fontSize:13.5, color:MUTED, margin:0 });
  s.addText([
    { text:"Read it honestly. ", options:{ bold:true, color:INK } },
    { text:"The cortical fingerprint predicts ~17% of the reflex's variation — with no labels during learning. Modest, but real and well above chance.", options:{ color:INK } },
  ], { x:7.7, y:4.35, w:4.9, h:1.5, fontFace:SANS, fontSize:14.5, lineSpacingMultiple:1.05, margin:0 });
  s.addText("On synthetic data this was 0.90 — only because that data was built to encode the reflex. 0.17 is the real cortex.",
    { x:7.7, y:5.95, w:4.9, h:0.9, fontFace:SANS, fontSize:12.5, italic:true, color:AMBER, lineSpacingMultiple:1.03, margin:0 });
  s.addNotes("Here's the test that makes the fingerprint trustworthy. Freeze the model, ask a tiny predictor to read the H-reflex off the fingerprint. R-squared 0.17 on real cortex. The green line climbing is it getting better at reading the reflex. It's far below the synthetic 0.90 — but that's expected and honest: the synthetic ECoG was built to encode the reflex; real cortex is far noisier. 0.17 with zero labels during learning is a genuine signal.");
})();

// ============================================================ 10 · RESULT 2 (DRIFT)
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "Result 2 · the headline", VIOLET);
  title(s, "The cortical fingerprint drifts as the cord learns");
  const [w,h] = imgFit(1.6, 7.2, 4.1);
  img(s, "centroid_drift.png", 0.7, 1.95, w, h);
  card(s, 8.4, 2.1, 4.2, 4.3, "F5F3FF");
  s.addText("What you're seeing", { x:8.65, y:2.35, w:3.7, h:0.35, fontFace:SANS, fontSize:14, bold:true, color:VIOLET, margin:0 });
  s.addText("Each point = how far that phase's average brain fingerprint sits from Baseline.",
    { x:8.65, y:2.8, w:3.75, h:1.0, fontFace:SANS, fontSize:14.5, color:INK, lineSpacingMultiple:1.05, margin:0 });
  s.addText([
    { text:"It jumps to 28.5 during down-conditioning, then falls back to 5.0 once conditioning stops.", options:{ bold:true, color:INK } },
  ], { x:8.65, y:3.95, w:3.75, h:1.4, fontFace:SANS, fontSize:15, lineSpacingMultiple:1.08, margin:0 });
  s.addText("The representation moves while the cord is learning — and partly recovers after. That's the effect we came to find.",
    { x:8.65, y:5.35, w:3.75, h:1.0, fontFace:SANS, fontSize:13, italic:true, color:VIOLET, lineSpacingMultiple:1.05, margin:0 });
  s.addNotes("This is the research question in one picture. Each phase's average cortical fingerprint, distance from baseline. It climbs sharply during down-conditioning and returns toward baseline afterward. The brain representation shifts as the cord learns and partly recovers when training stops. On a clean dataset, this figure is the paper. But — next slide — there's a confound to resolve first.");
})();

// ============================================================ 11 · CAVEAT
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "The honest caveat — read this", AMBER);
  title(s, "Is the drift learning, or just session state?");
  const [w,h] = imgFit(1.6, 6.4, 3.9);
  img(s, "hreflex_by_phase.png", 0.7, 2.0, w, h);
  card(s, 7.5, 2.1, 5.1, 4.35, "FEF3E2");
  s.addText("The problem", { x:7.75, y:2.35, w:4.6, h:0.35, fontFace:SANS, fontSize:14, bold:true, color:AMBER, margin:0 });
  s.addText("Down-conditioning should make the H-reflex SMALLER. But in the data it's larger during down-conditioning than at Baseline.",
    { x:7.75, y:2.78, w:4.65, h:1.15, fontFace:SANS, fontSize:14.5, color:INK, lineSpacingMultiple:1.05, margin:0 });
  s.addText("Most likely why:", { x:7.75, y:3.95, w:4.6, h:0.35, fontFace:SANS, fontSize:14, bold:true, color:INK, margin:0 });
  s.addText("our 'Baseline' is really the setup period — the log shows the stimulus being constantly re-tuned, so responses there are smaller and inconsistent.",
    { x:7.75, y:4.35, w:4.65, h:1.15, fontFace:SANS, fontSize:14, color:INK, lineSpacingMultiple:1.05, margin:0 });
  s.addText("So part of the cortical drift may track session state (fixed-stimulus, active recording) rather than learning itself. #1 thing to resolve.",
    { x:7.75, y:5.5, w:4.65, h:0.9, fontFace:SANS, fontSize:12.5, italic:true, bold:true, color:AMBER, lineSpacingMultiple:1.03, margin:0 });
  s.addNotes("I want to be upfront. The H-reflex is HIGHER during down-conditioning, which is backwards — down-conditioning should shrink it. The likely reason: the 'Baseline' block is really the setup/characterization period, where the stimulus intensity is still being tuned (the log is full of TARG adjustments). So the cortical drift might partly reflect overall session state rather than the learning. This is the single most important thing to nail down before we call it a cortical correlate of conditioning — and it's exactly where I need your input.");
})();

// ============================================================ 12 · ASSESSMENT
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "Where we stand");
  title(s, "Is this good progress? My honest scorecard");
  const items = [
    ["Infrastructure","STRONG", GREEN, "Real data flows end to end — decode, phase labels, training, analysis. Reproducible, on a laptop. This was the hard part and it's done."],
    ["First real signal","PROMISING", TEAL, "The fingerprint predicts the reflex above chance (R²=0.17) and the representation clearly moves during conditioning."],
    ["A publishable claim","NOT YET", AMBER, "Needs the baseline confound resolved, proper statistics, and more animals. Today is a strong foundation, not a result."],
  ];
  let x=0.7;
  items.forEach(([t,badge,col,desc])=>{
    card(s, x, 2.0, 3.87, 4.5);
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x:x+0.3, y:2.3, w:1.9, h:0.5, rectRadius:0.1, fill:{color:col}, line:{type:"none"} });
    s.addText(badge, { x:x+0.3, y:2.3, w:1.9, h:0.5, align:"center", valign:"middle", fontFace:SANS, fontSize:13, bold:true, color:WHITE, charSpacing:1, margin:0 });
    s.addText(t, { x:x+0.3, y:3.0, w:3.3, h:0.6, fontFace:SANS, fontSize:18, bold:true, color:INK, margin:0 });
    s.addText(desc, { x:x+0.3, y:3.7, w:3.35, h:2.5, fontFace:SANS, fontSize:14, color:MUTED, lineSpacingMultiple:1.08, margin:0 });
    x+=4.08;
  });
  s.addNotes("My honest read: the infrastructure is the big win — real data end to end, reproducible, and it was genuinely the hard part. The first signal is promising, above chance, with a visible drift. But it's not yet a claim: the confound, statistics, and more animals stand between us and a result. Strong foundation, honest about where it sits.");
})();

// ============================================================ 13 · NEXT / ROADMAP
(() => {
  const s = p.addSlide(); bg(s, WHITE);
  kicker(s, "Next", TEAL);
  title(s, "The plan — and it scales");
  s.addText("Animal 9 is 1 of ~14 conditioned animals sitting in the Drive. The pipeline is built to pool them — every new animal makes the drift result stronger.",
    { x:0.7, y:1.75, w:11.9, h:0.8, fontFace:SANS, fontSize:16, color:INK, lineSpacingMultiple:1.05, margin:0 });
  const road = [
    ["Resolve the baseline confound","Restrict 'Baseline' to post-setup trials; regress out raw reflex size. Does the drift survive?"],
    ["Add statistics","Bootstrap the drift — a within-baseline split should drift ~0. Is 28.5 vs 5.0 real?"],
    ["Pool more animals","Convert 6, 10, 11, 12, 13… one at a time, watching for animal-identity confounds."],
    ["Bring in controls","Up-conditioning animals should drift the other way; freely-running should barely drift."],
  ];
  let y=2.75;
  road.forEach((r,i)=>{
    card(s, 0.7, y, 11.9, 0.92);
    numCircle(s, 0.95, y+0.21, i+1, i<2?VIOLET:TEAL);
    s.addText(r[0], { x:1.7, y:y+0.13, w:4.2, h:0.65, valign:"middle", fontFace:SANS, fontSize:15.5, bold:true, color:INK, margin:0 });
    s.addText(r[1], { x:6.0, y:y+0.13, w:6.4, h:0.65, valign:"middle", fontFace:SANS, fontSize:13.5, color:MUTED, lineSpacingMultiple:1.0, margin:0 });
    y+=1.03;
  });
  s.addNotes("The plan, and why it scales. Near term: resolve the baseline confound and add real statistics to the drift. Then the leverage — there are ~14 conditioned animals in the Drive. The pipeline pools them, so each one sharpens the result. And up-conditioning and freely-running animals are natural controls: they should drift in the opposite direction, or barely at all. That's how we turn today's foundation into a claim.");
})();

// ============================================================ 14 · DISCUSSION (dark)
(() => {
  const s = p.addSlide(); bg(s, DARK);
  s.addText("WHERE I NEED YOUR READ", { x:0.8, y:0.6, w:11, h:0.4, fontFace:SANS, fontSize:14, bold:true, color:TEAL, charSpacing:3, margin:0 });
  s.addText("Four neuro calls — not code", { x:0.8, y:1.05, w:11.5, h:0.7, fontFace:SERIF, fontSize:30, bold:true, color:WHITE, margin:0 });
  const qs = [
    ["Baseline definition","Given the setup-period confound, how should we define a clean behavioral baseline for Animal 9?"],
    ["The H-reflex label","Confirm: mean rectified amplitude, 6–9 ms window — is that the measure you want us predicting?"],
    ["What would convince you","What controls make the cortical drift believable — up-conditioning reversing it? freely-running as a null?"],
    ["Which animals next","Of the ~14 in the Drive, which should we prioritize converting and pooling?"],
  ];
  let x=0.8, y=2.1;
  qs.forEach((q,i)=>{
    const cx = x + (i%2)*6.05, cy = y + Math.floor(i/2)*2.35;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x:cx, y:cy, w:5.75, h:2.05, rectRadius:0.09,
      fill:{color:"1E293B"}, line:{color:"334155", width:1} });
    numCircle(s, cx+0.3, cy+0.3, i+1, i<2?VIOLET:TEAL);
    s.addText(q[0], { x:cx+0.95, y:cy+0.32, w:4.6, h:0.5, fontFace:SANS, fontSize:16, bold:true, color:WHITE, margin:0 });
    s.addText(q[1], { x:cx+0.32, y:cy+0.92, w:5.15, h:1.0, fontFace:SANS, fontSize:13, color:"CBD5E1", lineSpacingMultiple:1.05, margin:0 });
  });
  s.addText("Code + all figures on GitHub — happy to add you and Tarun as collaborators.",
    { x:0.8, y:6.95, w:11.7, h:0.4, fontFace:SANS, fontSize:13, italic:true, color:FAINT, margin:0 });
  s.addNotes("Hand the conversation over. The two that actually block me are the first two: how to define a clean baseline given the setup confound, and confirming the H-reflex label. Then the bigger-picture ones: what controls would convince you it's real, and which animals to prioritize. Everything's on GitHub for you and Tarun.");
})();

p.writeFile({ fileName: "slides/HROC_Carp_Update_Animal9.pptx" }).then(f => console.log("WROTE", f));
