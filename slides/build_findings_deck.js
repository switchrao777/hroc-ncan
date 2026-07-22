// HROC — 4-animal findings deck (null control result).
// Run: NODE_PATH=$(npm root -g) node slides/build_findings_deck.js  (from repo root)
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "Suchith Rao";
p.title = "HROC — Four-Animal Findings";

const DARK="0F172A", INK="1E293B", MUTED="64748B", FAINT="94A3B8";
const VIOLET="6D28D9", TEAL="0D9488", AMBER="D97706", GREEN="16A34A", RED="DC2626";
const CARDLINE="E2E8F0", WHITE="FFFFFF", CARD="F1F5F9";
const SERIF="Cambria", SANS="Calibri";
const IMG = f => "outputs/" + f;
const shadow = () => ({type:"outer",color:"0F172A",blur:9,offset:3,angle:90,opacity:0.14});

function bg(s,c){ s.background={color:c}; }
function title(s,t){ s.addText(t,{x:0.7,y:0.5,w:12,h:0.75,fontFace:SERIF,fontSize:30,bold:true,color:INK,margin:0}); }
function kicker(s,t,c){ s.addText(t.toUpperCase(),{x:0.72,y:0.42,w:12,h:0.3,fontFace:SANS,fontSize:12.5,bold:true,color:c||TEAL,charSpacing:3,margin:0}); }
function card(s,x,y,w,h,fill){ s.addShape(p.shapes.ROUNDED_RECTANGLE,{x,y,w,h,rectRadius:0.09,fill:{color:fill||WHITE},line:{color:CARDLINE,width:1},shadow:shadow()}); }
function numCircle(s,x,y,n,c){ const d=0.5;
  s.addShape(p.shapes.OVAL,{x,y,w:d,h:d,fill:{color:c},line:{type:"none"}});
  s.addText(String(n),{x,y,w:d,h:d,align:"center",valign:"middle",fontFace:SANS,fontSize:17,bold:true,color:WHITE,margin:0}); }
function img(s,f,x,y,w,h){ s.addImage({path:IMG(f),x,y,w,h,sizing:{type:"contain",w,h}}); }
function fit(r,mw,mh){ let w=mw,h=w/r; if(h>mh){h=mh;w=h*r;} return [w,h]; }

// 1 TITLE
(()=>{const s=p.addSlide(); bg(s,DARK);
 s.addShape(p.shapes.OVAL,{x:11.1,y:1.0,w:1.4,h:1.4,fill:{color:VIOLET,transparency:55},line:{type:"none"}});
 s.addShape(p.shapes.OVAL,{x:11.8,y:1.8,w:0.95,h:0.95,fill:{color:TEAL,transparency:45},line:{type:"none"}});
 s.addText("HROC · NCAN · DEEP-LEARNING TRACK",{x:0.8,y:1.6,w:10,h:0.4,fontFace:SANS,fontSize:14,bold:true,color:TEAL,charSpacing:3,margin:0});
 s.addText("Four animals in.\nWhat's real, and what isn't.",{x:0.8,y:2.15,w:11.4,h:2.0,fontFace:SERIF,fontSize:44,bold:true,color:WHITE,lineSpacingMultiple:0.98,margin:0});
 s.addText("Behaviour is solid. The cortical drift did not survive its own control.",{x:0.82,y:4.3,w:11,h:0.5,fontFace:SANS,fontSize:18,color:"CBD5E1",margin:0});
 s.addText([{text:"Suchith Rao",options:{bold:true,color:WHITE}},{text:"    •    for Dr. Carp    •    July 2026",options:{color:FAINT}}],{x:0.82,y:6.5,w:11,h:0.4,fontFace:SANS,fontSize:15,margin:0});
 s.addNotes("Since last time we went from one animal to four, and we ran the null control you suggested. Headline: the behaviour is solid, but the cortical drift did not survive the null control. I'll show you exactly what happened and what I think it means.");})();

// 2 WHERE WE WERE / WHAT'S NEW
(()=>{const s=p.addSlide(); bg(s,WHITE); kicker(s,"Since last meeting"); title(s,"What changed");
 const items=[["4 animals processed","9, 10, 11 down-conditioned; 12 up. Directions read straight from the experimenters' logs.",VIOLET],
  ["Per-day analysis","Timestamps now in the data, so drift is measured per day / 5-day block, not per phase.",TEAL],
  ["The null control","Your sham test: split baseline-only data as a fake experiment and see if it 'drifts'.",AMBER]];
 let y=2.0;
 items.forEach((it,i)=>{ card(s,0.7,y,11.9,1.45);
  numCircle(s,1.0,y+0.47,i+1,it[2]);
  s.addText(it[0],{x:1.7,y:y+0.3,w:3.6,h:0.5,valign:"middle",fontFace:SANS,fontSize:17,bold:true,color:INK,margin:0});
  s.addText(it[1],{x:5.4,y:y+0.25,w:6.9,h:0.95,valign:"middle",fontFace:SANS,fontSize:14,color:MUTED,lineSpacingMultiple:1.04,margin:0});
  y+=1.62;});
 s.addText("~1.6 million trials decoded across the four animals.",{x:0.72,y:6.85,w:11,h:0.4,fontFace:SANS,fontSize:13,italic:true,color:VIOLET,margin:0});
 s.addNotes("Three things changed. We went to four animals and confirmed their conditioning directions from the logs. We got timestamps in, so we can do drift per day instead of per phase. And we ran your null control, which turned out to be the most important thing we did.");})();

// 3 CHEAT SHEET
(()=>{const s=p.addSlide(); bg(s,WHITE); kicker(s,"Plain English"); title(s,"Three terms for the next few slides");
 const c=[["H / M ratio",VIOLET,"The reflex size divided by the direct muscle response. We never use raw reflex size, because it depends on how hard you stimulate."],
  ["Drift",TEAL,"How far the average brain state has moved from where it started at baseline. Bigger number means the representation changed more."],
  ["The null control",AMBER,"Take baseline-only data, pretend half of it was 'conditioning', and run the same analysis. There was no real conditioning, so it should show ~zero drift."]];
 let y=2.0;
 c.forEach(x=>{ card(s,0.7,y,11.9,1.5,x[0]==="The null control"?"FEF3E2":WHITE);
  s.addShape(p.shapes.OVAL,{x:1.05,y:y+0.62,w:0.24,h:0.24,fill:{color:x[1]},line:{type:"none"}});
  s.addText(x[0],{x:1.5,y:y+0.32,w:3.3,h:0.5,valign:"middle",fontFace:SANS,fontSize:18,bold:true,color:INK,margin:0});
  s.addText(x[2],{x:4.9,y:y+0.25,w:7.4,h:1.0,valign:"middle",fontFace:SANS,fontSize:14,color:MUTED,lineSpacingMultiple:1.04,margin:0});
  y+=1.67;});
 s.addNotes("Quick vocabulary. H over M is the reflex normalised by stimulus strength, which is the only valid way to measure it. Drift is how far the cortical representation moved. And the null control is your sham test, which is the centrepiece today.");})();

// 4 RESULT 1 — BEHAVIOUR WORKS
(()=>{const s=p.addSlide(); bg(s,WHITE); kicker(s,"Result 1 · the behaviour","0D9488"); title(s,"Down-conditioning worked");
 const [w,h]=fit(2.83,7.9,3.3); img(s,"animal11/confound/learning_curve.png",0.65,2.05,w,h);
 card(s,8.8,2.15,3.8,4.0,"F5F3FF");
 s.addText("Animal 11",{x:9.05,y:2.4,w:3.3,h:0.35,fontFace:SANS,fontSize:15,bold:true,color:VIOLET,margin:0});
 s.addText("H/M sits flat around 0.87 through baseline, then falls steadily to about 0.60 once conditioning starts. Animal 9 shows the same pattern.",
  {x:9.05,y:2.85,w:3.35,h:1.6,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("This is the textbook curve, and it's the most solid thing we have.",
  {x:9.05,y:4.6,w:3.35,h:1.2,fontFace:SANS,fontSize:13.5,italic:true,bold:true,color:VIOLET,lineSpacingMultiple:1.05,margin:0});
 s.addNotes("Start with what works. Animal 11: H over M is flat through baseline then drops steadily after conditioning starts, down to about 0.6. Animal 9 does the same thing. This is textbook down-conditioning and it is the most solid result we have.");})();

// 5 THE NULL CONTROL — WHAT IT IS
(()=>{const s=p.addSlide(); bg(s,WHITE); kicker(s,"Result 2 · your sham test",AMBER); title(s,"The null control, and why it matters");
 card(s,0.7,2.0,5.85,4.3,CARD);
 s.addText("The idea",{x:1.0,y:2.3,w:5,h:0.4,fontFace:SANS,fontSize:16,bold:true,color:INK,margin:0});
 s.addText("Take ONLY the baseline recordings, before any conditioning happened. Pretend the first part is 'baseline' and the rest is 'conditioning'. Run the identical drift analysis.",
  {x:1.0,y:2.8,w:5.3,h:1.8,fontFace:SANS,fontSize:15,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("Nothing happened in that data, so an honest method must report ~zero drift.",
  {x:1.0,y:4.8,w:5.3,h:1.2,fontFace:SANS,fontSize:14,italic:true,color:MUTED,lineSpacingMultiple:1.05,margin:0});
 card(s,6.75,2.0,5.85,4.3,"FEF3E2");
 s.addText("What we found",{x:7.05,y:2.3,w:5,h:0.4,fontFace:SANS,fontSize:16,bold:true,color:AMBER,margin:0});
 s.addText("The sham 'drifts' just as much as real conditioning in 3 of the 4 animals.",
  {x:7.05,y:2.85,w:5.3,h:1.2,fontFace:SANS,fontSize:16,bold:true,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("So most of what we were calling a cortical effect is slow drift in the recording itself over weeks, not learning.",
  {x:7.05,y:4.15,w:5.3,h:1.5,fontFace:SANS,fontSize:14.5,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addNotes("This is the test you suggested and it was the right call. Take baseline-only data, pretend part of it was conditioning, run the same analysis. Nothing happened in that data so it should show zero drift. It doesn't. In three of four animals the sham drifts as much as the real thing, which means most of what we were calling a cortical effect is recording drift over weeks.");})();

// 6 THE FIGURE
(()=>{const s=p.addSlide(); bg(s,WHITE); kicker(s,"The null control, in one picture",AMBER); title(s,"Animal 9: the sham drifts as much as the real thing");
 const [w,h]=fit(1.80,7.3,4.2); img(s,"drift_time/null_control.png",0.65,2.0,w,h);
 card(s,8.5,2.15,4.1,4.0,"FEF3E2");
 s.addText("Red = fake experiment",{x:8.75,y:2.4,w:3.6,h:0.35,fontFace:SANS,fontSize:14.5,bold:true,color:RED,margin:0});
 s.addText("Baseline-only data, no conditioning at all. It climbs as high as the purple real-conditioning line.",
  {x:8.75,y:2.85,w:3.65,h:1.3,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("Also note the purple line rises during baseline and falls during the strongest learning. It runs opposite to the behaviour.",
  {x:8.75,y:4.3,w:3.65,h:1.7,fontFace:SANS,fontSize:13.5,italic:true,color:AMBER,lineSpacingMultiple:1.05,margin:0});
 s.addNotes("Here it is. Red is the fake experiment on baseline-only data. It climbs just as high as the purple real-conditioning line. And look at the purple line itself, it rises during baseline and falls during the period when the animal was actually learning most. It runs opposite to the behaviour, which is the giveaway that it is not tracking conditioning.");})();

// 7 SCORECARD (4 animals)
(()=>{const s=p.addSlide(); bg(s,WHITE); kicker(s,"All four animals"); title(s,"The scorecard");
 const rows=[["9","down","Worked (H/M falls)",GREEN,"Fails",RED],
   ["10","down","Complicated (40-day gap)",AMBER,"PASSES",GREEN],
   ["11","down","Worked (H/M falls)",GREEN,"Fails",RED],
   ["12","up","Weak responder",AMBER,"Fails",RED]];
 // header
 s.addText("Animal",{x:1.0,y:2.05,w:1.6,h:0.4,fontFace:SANS,fontSize:13,bold:true,color:MUTED,margin:0});
 s.addText("Direction",{x:2.7,y:2.05,w:1.8,h:0.4,fontFace:SANS,fontSize:13,bold:true,color:MUTED,margin:0});
 s.addText("Behaviour",{x:4.7,y:2.05,w:4.2,h:0.4,fontFace:SANS,fontSize:13,bold:true,color:MUTED,margin:0});
 s.addText("Null control",{x:9.5,y:2.05,w:2.8,h:0.4,fontFace:SANS,fontSize:13,bold:true,color:MUTED,margin:0});
 let y=2.55;
 rows.forEach(r=>{ card(s,0.7,y,11.9,0.95);
  s.addText("A"+r[0],{x:1.0,y:y+0.2,w:1.6,h:0.55,valign:"middle",fontFace:SERIF,fontSize:20,bold:true,color:INK,margin:0});
  s.addText(r[1],{x:2.7,y:y+0.2,w:1.8,h:0.55,valign:"middle",fontFace:SANS,fontSize:15,color:r[1]==="up"?RED:VIOLET,bold:true,margin:0});
  s.addText(r[2],{x:4.7,y:y+0.2,w:4.6,h:0.55,valign:"middle",fontFace:SANS,fontSize:14.5,color:r[3],margin:0});
  s.addText(r[4],{x:9.5,y:y+0.2,w:2.8,h:0.55,valign:"middle",fontFace:SANS,fontSize:15,bold:true,color:r[5],margin:0});
  y+=1.08;});
 s.addText("Down-conditioning is reproducible. The cortical drift is not — only one animal survives its own control.",
  {x:0.72,y:6.95,w:11.9,h:0.4,fontFace:SANS,fontSize:13.5,italic:true,color:INK,margin:0});
 s.addNotes("All four side by side. Behaviour is reproducible: down-conditioning works in 9 and 11, animal 10 is complicated by a forty-day recording gap, and animal 12's up-conditioning is a weak responder. The cortical drift is the opposite story, only animal 10 survives the null control. That inconsistency is the finding.");})();

// 8 ANIMAL 10 — THE EXCEPTION
(()=>{const s=p.addSlide(); bg(s,WHITE); kicker(s,"The one exception",GREEN); title(s,"Animal 10 passed the null control");
 const [w,h]=fit(1.80,7.3,4.2); img(s,"animal10/drift/null_control.png",0.65,2.0,w,h);
 card(s,8.5,2.15,4.1,4.0,"F0FDF4");
 s.addText("Real 30.6  vs  sham 6.7",{x:8.75,y:2.4,w:3.6,h:0.45,fontFace:SERIF,fontSize:20,bold:true,color:GREEN,margin:0});
 s.addText("Here the real conditioning drift is about 4.6x the sham. This is the one animal where the cortical change is not explained by recording drift.",
  {x:8.75,y:3.0,w:3.65,h:1.7,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("Worth chasing. But one animal out of four is a lead, not a result.",
  {x:8.75,y:4.85,w:3.65,h:1.2,fontFace:SANS,fontSize:13.5,italic:true,bold:true,color:GREEN,lineSpacingMultiple:1.05,margin:0});
 s.addNotes("One animal bucks the trend. In animal 10 the real drift is about four and a half times the sham, so the cortical change there is not explained by recording drift. That's worth chasing. But one out of four is a lead, not a result, and I don't want to build a story on it yet.");})();

// 9 WHAT IT MEANS
(()=>{const s=p.addSlide(); bg(s,WHITE); kicker(s,"Interpretation"); title(s,"Why one animal can't settle this");
 card(s,0.7,2.0,11.9,1.9,"F5F3FF");
 s.addText("In a single animal, conditioning and recording drift are both slow changes over weeks. They are mathematically tangled, so no single-animal analysis can separate them.",
  {x:1.05,y:2.25,w:11.2,h:1.4,valign:"middle",fontFace:SANS,fontSize:17,color:INK,lineSpacingMultiple:1.06,margin:0});
 card(s,0.7,4.1,5.85,2.6);
 s.addText("What is solid",{x:1.0,y:4.35,w:5,h:0.4,fontFace:SANS,fontSize:15,bold:true,color:GREEN,margin:0});
 s.addText([{text:"Decoding + pipeline across 4 animals",options:{bullet:true,breakLine:true}},
   {text:"Down-conditioning quantified with H/M",options:{bullet:true,breakLine:true}},
   {text:"The control methodology itself",options:{bullet:true}}],
  {x:1.0,y:4.8,w:5.3,h:1.7,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.05,paraSpaceAfter:6,margin:0});
 card(s,6.75,4.1,5.85,2.6,"FEF3E2");
 s.addText("What is not",{x:7.05,y:4.35,w:5,h:0.4,fontFace:SANS,fontSize:15,bold:true,color:AMBER,margin:0});
 s.addText([{text:"A conditioning-specific cortical drift",options:{bullet:true,breakLine:true}},
   {text:"Any up-vs-down cortical contrast",options:{bullet:true,breakLine:true}},
   {text:"Pooling animals (results disagree)",options:{bullet:true}}],
  {x:7.05,y:4.8,w:5.3,h:1.7,fontFace:SANS,fontSize:14,color:INK,lineSpacingMultiple:1.05,paraSpaceAfter:6,margin:0});
 s.addNotes("Here's the interpretation. In one animal, conditioning and recording drift are both slow changes over weeks, so they're mathematically tangled and no single-animal analysis can pull them apart. What's solid is the pipeline, the behaviour, and the control methodology. What's not solid is a conditioning-specific cortical effect, the up versus down contrast, or pooling animals.");})();

// 10 WHAT WOULD MAKE IT REAL
(()=>{const s=p.addSlide(); bg(s,WHITE); kicker(s,"The bar","6D28D9"); title(s,"What would make a cortical claim believable");
 s.addText("A cortical signature has to survive all five of these. Right now we clearly pass one.",
  {x:0.7,y:1.75,w:11.9,h:0.5,fontFace:SANS,fontSize:16,color:INK,margin:0});
 const ctrl=[["Null control","sham on baseline shows ~zero",AMBER,"only 1 of 4"],
  ["M-wave control","not driven by stimulus size",GREEN,"cleared"],
  ["Pre-stimulus control","not just arousal / background",MUTED,"not built yet"],
  ["Direction contrast","up and down differ or flip",AMBER,"need a strong up animal"],
  ["Tracks behaviour","follows the H/M learning curve",AMBER,"not yet"]];
 let y=2.45;
 ctrl.forEach((c,i)=>{ card(s,0.7,y,11.9,0.85);
  numCircle(s,0.98,y+0.17,i+1,c[2]);
  s.addText(c[0],{x:1.68,y:y+0.13,w:3.0,h:0.6,valign:"middle",fontFace:SANS,fontSize:15,bold:true,color:INK,margin:0});
  s.addText(c[1],{x:4.8,y:y+0.13,w:4.4,h:0.6,valign:"middle",fontFace:SANS,fontSize:13.5,color:MUTED,margin:0});
  s.addText(c[3],{x:9.4,y:y+0.13,w:2.9,h:0.6,valign:"middle",fontFace:SANS,fontSize:13.5,bold:true,color:c[2],margin:0});
  y+=0.95;});
 s.addNotes("This is the bar I want to hold us to. Five controls. We clear the M-wave one, and the null control only in one animal. Pre-stimulus excitability isn't built yet, we need a strong up-conditioned animal for the direction contrast, and nothing yet tracks the behavioural curve. If we clear all five, that's a real result.");})();

// 11 PLAN
(()=>{const s=p.addSlide(); bg(s,WHITE); kicker(s,"Plan","0D9488"); title(s,"Next few weeks");
 const road=[["Per-animal clean-up","Handle recording gaps, set M/H windows from each animal's own average."],
  ["Pooled encoder","Retrain the representation on all animals, not just animal 9."],
  ["Pre-stimulus control","Add background excitability alongside the M-wave."],
  ["Chase animal 10","Is its surviving drift real, or luck?"],
  ["A strong up animal","The single highest-value thing to add."]];
 let y=2.15;
 road.forEach((r,i)=>{ card(s,0.7,y,11.9,0.9);
  numCircle(s,0.98,y+0.2,i+1,i<3?VIOLET:TEAL);
  s.addText(r[0],{x:1.68,y:y+0.15,w:3.9,h:0.6,valign:"middle",fontFace:SANS,fontSize:15,bold:true,color:INK,margin:0});
  s.addText(r[1],{x:5.7,y:y+0.15,w:6.6,h:0.6,valign:"middle",fontFace:SANS,fontSize:13.5,color:MUTED,margin:0});
  y+=1.0;});
 s.addText("We're deliberately not rushing a draft. Better to clear the bar than publish a confounded effect.",
  {x:0.72,y:7.0,w:11.9,h:0.4,fontFace:SANS,fontSize:13.5,italic:true,color:VIOLET,margin:0});
 s.addNotes("The plan. Clean up per animal, retrain the encoder on everything, add the pre-stimulus control, chase animal 10, and get a strongly conditioned up animal. We're deliberately not rushing a draft, because it's better to clear the bar than to publish a confounded effect.");})();

// 12 DISCUSSION
(()=>{const s=p.addSlide(); bg(s,DARK);
 s.addText("WHERE I NEED YOUR READ",{x:0.8,y:0.6,w:11,h:0.4,fontFace:SANS,fontSize:14,bold:true,color:TEAL,charSpacing:3,margin:0});
 s.addText("Four questions",{x:0.8,y:1.05,w:11.5,h:0.7,fontFace:SERIF,fontSize:30,bold:true,color:WHITE,margin:0});
 const qs=[["Is the null-control read right?","Baseline sham drifts as much as conditioning. Does that convince you the drift is recording, not learning?"],
  ["Animal 10","It passed. Worth chasing, or likely a fluke given 3 of 4 failed?"],
  ["A strong up animal","Which animal in the drive is most likely a solid up-conditioning responder?"],
  ["The bar","Are the five controls the right bar, or would you add or drop one?"]];
 let x=0.8,y=2.1;
 qs.forEach((q,i)=>{ const cx=x+(i%2)*6.05, cy=y+Math.floor(i/2)*2.35;
  s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:cx,y:cy,w:5.75,h:2.05,rectRadius:0.09,fill:{color:"1E293B"},line:{color:"334155",width:1}});
  numCircle(s,cx+0.3,cy+0.3,i+1,i<2?VIOLET:TEAL);
  s.addText(q[0],{x:cx+0.95,y:cy+0.32,w:4.6,h:0.5,fontFace:SANS,fontSize:15.5,bold:true,color:WHITE,margin:0});
  s.addText(q[1],{x:cx+0.32,y:cy+0.92,w:5.15,h:1.0,fontFace:SANS,fontSize:12.5,color:"CBD5E1",lineSpacingMultiple:1.05,margin:0});});
 s.addText("Everything (code, figures, per-animal results) is in the repo.",{x:0.8,y:6.95,w:11.7,h:0.4,fontFace:SANS,fontSize:13,italic:true,color:FAINT,margin:0});
 s.addNotes("Four things I want your read on. Whether you buy the null-control interpretation. Whether animal 10 is worth chasing. Which drive animal is the best bet for a strong up-conditioning responder. And whether the five controls are the right bar.");})();

p.writeFile({fileName:"slides/HROC_Findings_4Animals.pptx"}).then(f=>console.log("WROTE",f));
