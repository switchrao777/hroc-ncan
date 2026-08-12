// HROC — weekly update for Dr Carp (what changed since 12 Aug)
// Run: NODE_PATH=$(npm root -g) node slides/build_weekly_deck.js
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "Suchith Rao";
p.title = "HROC — Weekly Update";

const DARK="0F172A", INK="1E293B", MUTED="64748B", FAINT="94A3B8";
const VIOLET="6D28D9", TEAL="0D9488", AMBER="D97706", GREEN="16A34A", RED="DC2626", BLUE="2563EB";
const CARDLINE="E2E8F0", WHITE="FFFFFF", CARD="F1F5F9";
const SERIF="Cambria", SANS="Calibri";
const IMG = f => "outputs/" + f;
const sh = () => ({type:"outer",color:"0F172A",blur:9,offset:3,angle:90,opacity:0.14});
const bg=(s,c)=>{s.background={color:c};};
const title=(s,t)=>s.addText(t,{x:0.7,y:0.5,w:12.1,h:0.78,fontFace:SERIF,fontSize:28,bold:true,color:INK,margin:0});
const kick=(s,t,c)=>s.addText(t.toUpperCase(),{x:0.72,y:0.42,w:12,h:0.3,fontFace:SANS,fontSize:12,bold:true,color:c||TEAL,charSpacing:3,margin:0});
const card=(s,x,y,w,h,f)=>s.addShape(p.shapes.ROUNDED_RECTANGLE,{x,y,w,h,rectRadius:0.09,fill:{color:f||WHITE},line:{color:CARDLINE,width:1},shadow:sh()});
function num(s,x,y,n,c){const d=0.48;
  s.addShape(p.shapes.OVAL,{x,y,w:d,h:d,fill:{color:c},line:{type:"none"}});
  s.addText(String(n),{x,y,w:d,h:d,align:"center",valign:"middle",fontFace:SANS,fontSize:16,bold:true,color:WHITE,margin:0});}
const img=(s,f,x,y,w,h)=>s.addImage({path:IMG(f),x,y,w,h,sizing:{type:"contain",w,h}});
const fit=(r,mw,mh)=>{let w=mw,h=w/r; if(h>mh){h=mh;w=h*r;} return [w,h];};

// 1 TITLE
(()=>{const s=p.addSlide(); bg(s,DARK);
 s.addShape(p.shapes.OVAL,{x:11.1,y:1.1,w:1.4,h:1.4,fill:{color:VIOLET,transparency:55},line:{type:"none"}});
 s.addShape(p.shapes.OVAL,{x:11.8,y:1.9,w:0.95,h:0.95,fill:{color:TEAL,transparency:45},line:{type:"none"}});
 s.addText("WEEKLY UPDATE",{x:0.8,y:1.7,w:10,h:0.4,fontFace:SANS,fontSize:14,bold:true,color:TEAL,charSpacing:3,margin:0});
 s.addText("Everything you asked for\nlast week, answered.",{x:0.8,y:2.2,w:11.4,h:1.9,fontFace:SERIF,fontSize:40,bold:true,color:WHITE,lineSpacingMultiple:0.98,margin:0});
 s.addText("Including one number that moved against us.",{x:0.82,y:4.3,w:11,h:0.5,fontFace:SANS,fontSize:17,color:"CBD5E1",margin:0});
 s.addText("Suchith Rao & Tarun Senthil    •    for Dr. Carp",{x:0.82,y:6.5,w:11,h:0.4,fontFace:SANS,fontSize:14,color:FAINT,margin:0});
 s.addNotes("Short update this week. You gave us four things to check, all four are done, and I want to lead with the one where the number moved against us.");})();

// 2 THE FOUR ASKS
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Since last week"); title(s,"Four things you asked for");
 const items=[["Partition the variance","How much does each factor explain?","Done — table next slide",GREEN],
  ["Re-check the 0.35","Was stimulus removed properly?","Done — the number dropped",AMBER],
  ["Test for crosstalk","Correlate cortex against muscle power","Done — no contamination",GREEN],
  ["Does it scale with learning?","Failed animals as internal control","Done — r = +0.64",GREEN]];
 let y=2.0;
 items.forEach((it,i)=>{card(s,0.7,y,11.9,1.15);
  num(s,0.98,y+0.33,i+1,it[3]);
  s.addText(it[0],{x:1.66,y:y+0.14,w:3.3,h:0.85,valign:"middle",fontFace:SANS,fontSize:15,bold:true,color:INK,margin:0});
  s.addText(it[1],{x:5.1,y:y+0.14,w:4.3,h:0.85,valign:"middle",fontFace:SANS,fontSize:12.5,color:MUTED,lineSpacingMultiple:1.02,margin:0});
  s.addText(it[2],{x:9.55,y:y+0.14,w:2.9,h:0.85,valign:"middle",fontFace:SANS,fontSize:12.5,bold:true,color:it[3],margin:0});
  y+=1.27;});
 s.addNotes("Four things. Partition the variance — done, table on the next slide. Re-check the 0.35 to see whether the stimulus was removed properly — done, and the number dropped, which I'll explain. Test for crosstalk using your correlation method — done, no contamination. And whether the effect scales with how much each animal learned — done, and that one is the most promising.");})();

// 3 VARIANCE PARTITION
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Ask 1 · the partition"); title(s,"What explains reflex size");
 const rows=[["Stimulus (M-wave)","47%",VIOLET,"Dominant — how much stimulus reached the muscle"],
  ["Background excitability","1%",TEAL,"Small alone, but a necessary control"],
  ["Cortex, alone","21%",BLUE,"Mostly overlaps stimulus — stimulus drives both"],
  ["Cortex, unique","2%",GREEN,"What cortex adds once the others are known"],
  ["Unexplained","51%",MUTED,"Trial-to-trial variability we can't account for"]];
 let y=1.95;
 rows.forEach(r=>{card(s,0.7,y,11.9,0.95,r[0]==="Cortex, unique"?"F0FDF4":WHITE);
  s.addText(r[0],{x:1.05,y:y+0.15,w:4.2,h:0.65,valign:"middle",fontFace:SANS,fontSize:14.5,bold:true,color:INK,margin:0});
  s.addText(r[1],{x:5.4,y:y+0.15,w:1.5,h:0.65,valign:"middle",align:"right",fontFace:SERIF,fontSize:23,bold:true,color:r[2],margin:0});
  s.addText(r[3],{x:7.2,y:y+0.15,w:5.1,h:0.65,valign:"middle",fontFace:SANS,fontSize:12,color:MUTED,lineSpacingMultiple:1.02,margin:0});
  y+=1.05;});
 s.addText("Your read was right: the three don't add up, because cortex and stimulus share variance.",
   {x:0.72,y:7.15,w:11.9,h:0.35,fontFace:SANS,fontSize:12.5,italic:true,color:VIOLET,margin:0});
 s.addNotes("Here's the partition you asked for. Stimulus dominates at 47 percent. Background is 1. Cortex alone is 21, but most of that overlaps with stimulus because the stimulus drives both the cortical evoked response and the reflex. Cortex's unique contribution, once the other two are in the model, is 2 percent. And about half the variance is still unexplained. Your intuition in the meeting was right — they don't add up, because of that shared variance.");})();

// 4 THE CORRECTION
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Ask 2 · the correction",AMBER); title(s,"The 0.35 was inflated. The real number is 0.04.");
 card(s,0.7,1.95,5.85,2.5,CARD);
 s.addText("What was wrong",{x:1.0,y:2.2,w:5,h:0.35,fontFace:SANS,fontSize:15,bold:true,color:AMBER,margin:0});
 s.addText("I removed stimulus and background across ALL trials at once, then measured cortex within each 5-day block. If the stimulus–reflex relationship shifts between blocks, that leaves stimulus variance behind — and cortex tracks stimulus.",
   {x:1.0,y:2.65,w:5.3,h:1.6,fontFace:SANS,fontSize:13.5,color:INK,lineSpacingMultiple:1.05,margin:0});
 card(s,6.75,1.95,5.85,2.5,"F0FDF4");
 s.addText("The fix",{x:7.05,y:2.2,w:5,h:0.35,fontFace:SANS,fontSize:15,bold:true,color:GREEN,margin:0});
 s.addText("Remove them INSIDE each block, then decode. Nothing can leak across blocks. This is the conservative estimate and the one we'll quote.",
   {x:7.05,y:2.65,w:5.3,h:1.6,fontFace:SANS,fontSize:13.5,color:INK,lineSpacingMultiple:1.05,margin:0});
 const nums=[["0.35","best block, old method",MUTED],["0.09","mean, old method",MUTED],["0.04","mean, corrected",GREEN],["−0.01","shuffle null",RED]];
 let x=0.7;
 nums.forEach(([n,l,c])=>{card(s,x,4.75,2.87,1.9);
  s.addText(n,{x:x,y:4.95,w:2.87,h:0.9,align:"center",fontFace:SERIF,fontSize:34,bold:true,color:c,margin:0});
  s.addText(l,{x:x+0.15,y:5.85,w:2.57,h:0.6,align:"center",fontFace:SANS,fontSize:12,color:MUTED,margin:0}); x+=3.05;});
 s.addText("Still above the null in every animal — the finding holds, it's just smaller than I said.",
   {x:0.72,y:6.9,w:11.9,h:0.4,fontFace:SANS,fontSize:13,italic:true,bold:true,color:INK,margin:0});
 s.addNotes("This is the one I want to lead with. Last week I quoted 0.35. That was the best block, and on top of that I'd removed stimulus and background globally rather than block by block. If the stimulus-reflex relationship shifts between blocks, global removal leaves stimulus variance behind, and cortex tracks stimulus — so the number was inflated. Doing it inside each block gives 0.04. That's the number we'll quote from now on. It's still above the shuffle null in every animal, so the finding holds, it's just a smaller claim than I made last week.");})();

// 5 CROSSTALK
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Ask 3 · crosstalk",GREEN); title(s,"No muscle contamination");
 const [w,h]=fit(2.6,7.6,3.8); img(s,"verify/verification.png",0.5,2.0,w,h);
 card(s,8.35,2.1,4.25,4.15,"F0FDF4");
 s.addText("Your method",{x:8.6,y:2.35,w:3.7,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:TEAL,margin:0});
 s.addText("Correlate cortical power against muscle power, band by band. Muscle artefact lives at high frequency, so contamination would show there.",
   {x:8.6,y:2.78,w:3.75,h:1.35,fontFace:SANS,fontSize:13,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("Above 100 Hz:\nr = +0.06",{x:8.6,y:4.2,w:3.75,h:0.85,fontFace:SERIF,fontSize:20,bold:true,color:GREEN,lineSpacingMultiple:1.1,margin:0});
 s.addText("Essentially zero. Low bands slightly negative. Cortex marginally leads muscle, which is the acceptable direction.",
   {x:8.6,y:5.15,w:3.75,h:1.0,fontFace:SANS,fontSize:12.5,italic:true,color:MUTED,lineSpacingMultiple:1.05,margin:0});
 s.addNotes("Crosstalk, using exactly the method you suggested — correlate cortical against muscle power and see how much coordination there is. Above 100 hertz, where muscle artefact lives, the correlation is plus 0.06, essentially zero. The low bands are slightly negative. And the lead-lag check has cortex marginally leading muscle, which you said would be the acceptable direction. So we don't think the ECoG is reproducing the EMG.");})();

// 6 SCALING
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Ask 4 · the internal control",VIOLET); title(s,"The effect tracks how much they learned");
 const [w,h]=fit(2.6,7.6,3.8); img(s,"scaling/scaling.png",0.5,2.0,w,h);
 card(s,8.35,2.1,4.25,4.15,"F5F3FF");
 s.addText("Your idea",{x:8.6,y:2.35,w:3.7,h:0.35,fontFace:SANS,fontSize:14,bold:true,color:VIOLET,margin:0});
 s.addText("Animals that failed to condition shouldn't show the cortical effect. Two of ours failed — they're the built-in negative control.",
   {x:8.6,y:2.78,w:3.75,h:1.35,fontFace:SANS,fontSize:13,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("r = +0.64",{x:8.6,y:4.2,w:3.75,h:0.6,fontFace:SERIF,fontSize:26,bold:true,color:VIOLET,margin:0});
 s.addText("between learning and the change in coupling. The two successes gained coupling; the two failures didn't.",
   {x:8.6,y:4.85,w:3.75,h:1.0,fontFace:SANS,fontSize:12.5,color:INK,lineSpacingMultiple:1.05,margin:0});
 s.addText("n = 5, so not significant yet.",{x:8.6,y:5.9,w:3.75,h:0.35,fontFace:SANS,fontSize:12,italic:true,bold:true,color:AMBER,margin:0});
 s.addNotes("And this is your internal-control idea, which I think is the most promising thing we have. Animals differ in how much they learned and two of ours failed outright — those become the negative control. The correlation between learning and the change in coupling is plus 0.64. The two animals that succeeded gained coupling; the two that failed didn't. With five animals it isn't significant, but it's the right direction, and it's exactly what more animals would power.");})();

// 7 THE UP-ANIMAL CAP
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"New finding · a constraint",AMBER); title(s,"We've run out of up-conditioned animals");
 s.addText("Using the reward criterion as a success readout across every animal's log — the same trick that found animals 3 and 4:",
   {x:0.7,y:1.8,w:11.9,h:0.6,fontFace:SANS,fontSize:14.5,color:INK,margin:0});
 const rows=[["A3","up","RW  90 → 190","bar raised — learned",GREEN],
  ["A4","up","RW 150 → 220","bar raised — learned",GREEN],
  ["A1","up","RW 110 → 59","bar lowered — struggled",RED],
  ["A6","up","RW 150 → 80","bar lowered — struggled",RED],
  ["A12","up","—","ECoG electrode dead (2.8 µV)",RED]];
 let y=2.6;
 rows.forEach(r=>{card(s,0.7,y,11.9,0.8);
  s.addText(r[0],{x:1.05,y:y+0.1,w:1.0,h:0.6,valign:"middle",fontFace:SERIF,fontSize:17,bold:true,color:INK,margin:0});
  s.addText(r[1],{x:2.1,y:y+0.1,w:1.0,h:0.6,valign:"middle",fontFace:SANS,fontSize:13,color:MUTED,margin:0});
  s.addText(r[2],{x:3.3,y:y+0.1,w:3.0,h:0.6,valign:"middle",fontFace:SANS,fontSize:13.5,color:INK,margin:0});
  s.addText(r[3],{x:6.5,y:y+0.1,w:5.8,h:0.6,valign:"middle",fontFace:SANS,fontSize:13,bold:true,color:r[4],margin:0});
  y+=0.9;});
 card(s,0.7,7.15,11.9,0.0);
 s.addText("So the up group is capped at two. The down group can still grow — 7, 8, 13, 14, 15 are ready to download.",
   {x:0.72,y:7.1,w:11.9,h:0.4,fontFace:SANS,fontSize:13,italic:true,bold:true,color:VIOLET,margin:0});
 s.addNotes("One new finding, and it's a constraint. I went back through every animal's log using the reward criterion as a success readout. For up-conditioning, raising the bar means the rat is beating it. Animals 3 and 4 had theirs raised, so they learned. Animals 1 and 6 had theirs lowered, so they struggled. And animal 12's electrode was dead. So the up group is capped at two, permanently — there isn't another good up-conditioned animal in this dataset. The down group can still grow, and 7, 8, 13, 14 and 15 are ready to download.");})();


// 8 THE PACKAGE (website + 3 components)
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"New this week · deliverables",VIOLET);
 title(s,"Everything now lives in one place");
 s.addText("We put the project behind a single page so the code, the write-up and the slides stay in sync and are easy to hand to anyone.",
   {x:0.7,y:1.78,w:11.9,h:0.55,fontFace:SANS,fontSize:14.5,color:INK,margin:0});
 const parts=[["Repository","The pipeline",VIOLET,
    "Decoding, the pooled autoencoder, every control, per-animal results. One command per animal, reproducible end to end.",
    "github.com/switchrao777/hroc-ncan"],
   ["Report","Six-page write-up",TEAL,
    "Background, methods, results, limitations, references — with the four figures and the real numbers. Formatted as a handout.",
    "docs/HROC_Report.pdf"],
   ["Slides","The decks",AMBER,
    "This update, the talk for your group, and speaker notes for each.",
    "slides/"]];
 let x=0.7;
 parts.forEach(([k,t,c,d,u])=>{card(s,x,2.5,3.87,3.5);
  s.addText(k.toUpperCase(),{x:x+0.3,y:2.75,w:3.3,h:0.3,fontFace:SANS,fontSize:11,bold:true,color:c,charSpacing:2,margin:0});
  s.addText(t,{x:x+0.3,y:3.1,w:3.3,h:0.5,fontFace:SERIF,fontSize:19,bold:true,color:INK,margin:0});
  s.addText(d,{x:x+0.3,y:3.7,w:3.35,h:1.6,fontFace:SANS,fontSize:12.5,color:MUTED,lineSpacingMultiple:1.06,margin:0});
  s.addText(u,{x:x+0.3,y:5.45,w:3.35,h:0.4,fontFace:SANS,fontSize:10.5,italic:true,color:c,margin:0});
  x+=4.08;});
 card(s,0.7,6.25,11.9,0.85,"F5F3FF");
 s.addText([{text:"Two blanks I left for you:  ",options:{bold:true,color:VIOLET}},
   {text:"Theresa's surname, and what Tarun and I should be listed as. I didn't want to guess on the write-up.",options:{color:INK}}],
   {x:1.05,y:6.4,w:11.2,h:0.55,valign:"middle",fontFace:SANS,fontSize:13,margin:0});
 s.addNotes("One more thing from this week. We put everything behind a single page so it stays in sync and is easy to hand to anyone — the repository with the whole pipeline, a six-page write-up formatted as a handout with the real numbers and figures, and the slide decks. Two blanks I deliberately left: Theresa's surname, and what Tarun and I should be listed as on the write-up. I didn't want to guess at either.");})();

// 9 PLAN
(()=>{const s=p.addSlide(); bg(s,WHITE); kick(s,"Next","0D9488"); title(s,"Between now and the 21st");
 const road=[["Download and process the remaining animals","7, 8, 13, 14, 15 (down) plus 1 and 6 (failed up — negative controls). Takes n from 5 to about 12.",VIOLET],
  ["Re-run everything at the larger n","The scaling correlation is the analysis this powers. Fully automated — two commands per animal.",VIOLET],
  ["Build the presentation for your group","Pipeline explained with a data-flow figure, at the level you described.",TEAL],
  ["Preview it with you","Before the 21st, so it's on par with what your group expects.",TEAL]];
 let y=2.1;
 road.forEach((r,i)=>{card(s,0.7,y,11.9,1.05);
  num(s,0.98,y+0.28,i+1,r[2]);
  s.addText(r[0],{x:1.66,y:y+0.2,w:4.3,h:0.65,valign:"middle",fontFace:SANS,fontSize:14.5,bold:true,color:INK,lineSpacingMultiple:1.0,margin:0});
  s.addText(r[1],{x:6.1,y:y+0.2,w:6.2,h:0.65,valign:"middle",fontFace:SANS,fontSize:12.5,color:MUTED,lineSpacingMultiple:1.02,margin:0}); y+=1.17;});
 card(s,0.7,6.85,11.9,0.75,"F5F3FF");
 s.addText("Question for you: with the up group capped at two, is the scaling analysis the right thing to build the paper on?",
   {x:1.05,y:6.98,w:11.2,h:0.5,valign:"middle",fontFace:SANS,fontSize:13.5,bold:true,color:VIOLET,margin:0});
 s.addNotes("Plan between now and the 21st. Download and process the remaining animals — the five down ones plus the two failed up animals, which are useful as negative controls. That takes us from five to about twelve. Re-run everything at that larger n, which is what powers the scaling correlation. Build the presentation for your group. And preview it with you beforehand. One question for you: given the up group is capped at two, is the scaling analysis the right thing to build the paper around rather than the direction contrast?");})();

p.writeFile({fileName:"slides/HROC_Weekly_Update.pptx"}).then(f=>console.log("WROTE",f));
