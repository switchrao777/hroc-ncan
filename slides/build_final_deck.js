// HROC — 6-animal update deck for Dr. Carp (Aug 2026)
// Run: NODE_PATH=$(npm root -g) node slides/build_final_deck.js
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "Suchith Rao";
p.title = "HROC — Six-Animal Update";

const DARK="0F172A", INK="1E293B", MUTED="64748B", FAINT="94A3B8";
const VIOLET="6D28D9", TEAL="0D9488", AMBER="D97706", GREEN="16A34A", RED="DC2626";
const CARDLINE="E2E8F0", WHITE="FFFFFF", CARD="F1F5F9";
const SERIF="Cambria", SANS="Calibri";
const IMG = f => "outputs/" + f;
const sh = () => ({type:"outer",color:"0F172A",blur:9,offset:3,angle:90,opacity:0.14});

const bg=(s,c)=>{s.background={color:c};};
const title=(s,t)=>s.addText(t,{x:0.7,y:0.5,w:12.1,h:0.75,fontFace:SERIF,fontSize:29,bold:true,color:INK,margin:0});
const kick=(s,t,c)=>s.addText(t.toUpperCase(),{x:0.72,y:0.42,w:12,h:0.3,fontFace:SANS,fontSize:12.5,bold:true,color:c||TEAL,charSpacing:3,margin:0});
const card=(s,x,y,w,h,f)=>s.addShape(p.shapes.ROUNDED_RECTANGLE,{x,y,w,h,rectRadius:0.09,fill:{color:f||WHITE},line:{color:CARDLINE,width:1},shadow:sh()});
function num(s,x,y,n,c){const d=0.5;
  s.addShape(p.shapes.OVAL,{x,y,w:d,h:d,fill:{color:c},line:{type:"none"}});
  s.addText(String(n),{x,y,w:d,h:d,align:"center",valign:"middle",fontFace:SANS,fontSize:17,bold:true,color:WHITE,margin:0});}
const img=(s,f,x,y,w,h)=>s.addImage({path:IMG(f),x,y,w,h,sizing:{type:"contain",w,h}});
const fit=(r,mw,mh)=>{let w=mw,h=w/r; if(h>mh){h=mh;w=h*r;} return [w,h];};

// 1 TITLE
(()=>{const s=p.addSlide(); bg(s,DARK);
 s.addShape(p.shapes.OVAL,{x:11.1,y:1.0,w:1.4,h:1.4,fill:{color:VIOLET,transparency:55},line:{type:"none"}});
 s.addShape(p.shapes.OVAL,{x:11.8,y:1.8,w:0.95,h:0.95,fill:{color:TEAL,transparency:45},line:{type:"none"}});
 s.addText("HROC · NCAN · DEEP-LEARNING TRACK",{x:0.8,y:1.55,w:10,h:0.4,fontFace:SANS,fontSize:14,bold:true,color:TEAL,charSpacing:3,margin:0});
 s.addText("Six animals, both directions,\nand a positive result.",{x:0.8,y:2.1,w:11.4,h:2.0,fontFace:SERIF,fontSize:42,bold:true,color:WHITE,lineSpacingMultiple:0.98,margin:0});
 s.addText("Every control you asked for is now built and run.",{x:0.82,y:4.3,w:11,h:0.5,fontFace:SANS,fontSize:18,color:"CBD5E1",margin:0});
 s.addText([{text:"Suchith Rao",options:{bold:true,color:WHITE}},{text:"    •    for Dr. Carp    •    August 2026",options:{color:FAINT}}],
   {x:0.82,y:6.5,w:11,h:0.4,fontFace:SANS,fontSize:15,margin:0});
 s.addNotes("Since last time we doubled the dataset to six animals including three up-conditioned, built every control you asked for, and found a positive result by changing the question. I'll go through it in that order.");})();

// 2 WHAT YOU ASKED FOR
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Your asks, last meeting"); title(s,"All four are built and run");
 const items=[["Randomised-order control","Shuffle trial order, rerun the drift. If it still drifts, it's baked into the numbers.","PASSES — null ≈ 0 in every animal",GREEN],
  ["Pre-stimulus background","Motoneuron-pool excitability, 20 ms before the stimulus, from fragment 0.","Built — now a covariate everywhere",GREEN],
  ["Last 10 baseline days","Early baseline had settings changes, so only the last 10 days are the reference.","Adopted — visibly cleaner",GREEN],
  ["A strong up-conditioned animal","Animal 12 was weak. Scanned every log for reward-criterion progression.","Found animals 3 and 4",GREEN]];
 let y=2.0;
 items.forEach((it,i)=>{card(s,0.7,y,11.9,1.15);
  num(s,0.98,y+0.32,i+1,it[3]);
  s.addText(it[0],{x:1.66,y:y+0.14,w:3.5,h:0.85,valign:"middle",fontFace:SANS,fontSize:15,bold:true,color:INK,margin:0});
  s.addText(it[1],{x:5.3,y:y+0.14,w:4.5,h:0.85,valign:"middle",fontFace:SANS,fontSize:12.5,color:MUTED,lineSpacingMultiple:1.02,margin:0});
  s.addText(it[2],{x:9.95,y:y+0.14,w:2.5,h:0.85,valign:"middle",fontFace:SANS,fontSize:12,bold:true,color:it[3],margin:0});
  y+=1.27;});
 s.addNotes("First, your four asks. The randomized-order control passes cleanly, the null is essentially zero in every animal, so the drift metric is not an artifact of the numbers. Pre-stimulus background is extracted from fragment zero and is now a covariate in everything. We adopted the last-ten-days baseline and it visibly cleans things up. And we found strong up-conditioned animals by scanning the reward criterion in every log.");})();

// 3 THE DATASET NOW
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"The dataset"); title(s,"Six animals, both directions");
 const stats=[["6","animals processed",VIOLET],["2.7M","trials decoded",TEAL],["3 / 3","down / up",AMBER]];
 let x=0.7;
 stats.forEach(([n,l,c])=>{card(s,x,1.95,3.87,1.9);
  s.addText(n,{x:x,y:2.15,w:3.87,h:0.9,align:"center",fontFace:SERIF,fontSize:40,bold:true,color:c,margin:0});
  s.addText(l,{x:x,y:3.05,w:3.87,h:0.5,align:"center",fontFace:SANS,fontSize:14,color:MUTED,margin:0}); x+=4.08;});
 card(s,0.7,4.15,11.9,2.5,CARD);
 s.addText("How we found the up animals",{x:1.05,y:4.4,w:6,h:0.4,fontFace:SANS,fontSize:15,bold:true,color:VIOLET,margin:0});
 s.addText("We scanned every animal's log without downloading the data. The reward criterion (RW) is a success readout — you raise the bar when the rat beats it, lower it when it struggles.",
   {x:1.05,y:4.85,w:11.2,h:0.9,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.04,margin:0});
 s.addText([{text:"Animal 4: RW 150→220 (+47%)   •   Animal 3: RW 90→190 (+111%)",options:{bold:true,color:GREEN}},
   {text:"        Animals 1 and 6: criterion lowered — failed",options:{color:MUTED}}],
   {x:1.05,y:5.85,w:11.2,h:0.5,fontFace:SANS,fontSize:14,margin:0});
 s.addNotes("The dataset is now six animals, 2.7 million trials, three down and three up. Worth explaining how we picked the up animals: we scanned the logs only, no big downloads, and used the reward criterion as a success readout. Animals 4 and 3 had their bar raised substantially, so they genuinely learned. Animals 1 and 6 had it lowered, so they failed.");})();

// 4 BEHAVIOUR — BIDIRECTIONAL
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Result 1 · behaviour",GREEN); title(s,"Conditioning works in both directions");
 const [w,h]=fit(2.6,7.6,4.0); img(s,"updown/updown_contrast.png",0.5,1.95,w,h);
 card(s,8.45,2.1,4.15,4.2,"F0FDF4");
 s.addText("Left panel",{x:8.7,y:2.35,w:3.6,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:GREEN,margin:0});
 s.addText("Corrected H, aligned to each animal's own onset. Red (up) rises, blue (down) falls. Group difference +72 percentage points.",
   {x:8.7,y:2.8,w:3.65,h:1.5,fontFace:SANS,fontSize:13.5,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("Animals 9, 11 (down) and 3 (up) clear your 20% criterion.",
   {x:8.7,y:4.35,w:3.65,h:1.0,fontFace:SANS,fontSize:13.5,bold:true,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("All with stimulus and pre-stimulus background regressed out.",
   {x:8.7,y:5.4,w:3.65,h:0.8,fontFace:SANS,fontSize:12.5,italic:true,color:MUTED,lineSpacingMultiple:1.03,margin:0});
 s.addNotes("Behaviour first, because it's the positive control that has to hold. Every animal aligned to its own conditioning onset. Up animals' corrected H rises, down animals' falls, a seventy-two point group difference. Animals 9, 11 and 3 clear your twenty percent criterion. And this is with stimulus size and pre-stimulus background both regressed out, so it isn't stimulus drift.");})();

// 5 CORTICAL DRIFT — THE NEGATIVE
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Result 2 · the drift question, answered",AMBER); title(s,"Cortical drift is not conditioning");
 card(s,0.7,1.95,5.85,2.15,CARD);
 s.addText("The logic",{x:1.0,y:2.2,w:5,h:0.35,fontFace:SANS,fontSize:15,bold:true,color:INK,margin:0});
 s.addText("Recording drift doesn't care which direction you trained the animal. Conditioning does. So if the drift is learning, it must differ between up and down.",
   {x:1.0,y:2.62,w:5.3,h:1.3,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.05,margin:0});
 card(s,6.75,1.95,5.85,2.15,"FEF3E2");
 s.addText("It doesn't",{x:7.05,y:2.2,w:5,h:0.35,fontFace:SANS,fontSize:15,bold:true,color:AMBER,margin:0});
 s.addText("Up 21.9 vs down 34.6, t = −1.01, not significant. No direction dependence, so the drift is recording nonstationarity.",
   {x:7.05,y:2.62,w:5.3,h:1.3,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.05,margin:0});
 const rows=[["Sham null (baseline split)","fails in 5 of 6 animals",RED],
   ["Randomised-order null","passes — ≈0 everywhere",GREEN],
   ["Direction contrast","no difference (t = −1.01)",RED]];
 let y=4.35;
 rows.forEach(r=>{card(s,0.7,y,11.9,0.78);
  s.addText(r[0],{x:1.05,y:y+0.1,w:5.5,h:0.58,valign:"middle",fontFace:SANS,fontSize:14.5,bold:true,color:INK,margin:0});
  s.addText(r[1],{x:6.8,y:y+0.1,w:5.5,h:0.58,valign:"middle",fontFace:SANS,fontSize:14,color:r[2],bold:true,margin:0}); y+=0.9;});
 s.addText("Three independent controls agree. This question is answered.",
   {x:0.72,y:7.0,w:11.9,h:0.4,fontFace:SANS,fontSize:13,italic:true,color:MUTED,margin:0});
 s.addNotes("Now the drift question, and we can actually close it. The logic is that recording drift doesn't care which direction you trained the animal but conditioning does, so a real effect must differ between up and down. It doesn't — twenty-two versus thirty-five, not significant. Combined with the sham null failing in five of six animals, and your randomized-order control passing, three independent controls agree. The average cortical state drift is recording nonstationarity, not learning.");})();

// 6 THE PIVOT
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"So we changed the question",VIOLET); title(s,"A question drift can't contaminate");
 card(s,0.7,2.0,5.85,2.0,CARD);
 s.addText("Old question",{x:1.0,y:2.25,w:5,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:MUTED,margin:0});
 s.addText("\"Did the average cortical state move over weeks?\"",
   {x:1.0,y:2.7,w:5.3,h:1.1,fontFace:SERIF,fontSize:17,italic:true,color:INK,lineSpacingMultiple:1.05,margin:0});
 card(s,6.75,2.0,5.85,2.0,"F5F3FF");
 s.addText("New question",{x:7.05,y:2.25,w:5,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:VIOLET,margin:0});
 s.addText("\"Can cortex predict the reflex trial by trial?\"",
   {x:7.05,y:2.7,w:5.3,h:1.1,fontFace:SERIF,fontSize:17,italic:true,bold:true,color:VIOLET,lineSpacingMultiple:1.05,margin:0});
 const why=[["Train and test inside one 5-day block","Slow drift moves train and test together, so it cancels. Drift cannot create within-block predictive structure."],
   ["Stimulus and background removed first","So the decoder can't cheat by reading stimulus size or muscle tone."],
   ["Within-block label shuffle as the null","Real coupling has to beat a shuffle of its own block."]];
 let y=4.35;
 why.forEach((r,i)=>{card(s,0.7,y,11.9,0.85);
  num(s,0.98,y+0.18,i+1,VIOLET);
  s.addText(r[0],{x:1.66,y:y+0.12,w:4.0,h:0.62,valign:"middle",fontFace:SANS,fontSize:14,bold:true,color:INK,margin:0});
  s.addText(r[1],{x:5.8,y:y+0.12,w:6.5,h:0.62,valign:"middle",fontFace:SANS,fontSize:12.5,color:MUTED,lineSpacingMultiple:1.0,margin:0}); y+=0.97;});
 s.addNotes("So rather than keep fighting the confound, we changed the question. Instead of asking whether the average state moved, ask whether cortex predicts the reflex trial by trial. The key design point is that we train and test inside a single five-day block, so slow drift moves train and test together and cancels. Drift literally cannot manufacture within-block predictive structure. We also remove stimulus and background first, and use a within-block shuffle as the null.");})();

// 7 THE POSITIVE RESULT
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Result 3 · the positive finding",GREEN); title(s,"Cortex predicts the reflex, trial by trial");
 const [w,h]=fit(1.73,7.5,4.15); img(s,"coupling/coupling_group.png",0.55,1.95,w,h);
 card(s,8.4,2.1,4.2,4.2,"F0FDF4");
 s.addText("R² up to 0.35",{x:8.65,y:2.35,w:3.7,h:0.5,fontFace:SERIF,fontSize:24,bold:true,color:GREEN,margin:0});
 s.addText("against a shuffle null of ≈ 0. Present in every animal (0.02–0.19 mean).",
   {x:8.65,y:2.95,w:3.7,h:1.0,fontFace:SANS,fontSize:13.5,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("Cortical activity carries trial-by-trial information about the reflex that isn't stimulus intensity, isn't muscle tone, and isn't drift.",
   {x:8.65,y:4.05,w:3.7,h:1.6,fontFace:SANS,fontSize:13.5,bold:true,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("Whether it CHANGES with conditioning is not resolved (t = 0.69, n = 5).",
   {x:8.65,y:5.6,w:3.7,h:0.7,fontFace:SANS,fontSize:12,italic:true,color:AMBER,lineSpacingMultiple:1.03,margin:0});
 s.addNotes("And here's the positive result. Cross-validated R-squared reaches point three five, against a shuffle null of essentially zero, and it's present in every animal. So cortical activity carries trial-by-trial information about the reflex that is not stimulus intensity, not muscle tone, and not drift. What we can't yet say is whether that coupling changes with conditioning — that's a power problem, n of five.");})();

// 8 PRE-STIMULUS + CROSSTALK
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Result 4 · is it really cortical?",TEAL); title(s,"Pre-stimulus state and the crosstalk check");
 const [w,h]=fit(2.6,7.5,3.7); img(s,"prestim/prestim_coupling.png",0.55,2.05,w,h);
 card(s,8.4,2.1,4.2,4.2,CARD);
 s.addText("What we tested",{x:8.65,y:2.35,w:3.7,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:TEAL,margin:0});
 s.addText("Cortical band power measured entirely BEFORE the stimulus — it can't contain a response that hasn't happened.",
   {x:8.65,y:2.8,w:3.7,h:1.3,fontFace:SANS,fontSize:13,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("It works, but weakly: R² 0.010 vs null −0.002.",
   {x:8.65,y:4.2,w:3.7,h:0.7,fontFace:SANS,fontSize:13.5,bold:true,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("And pre-stimulus MUSCLE predicts better (0.022) — exactly what you predicted about motoneuron-pool excitability. A good check that the measurement is right.",
   {x:8.65,y:4.95,w:3.7,h:1.3,fontFace:SANS,fontSize:12.5,italic:true,color:MUTED,lineSpacingMultiple:1.05,margin:0});
 s.addNotes("We also asked whether cortical state before the stimulus predicts how big the reflex will be. It does, but weakly, R-squared point zero one against a null of essentially zero. Notably, pre-stimulus muscle activity predicts better than cortex — which is exactly what you said would happen with motoneuron pool excitability, and it's a good sign the measurement is working. So the main coupling result is not just pre-stimulus state.");})();

// 9 WHERE WE STAND
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Where we stand"); title(s,"Three findings, honestly rated");
 const items=[["Behaviour, bidirectional","SOLID",GREEN,"Conditioning works both directions, fully controlled for stimulus and background. Clears your 20% criterion in 3 animals."],
  ["Cortex→reflex coupling","REAL",TEAL,"R² up to 0.35 over a ≈0 null, drift-immune by design, present in every animal. This is the positive result."],
  ["Drift = learning?","ANSWERED: NO",AMBER,"Three independent controls agree the average-state drift is recording nonstationarity. Useful negative."]];
 let x=0.7;
 items.forEach(([t,badge,col,d])=>{card(s,x,2.0,3.87,4.4);
  s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:x+0.3,y:2.3,w:2.35,h:0.5,rectRadius:0.1,fill:{color:col},line:{type:"none"}});
  s.addText(badge,{x:x+0.3,y:2.3,w:2.35,h:0.5,align:"center",valign:"middle",fontFace:SANS,fontSize:12.5,bold:true,color:WHITE,charSpacing:1,margin:0});
  s.addText(t,{x:x+0.3,y:3.0,w:3.3,h:0.75,fontFace:SANS,fontSize:16.5,bold:true,color:INK,lineSpacingMultiple:1.0,margin:0});
  s.addText(d,{x:x+0.3,y:3.9,w:3.35,h:2.3,fontFace:SANS,fontSize:13,color:MUTED,lineSpacingMultiple:1.07,margin:0}); x+=4.08;});
 s.addNotes("Three findings, rated honestly. The behaviour is solid and bidirectional. The coupling result is real and drift-immune, and it's our positive finding. And the drift-equals-learning question is answered no, with three independent controls agreeing — which is a useful negative, not a failure.");})();

// 10 MOVING FORWARD
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Last few weeks","6D28D9"); title(s,"Plan for the rest of the project");
 const road=[["Add the remaining down animals","7, 8, 13, 14, 15 are logged and ready. n=5→10 is what resolves whether coupling changes with conditioning.",VIOLET],
   ["Finish the crosstalk test","Spectral/temporal dissociation for the post-stimulus coupling. The one thing a reviewer will demand.",VIOLET],
   ["Frequency-resolved coupling","Which bands carry the reflex information? Sharpens the result and the crosstalk argument.",TEAL],
   ["Write it up","Behaviour + coupling + the controls. Draft while the last animals process.",TEAL]];
 let y=2.1;
 road.forEach((r,i)=>{card(s,0.7,y,11.9,1.0);
  num(s,0.98,y+0.25,i+1,r[2]);
  s.addText(r[0],{x:1.66,y:y+0.18,w:4.0,h:0.65,valign:"middle",fontFace:SANS,fontSize:15,bold:true,color:INK,margin:0});
  s.addText(r[1],{x:5.8,y:y+0.18,w:6.5,h:0.65,valign:"middle",fontFace:SANS,fontSize:12.5,color:MUTED,lineSpacingMultiple:1.0,margin:0}); y+=1.12;});
 card(s,0.7,6.7,11.9,0.75,"F5F3FF");
 s.addText("The paper: bidirectional conditioning + a drift-immune cortical coupling result + the control methodology.",
   {x:1.05,y:6.82,w:11.2,h:0.5,valign:"middle",fontFace:SANS,fontSize:14,bold:true,color:VIOLET,margin:0});
 s.addNotes("For the last few weeks: add the remaining down animals, which are already logged and ready — going from five to ten animals is what resolves whether the coupling changes with conditioning. Finish the crosstalk test, which is the one thing a reviewer will demand. Do frequency-resolved coupling. And start writing. The paper is bidirectional conditioning, plus the drift-immune coupling result, plus the control methodology.");})();

// 11 QUESTIONS
(()=>{const s=p.addSlide(); bg(s,DARK);
 s.addText("WHERE I NEED YOUR READ",{x:0.8,y:0.6,w:11,h:0.4,fontFace:SANS,fontSize:14,bold:true,color:TEAL,charSpacing:3,margin:0});
 s.addText("Four questions",{x:0.8,y:1.05,w:11.5,h:0.7,fontFace:SERIF,fontSize:30,bold:true,color:WHITE,margin:0});
 const qs=[["Is the coupling result interesting to you?","Cortex predicts reflex size trial by trial, independent of stimulus and background. Is that a finding worth building the paper on?"],
  ["How would you rule out crosstalk?","Both channels record simultaneously. What would convince you the ECoG isn't picking up muscle?"],
  ["Which animals next?","7, 8, 13, 14, 15 are all down. Any more up-conditioned animals worth finding?"],
  ["Is the negative worth reporting?","Three controls say the average-state drift is recording, not learning. Worth publishing as a caution?"]];
 let x=0.8,y=2.1;
 qs.forEach((q,i)=>{const cx=x+(i%2)*6.05, cy=y+Math.floor(i/2)*2.35;
  s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:cx,y:cy,w:5.75,h:2.05,rectRadius:0.09,fill:{color:"1E293B"},line:{color:"334155",width:1}});
  num(s,cx+0.3,cy+0.3,i+1,i<2?VIOLET:TEAL);
  s.addText(q[0],{x:cx+0.95,y:cy+0.3,w:4.6,h:0.55,fontFace:SANS,fontSize:14.5,bold:true,color:WHITE,lineSpacingMultiple:0.95,margin:0});
  s.addText(q[1],{x:cx+0.32,y:cy+0.95,w:5.15,h:1.0,fontFace:SANS,fontSize:12,color:"CBD5E1",lineSpacingMultiple:1.05,margin:0});});
 s.addText("All code, figures and per-animal results are in the repo.",{x:0.8,y:6.95,w:11.7,h:0.4,fontFace:SANS,fontSize:13,italic:true,color:FAINT,margin:0});
 s.addNotes("Four things I'd like your read on. Whether the coupling result is interesting enough to build the paper on. How you'd rule out EMG crosstalk. Which animals to add next. And whether the negative drift result is worth reporting as a caution to the field.");})();

p.writeFile({fileName:"slides/HROC_SixAnimal_Update.pptx"}).then(f=>console.log("WROTE",f));
