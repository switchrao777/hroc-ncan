// HROC — team presentation (Carp's group, target 21 Aug 2026)
// Audience: not ML-literate but scientifically sophisticated. Carp asked for an
// intermediate level: explain the pipeline with a figure, don't gloss, don't drown.
// Run: NODE_PATH=$(npm root -g) node slides/build_team_deck.js
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "Suchith Rao & Tarun Senthil";
p.title = "Cortical Correlates of H-Reflex Operant Conditioning";

const DARK="0F172A", INK="1E293B", MUTED="64748B", FAINT="94A3B8";
const VIOLET="6D28D9", TEAL="0D9488", AMBER="D97706", GREEN="16A34A", RED="DC2626", BLUE="2563EB";
const CARDLINE="E2E8F0", WHITE="FFFFFF", CARD="F1F5F9";
const SERIF="Cambria", SANS="Calibri";
const IMG = f => "outputs/" + f;
const sh = () => ({type:"outer",color:"0F172A",blur:9,offset:3,angle:90,opacity:0.14});

const bg=(s,c)=>{s.background={color:c};};
const title=(s,t)=>s.addText(t,{x:0.7,y:0.5,w:12.1,h:0.75,fontFace:SERIF,fontSize:28,bold:true,color:INK,margin:0});
const kick=(s,t,c)=>s.addText(t.toUpperCase(),{x:0.72,y:0.42,w:12,h:0.3,fontFace:SANS,fontSize:12,bold:true,color:c||TEAL,charSpacing:3,margin:0});
const card=(s,x,y,w,h,f)=>s.addShape(p.shapes.ROUNDED_RECTANGLE,{x,y,w,h,rectRadius:0.09,fill:{color:f||WHITE},line:{color:CARDLINE,width:1},shadow:sh()});
function num(s,x,y,n,c){const d=0.48;
  s.addShape(p.shapes.OVAL,{x,y,w:d,h:d,fill:{color:c},line:{type:"none"}});
  s.addText(String(n),{x,y,w:d,h:d,align:"center",valign:"middle",fontFace:SANS,fontSize:16,bold:true,color:WHITE,margin:0});}
const img=(s,f,x,y,w,h)=>s.addImage({path:IMG(f),x,y,w,h,sizing:{type:"contain",w,h}});
const fit=(r,mw,mh)=>{let w=mw,h=w/r; if(h>mh){h=mh;w=h*r;} return [w,h];};

// ---------------------------------------------------------------- 1 TITLE
(()=>{const s=p.addSlide(); bg(s,DARK);
 s.addShape(p.shapes.OVAL,{x:11.0,y:1.0,w:1.5,h:1.5,fill:{color:VIOLET,transparency:55},line:{type:"none"}});
 s.addShape(p.shapes.OVAL,{x:11.75,y:1.85,w:1.0,h:1.0,fill:{color:TEAL,transparency:45},line:{type:"none"}});
 s.addText("NCAN · WADSWORTH · SUMMER 2026",{x:0.8,y:1.5,w:10,h:0.4,fontFace:SANS,fontSize:13,bold:true,color:TEAL,charSpacing:3,margin:0});
 s.addText("Does cortex track the reflex\nas the spinal cord learns?",{x:0.8,y:2.0,w:11.4,h:2.0,fontFace:SERIF,fontSize:40,bold:true,color:WHITE,lineSpacingMultiple:0.98,margin:0});
 s.addText("Machine learning on 20-year-old paired EMG + ECoG recordings.\nSix animals, 2.7 million trials.",
   {x:0.82,y:4.15,w:11,h:0.9,fontFace:SANS,fontSize:17,color:"CBD5E1",lineSpacingMultiple:1.1,margin:0});
 s.addText([{text:"Suchith Rao & Tarun Senthil",options:{bold:true,color:WHITE}},
   {text:"    •    with Dr. Carp    •    21 August 2026",options:{color:FAINT}}],
   {x:0.82,y:6.5,w:11,h:0.4,fontFace:SANS,fontSize:14,margin:0});
 s.addNotes("Introduce yourselves and the collaboration. We're the machine-learning side of this project, working with Dr Carp on the operant conditioning data. Over the summer we built a pipeline to decode the old paired EMG and ECoG recordings and asked whether cortical activity changes as the spinal cord learns. Six animals, 2.7 million trials.");})();

// ---------------------------------------------------------------- 2 BACKGROUND
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Background"); title(s,"The paradigm, and the open question");
 card(s,0.7,1.9,5.85,2.3,CARD);
 s.addText("What the lab does",{x:1.0,y:2.15,w:5,h:0.35,fontFace:SANS,fontSize:15,bold:true,color:INK,margin:0});
 s.addText("Rats are rewarded for making the soleus H-reflex smaller (down-conditioning) or larger (up). Over weeks the spinal cord itself changes. Success is a ≥20% shift.",
   {x:1.0,y:2.6,w:5.3,h:1.4,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.05,margin:0});
 card(s,6.75,1.9,5.85,2.3,"F5F3FF");
 s.addText("The open question",{x:7.05,y:2.15,w:5,h:0.35,fontFace:SANS,fontSize:15,bold:true,color:VIOLET,margin:0});
 s.addText("Boulay et al. showed cortical activity relates to reflex size. Does that relationship CHANGE as the animal learns — and can we see it on single trials?",
   {x:7.05,y:2.6,w:5.3,h:1.4,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.05,margin:0});
 card(s,0.7,4.45,11.9,2.2,CARD);
 s.addText("Why machine learning helps here",{x:1.05,y:4.7,w:6,h:0.35,fontFace:SANS,fontSize:15,bold:true,color:TEAL,margin:0});
 s.addText("Rather than hand-picking features from the cortical trace, we let a neural network learn its own compact description of each trial, then test what that description can predict. With 2.7 million trials, that is tractable in a way manual feature engineering is not.",
   {x:1.05,y:5.15,w:11.2,h:1.3,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addNotes("Quick background for anyone not on this project. The lab conditions rats to raise or lower the soleus H-reflex over weeks; twenty percent counts as success. Chad Boulay's paper showed cortical activity relates to reflex size. Our question is whether that relationship changes with learning and whether it's visible on single trials. Machine learning helps because instead of hand-picking features we let the network learn its own description of each trial, and with 2.7 million trials that's tractable.");})();

// ---------------------------------------------------------------- 3 PIPELINE
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Methods"); title(s,"The pipeline, end to end");
 const steps=[["Raw 2006 database","MyISAM tables from the Elizan III system, loaded into a local MySQL server.",VIOLET],
  ["Decode each trial","Little-endian int16, two channels: soleus EMG and cortical ECoG. 150 samples at 5 kHz = 30 ms.",VIOLET],
  ["Measure the physiology","M-wave (2–4 ms), H-reflex (6–9 ms), and pre-stimulus background — all background-subtracted.",TEAL],
  ["Store as Zarr","One array store per animal: signals, labels, timestamps, covariates. ~2.7M trials total.",TEAL],
  ["Learn a representation","Autoencoder compresses each cortical trace to 48 numbers, trained across animals with no labels.",AMBER],
  ["Test what it predicts","Freeze it, then ask what the representation says about the reflex — with controls.",AMBER]];
 let y=1.9;
 steps.forEach((st,i)=>{card(s,0.7,y,11.9,0.78);
  num(s,0.95,y+0.15,i+1,st[2]);
  s.addText(st[0],{x:1.6,y:y+0.08,w:3.3,h:0.62,valign:"middle",fontFace:SANS,fontSize:14.5,bold:true,color:INK,margin:0});
  s.addText(st[1],{x:5.0,y:y+0.08,w:7.3,h:0.62,valign:"middle",fontFace:SANS,fontSize:12.5,color:MUTED,lineSpacingMultiple:1.0,margin:0});
  y+=0.86;});
 s.addText("Everything is scripted and reproducible; one command per animal.",
   {x:0.72,y:7.05,w:11.9,h:0.35,fontFace:SANS,fontSize:12.5,italic:true,color:MUTED,margin:0});
 s.addNotes("This is the data flow. We load the original 2006 MyISAM tables into a local MySQL server, decode each trial — and one thing worth flagging, the format is little-endian, which contradicts the lab's own decoder docstring; decoding it the documented way produces noise. Each trial is two channels, soleus EMG and cortical ECoG, 150 samples at 5 kilohertz. We measure M-wave, H-reflex and pre-stimulus background, store everything as Zarr, then train an autoencoder that compresses each cortical trace to 48 numbers with no labels. Then we freeze it and test what it predicts.");})();

// ---------------------------------------------------------------- 4 MEASUREMENT
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Methods · measurement",TEAL); title(s,"Getting the reflex measurement right");
 const rows=[["Raw H is not interpretable","Reflex size scales with stimulus strength. Our M-wave drifted 100→450 µV over weeks, which alone made an early result look backwards.",RED],
  ["Control for stimulus","The M-wave is the direct muscle response in the same trace — a per-trial receipt for how much stimulus arrived.",TEAL],
  ["Control for excitability","Background EMG in the 20 ms before the stimulus. High background means an excited motoneuron pool and a larger H — not learning.",TEAL],
  ["Subtract background","We use mean rectified amplitude, and rectified background does not cancel; left in, it pulls H/M toward 1 and can hide a real effect.",AMBER]];
 let y=1.95;
 rows.forEach(r=>{card(s,0.7,y,11.9,1.2);
  s.addShape(p.shapes.OVAL,{x:1.05,y:y+0.48,w:0.22,h:0.22,fill:{color:r[2]},line:{type:"none"}});
  s.addText(r[0],{x:1.5,y:y+0.14,w:3.5,h:0.9,valign:"middle",fontFace:SANS,fontSize:14.5,bold:true,color:INK,lineSpacingMultiple:1.0,margin:0});
  s.addText(r[1],{x:5.1,y:y+0.14,w:7.2,h:0.9,valign:"middle",fontFace:SANS,fontSize:12.5,color:MUTED,lineSpacingMultiple:1.04,margin:0});
  y+=1.32;});
 s.addText("Every number in this talk is corrected for stimulus and background.",
   {x:0.72,y:7.0,w:11.9,h:0.35,fontFace:SANS,fontSize:13,italic:true,bold:true,color:VIOLET,margin:0});
 s.addNotes("This slide matters because it took us a while to get right. Raw H-reflex amplitude is not interpretable on its own because it scales with stimulus strength — and our M-wave drifted from about 100 to 450 microvolts over the recording, which alone made one early result look backwards. So we control for stimulus using the M-wave in the same trace, and for motoneuron excitability using the background EMG in the twenty milliseconds before the stimulus. We also subtract background from both measures, because rectified background doesn't cancel and it pulls the H over M ratio toward one. Every number from here on has both corrections applied.");})();

// ---------------------------------------------------------------- 5 ANIMALS
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Results · dataset"); title(s,"Six animals, both directions");
 const stats=[["6","animals",VIOLET],["2.7M","trials",TEAL],["3 / 3","down / up",AMBER],["45–210","days each",GREEN]];
 let x=0.7;
 stats.forEach(([n,l,c])=>{card(s,x,1.9,2.87,1.75);
  s.addText(n,{x:x,y:2.08,w:2.87,h:0.85,align:"center",fontFace:SERIF,fontSize:34,bold:true,color:c,margin:0});
  s.addText(l,{x:x,y:2.92,w:2.87,h:0.45,align:"center",fontFace:SANS,fontSize:13,color:MUTED,margin:0}); x+=3.05;});
 card(s,0.7,3.95,11.9,1.5,CARD);
 s.addText("Finding good up-conditioned animals without downloading everything",{x:1.05,y:4.15,w:8,h:0.35,fontFace:SANS,fontSize:14.5,bold:true,color:VIOLET,margin:0});
 s.addText("The log files are tiny. The reward criterion is a success readout — the experimenter raises the bar when the rat beats it. Animal 4's went 150→220, animal 3's 90→190. Animals 1 and 6 had theirs lowered, so they failed. We only downloaded the ones that worked.",
   {x:1.05,y:4.55,w:11.2,h:0.8,fontFace:SANS,fontSize:13,color:INK,lineSpacingMultiple:1.04,margin:0});
 card(s,0.7,5.65,11.9,1.35,"FEF3E2");
 s.addText("One animal excluded",{x:1.05,y:5.82,w:6,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:AMBER,margin:0});
 s.addText("Animal 12's pre-stimulus cortical signal is 2.8 µV, versus 106–128 µV in the others — the ECoG electrode was effectively dead. Its apparent weak conditioning was a recording failure.",
   {x:1.05,y:6.2,w:11.2,h:0.7,fontFace:SANS,fontSize:13,color:INK,lineSpacingMultiple:1.04,margin:0});
 s.addNotes("Six animals, three down and three up, ranging from 45 to 210 days of recording. Worth explaining how we found the up-conditioned animals: rather than download forty gigabytes hunting, we read only the log files, which are tiny. The reward criterion is effectively a success readout — the experimenter raises the bar when the rat is beating it. Animal 4's went from 150 to 220 and animal 3's from 90 to 190, so those two learned. Animals 1 and 6 had theirs lowered, so they failed. We also excluded animal 12 — its pre-stimulus cortical signal is under three microvolts against 106 to 128 in the others, so that electrode was dead.");})();

// ---------------------------------------------------------------- 6 BEHAVIOUR
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Result 1 · behaviour",GREEN); title(s,"Conditioning works, in both directions");
 const [w,h]=fit(2.6,7.7,4.0); img(s,"updown/updown_contrast.png",0.5,1.95,w,h);
 card(s,8.5,2.1,4.1,4.15,"F0FDF4");
 s.addText("The positive control",{x:8.75,y:2.35,w:3.6,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:GREEN,margin:0});
 s.addText("Each animal aligned to its own training start. Red (up) rises, blue (down) falls — a 72 percentage-point group separation.",
   {x:8.75,y:2.8,w:3.65,h:1.4,fontFace:SANS,fontSize:13,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("Three of five animals clear the lab's 20% criterion in the trained direction.",
   {x:8.75,y:4.3,w:3.65,h:1.0,fontFace:SANS,fontSize:13,bold:true,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("The two that don't become internal controls later in the talk.",
   {x:8.75,y:5.35,w:3.65,h:0.85,fontFace:SANS,fontSize:12,italic:true,color:MUTED,lineSpacingMultiple:1.04,margin:0});
 s.addNotes("We lead with behaviour because it's the check that has to pass before anything else counts. Each animal is aligned to its own training start day. Up animals rise, down animals fall, a seventy-two point separation between groups. Three of five clear the twenty percent criterion in the trained direction. The two that don't come back later as internal controls — that's actually useful.");})();

// ---------------------------------------------------------------- 7 DRIFT NEGATIVE
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Result 2 · a negative result",AMBER); title(s,"Average cortical state drifts — but not from learning");
 card(s,0.7,1.9,11.9,1.35,CARD);
 s.addText("Our first approach was to ask whether the average cortical state moves across conditioning. It does. But three controls say that movement is the recording changing over weeks, not learning.",
   {x:1.05,y:2.08,w:11.2,h:1.0,valign:"middle",fontFace:SANS,fontSize:14.5,color:INK,lineSpacingMultiple:1.05,margin:0});
 const ctrl=[["Baseline sham","Split baseline-only data as a fake experiment. Nothing happened, so it should be flat.","Drifts as much as the real thing — 5 of 6 animals",RED],
  ["Randomised order","Shuffle which trial belongs to which day. Breaks time structure, keeps the numbers.","Null ≈ 0 — so the metric itself is sound",GREEN],
  ["Direction contrast","Electrode drift is direction-independent; learning is not.","Up 21.9 vs down 34.6, t = −1.01, n.s.",RED]];
 let y=3.5;
 ctrl.forEach(c=>{card(s,0.7,y,11.9,1.05);
  s.addText(c[0],{x:1.05,y:y+0.12,w:2.6,h:0.8,valign:"middle",fontFace:SANS,fontSize:14,bold:true,color:INK,margin:0});
  s.addText(c[1],{x:3.75,y:y+0.12,w:4.6,h:0.8,valign:"middle",fontFace:SANS,fontSize:12,color:MUTED,lineSpacingMultiple:1.03,margin:0});
  s.addText(c[2],{x:8.5,y:y+0.12,w:3.8,h:0.8,valign:"middle",fontFace:SANS,fontSize:12,bold:true,color:c[3],lineSpacingMultiple:1.03,margin:0});
  y+=1.17;});
 s.addText("In a single animal, learning and electrode drift are both smooth in time — they cannot be separated. That is a design limit, not a data problem.",
   {x:0.72,y:7.02,w:11.9,h:0.35,fontFace:SANS,fontSize:12.5,italic:true,color:VIOLET,margin:0});
 s.addNotes("Our first approach was the obvious one: does the average cortical state move across conditioning. It does move. But three controls all say the same thing. First, if you take baseline-only data and split it as a fake experiment, it drifts as much as the real thing in five of six animals. Second — and this was Dr Carp's suggestion — if you shuffle which trial belongs to which day, the null is essentially zero, so the metric itself is fine. Third, electrode drift doesn't care which direction you trained the animal, and there's no direction difference. The underlying issue is that in one animal learning and electrode drift are both smooth functions of time, so they can't be separated. That's a design limit, not a data problem.");})();

// ---------------------------------------------------------------- 8 THE PIVOT
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Approach",VIOLET); title(s,"A question that drift cannot contaminate");
 card(s,0.7,1.95,5.85,1.85,CARD);
 s.addText("Instead of",{x:1.0,y:2.15,w:5,h:0.35,fontFace:SANS,fontSize:13,bold:true,color:MUTED,margin:0});
 s.addText("\"Did the average cortical state move over weeks?\"",{x:1.0,y:2.55,w:5.3,h:1.0,fontFace:SERIF,fontSize:16,italic:true,color:INK,lineSpacingMultiple:1.05,margin:0});
 card(s,6.75,1.95,5.85,1.85,"F5F3FF");
 s.addText("We ask",{x:7.05,y:2.15,w:5,h:0.35,fontFace:SANS,fontSize:13,bold:true,color:VIOLET,margin:0});
 s.addText("\"Can cortex predict this trial's reflex size?\"",{x:7.05,y:2.55,w:5.3,h:1.0,fontFace:SERIF,fontSize:16,bold:true,italic:true,color:VIOLET,lineSpacingMultiple:1.05,margin:0});
 card(s,0.7,4.1,11.9,1.7,"F0FDF4");
 s.addText("Why drift cannot fake this",{x:1.05,y:4.3,w:6,h:0.35,fontFace:SANS,fontSize:15,bold:true,color:GREEN,margin:0});
 s.addText("The decoder is trained and tested inside a single 5-day block, by cross-validation. A slow electrode change shifts the training and test trials together, so it cancels. Drift can move a mean; it cannot create trial-by-trial predictive structure within a block.",
   {x:1.05,y:4.72,w:11.2,h:1.0,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.05,margin:0});
 const extra=[["Stimulus and background removed inside each block",VIOLET],
  ["Compared against a shuffle of the same block's labels",VIOLET]];
 let y=6.05; extra.forEach(e=>{card(s,0.7,y,11.9,0.62);
  s.addShape(p.shapes.OVAL,{x:1.05,y:y+0.19,w:0.22,h:0.22,fill:{color:e[1]},line:{type:"none"}});
  s.addText(e[0],{x:1.5,y:y+0.05,w:10.6,h:0.52,valign:"middle",fontFace:SANS,fontSize:13.5,color:INK,margin:0}); y+=0.72;});
 s.addNotes("So rather than keep fighting that confound, we changed the question. Instead of asking whether the average state moved, we ask whether cortex can predict this particular trial's reflex size. The key design point — and this is the part I'd like feedback on — is that the decoder is trained and tested inside a single five-day block by cross-validation. A slow electrode change shifts training and test trials together, so it cancels. Drift can move a mean; it can't create trial-by-trial predictive structure inside a block. We also remove stimulus and background inside each block, and compare against a shuffle of that block's own labels.");})();

// ---------------------------------------------------------------- 9 COUPLING RESULT
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Result 3 · the positive finding",GREEN); title(s,"Cortex predicts reflex size on single trials");
 const [w,h]=fit(1.73,7.4,4.1); img(s,"coupling/coupling_group.png",0.55,1.95,w,h);
 card(s,8.3,2.1,4.3,4.15,"F0FDF4");
 s.addText("Present in every animal",{x:8.55,y:2.35,w:3.8,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:GREEN,margin:0});
 s.addText("Cross-validated R² is above the shuffle null in every animal and nearly every block, after stimulus and background are removed.",
   {x:8.55,y:2.8,w:3.85,h:1.3,fontFace:SANS,fontSize:13,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("Conservative estimate: R² ≈ 0.04\nnull ≈ −0.01",
   {x:8.55,y:4.2,w:3.85,h:0.9,fontFace:SERIF,fontSize:17,bold:true,color:INK,lineSpacingMultiple:1.1,margin:0});
 s.addText("Small, but consistent and not explainable by stimulus, muscle tone, or drift.",
   {x:8.55,y:5.2,w:3.85,h:1.0,fontFace:SANS,fontSize:12.5,italic:true,color:MUTED,lineSpacingMultiple:1.05,margin:0});
 s.addNotes("Here's the positive result. Cross-validated R-squared sits above the shuffle null in every animal and nearly every block. I want to be careful about the number: our conservative estimate, removing stimulus and background inside each block, is about 0.04. An earlier, looser version of the analysis gave larger numbers, but it removed the covariates globally rather than block by block, and that leaves stimulus variance behind. So 0.04 is the number we stand behind. It is small, but it's consistent across animals and it isn't explainable by stimulus, muscle tone, or drift.");})();

// ---------------------------------------------------------------- 10 VARIANCE PARTITION
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Result 3 · in context"); title(s,"What actually explains reflex size?");
 const rows=[["Stimulus (M-wave)","47%",VIOLET,"By far the dominant factor — how much stimulus reached the muscle."],
  ["Background excitability","1%",TEAL,"Small on its own, but a necessary control."],
  ["Cortical activity, alone","21%",BLUE,"Mostly overlapping with stimulus, since stimulus drives both."],
  ["Cortex, unique contribution","2%",GREEN,"What cortex adds once stimulus and background are already known."],
  ["Unexplained","51%",MUTED,"Trial-to-trial variability we cannot yet account for."]];
 let y=1.95;
 rows.forEach(r=>{card(s,0.7,y,11.9,0.95,r[0]==="Cortex, unique contribution"?"F0FDF4":WHITE);
  s.addText(r[0],{x:1.05,y:y+0.15,w:4.4,h:0.65,valign:"middle",fontFace:SANS,fontSize:14.5,bold:true,color:INK,margin:0});
  s.addText(r[1],{x:5.6,y:y+0.15,w:1.5,h:0.65,valign:"middle",align:"right",fontFace:SERIF,fontSize:22,bold:true,color:r[2],margin:0});
  s.addText(r[3],{x:7.4,y:y+0.15,w:4.9,h:0.65,valign:"middle",fontFace:SANS,fontSize:12,color:MUTED,lineSpacingMultiple:1.02,margin:0});
  y+=1.05;});
 s.addText("Percentages are variance in H-reflex amplitude explained, cross-validated within blocks, averaged over five animals.",
   {x:0.72,y:7.15,w:11.9,h:0.35,fontFace:SANS,fontSize:12,italic:true,color:MUTED,margin:0});
 s.addNotes("Dr Carp asked us to partition the variance, and this is the answer. The stimulus dominates at about 47 percent. Background is about 1 percent. Cortex on its own accounts for 21 percent, but most of that overlaps with the stimulus, because the stimulus drives both the cortical evoked response and the reflex. Once stimulus and background are already in the model, cortex adds about 2 percent uniquely. And roughly half the variance is still unexplained, which is normal for single-trial physiology. So the honest claim is a small but real unique cortical contribution.");})();

// ---------------------------------------------------------------- 11 CROSSTALK
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Result 4 · is it really cortical?",TEAL); title(s,"Ruling out muscle contamination");
 const [w,h]=fit(2.6,7.6,3.7); img(s,"verify/verification.png",0.5,2.05,w,h);
 card(s,8.35,2.1,4.25,4.2,CARD);
 s.addText("The objection",{x:8.6,y:2.35,w:3.7,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:AMBER,margin:0});
 s.addText("Both channels record at once, so the ECoG electrode might simply be picking up muscle activity.",
   {x:8.6,y:2.78,w:3.75,h:1.0,fontFace:SANS,fontSize:13,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("The test",{x:8.6,y:3.9,w:3.7,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:TEAL,margin:0});
 s.addText("Correlate cortical against muscle power, band by band. Muscle artefact lives at high frequency, so contamination would show up there.",
   {x:8.6,y:4.3,w:3.75,h:1.2,fontFace:SANS,fontSize:13,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("Above 100 Hz: r = +0.06.\nNo contamination.",
   {x:8.6,y:5.55,w:3.75,h:0.8,fontFace:SANS,fontSize:14,bold:true,color:GREEN,lineSpacingMultiple:1.1,margin:0});
 s.addNotes("The obvious objection is that both channels are recorded simultaneously, so maybe the ECoG electrode is just picking up muscle. Dr Carp suggested the test: correlate cortical power against muscle power and see how much coordination there is. Muscle artefact lives at high frequency, so that's where contamination would show. Above 100 hertz the correlation is plus 0.06 — essentially zero. The low bands are slightly negative. And the lead-lag check has cortex marginally leading muscle, which is the acceptable direction. So we don't think this is contamination.");})();

// ---------------------------------------------------------------- 12 SCALING
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Result 5 · the internal control",VIOLET); title(s,"Does the effect scale with how much they learned?");
 const [w,h]=fit(2.6,7.6,3.7); img(s,"scaling/scaling.png",0.5,2.05,w,h);
 card(s,8.35,2.1,4.25,4.2,"F5F3FF");
 s.addText("The logic",{x:8.6,y:2.35,w:3.7,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:VIOLET,margin:0});
 s.addText("Animals differ in how much they learned, and two failed outright. If the cortical effect is tied to conditioning, it should track learning — and be absent in the animals that failed.",
   {x:8.6,y:2.78,w:3.75,h:1.6,fontFace:SANS,fontSize:13,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("r = +0.64 between learning and the change in coupling.",
   {x:8.6,y:4.5,w:3.75,h:0.9,fontFace:SANS,fontSize:14,bold:true,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("Encouraging direction, but n = 5 — not significant. This is the analysis more animals would power.",
   {x:8.6,y:5.4,w:3.75,h:0.9,fontFace:SANS,fontSize:12,italic:true,color:AMBER,lineSpacingMultiple:1.04,margin:0});
 s.addNotes("This was Dr Carp's suggestion and I think it's the most promising thing we have. The animals differ in how much they learned, and two of them failed to condition at all — those become a built-in negative control. If the cortical effect is really tied to conditioning, it should scale with learning and be absent in the failures. The correlation between learning and the change in coupling is plus 0.64, which is the right direction, and the two failed animals show no increase. But with five animals it's not significant. This is exactly the analysis that adding the remaining animals would power.");})();

// ---------------------------------------------------------------- 13 SUMMARY
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Summary"); title(s,"Where this stands");
 const items=[["Bidirectional conditioning","SOLID",GREEN,"Reproduced with full stimulus and background control. Three of five animals clear the 20% criterion."],
  ["Single-trial cortical coupling","REAL, SMALL",TEAL,"R² ≈ 0.04 over a ≈0 null, in every animal. Drift-immune by design; contamination ruled out."],
  ["Average-state drift = learning","NO",AMBER,"Three independent controls agree it reflects recording change. Worth reporting as a caution."]];
 let x=0.7;
 items.forEach(([t,badge,col,d])=>{card(s,x,2.0,3.87,4.3);
  s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:x+0.3,y:2.3,w:2.6,h:0.5,rectRadius:0.1,fill:{color:col},line:{type:"none"}});
  s.addText(badge,{x:x+0.3,y:2.3,w:2.6,h:0.5,align:"center",valign:"middle",fontFace:SANS,fontSize:12,bold:true,color:WHITE,charSpacing:1,margin:0});
  s.addText(t,{x:x+0.3,y:3.0,w:3.3,h:0.8,fontFace:SANS,fontSize:15.5,bold:true,color:INK,lineSpacingMultiple:1.0,margin:0});
  s.addText(d,{x:x+0.3,y:3.95,w:3.35,h:2.2,fontFace:SANS,fontSize:12.5,color:MUTED,lineSpacingMultiple:1.07,margin:0}); x+=4.08;});
 s.addNotes("To summarise. Bidirectional conditioning is solid and reproduced with full control. The single-trial cortical coupling is real but small — R-squared around 0.04 over a zero null, present in every animal, immune to drift by design, and we've ruled out muscle contamination. And the average-state drift question is a no, with three independent controls agreeing, which we think is worth reporting as a caution to anyone attempting this analysis.");})();

// ---------------------------------------------------------------- 14 NEXT
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Next",TEAL); title(s,"What would strengthen this");
 const road=[["Add the remaining animals","7, 8, 13, 14, 15 are scanned and ready. The lab aims for ~10 per group; we have 5 usable.",VIOLET],
  ["Power the scaling test","With ~10 animals the learning-vs-coupling correlation becomes a real test rather than a hint.",VIOLET],
  ["Frequency-resolved coupling","Which bands carry the reflex information? Sharpens both the result and the contamination argument.",TEAL],
  ["Time course","Does cortical change lead or follow the behavioural change? Carp's suggestion, and mechanistically the interesting question.",TEAL]];
 let y=2.1;
 road.forEach((r,i)=>{card(s,0.7,y,11.9,1.0);
  num(s,0.98,y+0.26,i+1,r[2]);
  s.addText(r[0],{x:1.66,y:y+0.18,w:3.9,h:0.65,valign:"middle",fontFace:SANS,fontSize:14.5,bold:true,color:INK,margin:0});
  s.addText(r[1],{x:5.7,y:y+0.18,w:6.6,h:0.65,valign:"middle",fontFace:SANS,fontSize:12.5,color:MUTED,lineSpacingMultiple:1.02,margin:0}); y+=1.12;});
 card(s,0.7,6.7,11.9,0.8,"F5F3FF");
 s.addText("Target venue: a machine-learning conference (ICML / NeurIPS), framed as an extension of Boulay et al.",
   {x:1.05,y:6.85,w:11.2,h:0.5,valign:"middle",fontFace:SANS,fontSize:13.5,bold:true,color:VIOLET,margin:0});
 s.addNotes("What would strengthen this. Adding the remaining animals is the main one — the lab aims for around ten per group and we have five usable. That's also what powers the scaling test. Then frequency-resolved coupling, which sharpens both the result and the contamination argument. And the time course question — does the cortical change lead or follow the behavioural change — which Dr Carp raised and is mechanistically the most interesting version. We're aiming at a machine-learning venue, framed as an extension of Chad's paper.");})();

// ---------------------------------------------------------------- 15 QUESTIONS
(()=>{const s=p.addSlide(); bg(s,DARK);
 s.addText("QUESTIONS FOR YOU",{x:0.8,y:0.6,w:11,h:0.4,fontFace:SANS,fontSize:14,bold:true,color:TEAL,charSpacing:3,margin:0});
 s.addText("Where we'd value your input",{x:0.8,y:1.05,w:11.5,h:0.7,fontFace:SERIF,fontSize:28,bold:true,color:WHITE,margin:0});
 const qs=[["Is a 2% unique cortical contribution meaningful?","It is small but consistent and survives every control we can think of. Is that a result worth publishing?"],
  ["Is the within-block design convincing?","Train and test inside one 5-day block so drift cancels. Does that satisfy you that the effect isn't recording change?"],
  ["What else could produce this?","We've ruled out stimulus, muscle tone, drift, and crosstalk. What are we missing?"],
  ["Is the negative result worth reporting?","Three controls say average-state drift reflects recording, not learning. Useful caution, or a distraction?"]];
 let x=0.8,y=2.1;
 qs.forEach((q,i)=>{const cx=x+(i%2)*6.05, cy=y+Math.floor(i/2)*2.35;
  s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:cx,y:cy,w:5.75,h:2.05,rectRadius:0.09,fill:{color:"1E293B"},line:{color:"334155",width:1}});
  num(s,cx+0.3,cy+0.3,i+1,i<2?VIOLET:TEAL);
  s.addText(q[0],{x:cx+0.92,y:cy+0.26,w:4.65,h:0.62,fontFace:SANS,fontSize:14,bold:true,color:WHITE,lineSpacingMultiple:0.95,margin:0});
  s.addText(q[1],{x:cx+0.32,y:cy+1.0,w:5.15,h:0.95,fontFace:SANS,fontSize:12,color:"CBD5E1",lineSpacingMultiple:1.05,margin:0});});
 s.addText("Code, figures and per-animal results: github.com/switchrao777/hroc-ncan",
   {x:0.8,y:6.95,w:11.7,h:0.4,fontFace:SANS,fontSize:12.5,italic:true,color:FAINT,margin:0});
 s.addNotes("Four things we'd value your input on. Whether a two percent unique cortical contribution is meaningful enough to publish. Whether the within-block design convinces you the effect isn't recording change. What else could produce this that we haven't ruled out. And whether the negative drift result is worth reporting. Everything is on GitHub.");})();

p.writeFile({fileName:"slides/HROC_Team_Presentation.pptx"}).then(f=>console.log("WROTE",f));
