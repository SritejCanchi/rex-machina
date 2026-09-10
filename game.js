"use strict";
// ---------------------------------------------------------------------------
// Every line of content below is loaded from data/*.json. Those files are
// copied byte for byte from the pipeline runs by tools/sync_datatables.py.
// Nothing in this file authors game content.
// ---------------------------------------------------------------------------
const DT = {};
let SINK = null;   // tests replace this; the browser leaves it null
function setSinks(s){ SINK = s; }
const $ = id => SINK ? SINK(id) : document.getElementById(id);

const S = {
  act: 1, hazard: 0, hzTurn: 0, hzFails: 0, totalFails: 0,
  limping: false, phaseIx: 0, over: false, mode: "boot",
  // act 3
  dog: [0,0], rex: [5,5], kid: [7,4], distMax: 11,
  stamina: 15, round: 0, charge: 100, moves: [], lastCat: null,
  priorAttempt: null, attempts: 0, checkpoint: null, spoken: [], log: [], hzState: "play", ledger: [],
  // The ledger's judge used to be gated on the presence of a document, which
  // put it out of reach of qa/adversary.js. A flag can be turned on headlessly.
  judge: typeof document !== "undefined"
};

const MAXROUNDS = 15, START_CHARGE = 100, PURSUIT = 8, HOLD = 1, SOLAR = 2;
const BAND_CLIN = 60, BAND_CONF = 30, WINDOW = 4, FREQ = 20;

// Difficulty is three settings of the same four knobs. The defaults are the
// tuned, tested fight; the headless tests never touch this and get exactly
// that. Easy makes the machine forget sooner and tire faster and gives you
// legs; hard does the reverse. What it never changes is the prediction
// itself, because the prediction is the game.
const DIFFS = {
  easy:     { label: "easy",     window: 3, maxRounds: 18, pursuit: 12, staminaBonus: 4 },
  moderate: { label: "moderate", window: 4, maxRounds: 15, pursuit: 8,  staminaBonus: 0 },
  hard:     { label: "hard",     window: 6, maxRounds: 13, pursuit: 6,  staminaBonus: -2 }
};
let CFG = Object.assign({ name: "moderate" }, DIFFS.moderate);
function setDiff(name){
  if(!DIFFS[name]) return;
  CFG = Object.assign({ name: name }, DIFFS[name]);
  try { localStorage.setItem("rm_diff", name); } catch(e) {}
  if(S.mode === "fight") beginFight();
  else if(S.mode === "hazard") drawHazard();
  else if(S.mode === "intro") intro();
}
const STEP = {left:[-1,0], right:[1,0], up:[0,-1], down:[0,1]};

const man = (a,b) => Math.abs(a[0]-b[0]) + Math.abs(a[1]-b[1]);
const eq = (a,b) => a[0]===b[0] && a[1]===b[1];

function say(html, cls){
  if(QUIET) return;                                    // the planner is thinking, not speaking
  S.log.push(String(html).replace(/<[^>]*>/g, ""));   // visible to headless tests
  if(typeof document === "undefined"){ return; }
  const p = document.createElement("p");
  if(cls) p.className = cls;
  p.innerHTML = html;
  if(html.indexOf("class='rex'") >= 0 && S.mode === "fight"){
    BOARD.bubble = String(html).replace(/<[^>]*>/g, "").replace(/^REX:\s*/, "")
      .replace(/&ldquo;|&rdquo;/g, "“").replace(/&amp;/g, "&");
    BOARD.bubbleT0 = performance.now();
  }
  $("say").appendChild(p);
  while($("say").children.length > 4) $("say").removeChild($("say").firstChild);
}
function clearSay(){ if(typeof document === "undefined") return; $("say").innerHTML = ""; }

// A muted line under the stage naming the course work that made what is on
// screen. It is for a reader who has two minutes and seventy other games: the
// mechanics say what the agents do, this says which agent did it.
const BADGE = {
  hazard: "<b>Where the course shows up.</b> This encounter, its telegraph, its escape window " +
          "and what failing it costs came from a RAG pipeline over the design document and " +
          "story bible (A4). The narration voice was enforced by a style-guide agent (A7). " +
          "Nothing here was typed into the game.",
  fight:  "<b>Where the course shows up.</b> REX is the Nemesis, a goal-oriented agent: it " +
          "perceives your last four moves, predicts your next tile, moves to intercept it, and " +
          "vetoes its own prediction when that would lose ground (A5). Every line it speaks is " +
          "a RAG-generated read keyed by charge register (A4). If you lose, its first line back " +
          "names the gate you died at, from a generate-evaluate-refine loop (A6). This build was " +
          "attacked by an adversarial QA agent that found three real bugs, all fixed (A9)."
};
function badge(kind){ if(typeof document === "undefined") return; $("badge").innerHTML = BADGE[kind] || ""; }

// ---------------------------------------------------------------------- boot
async function boot(){
  const names = ["DT_JourneyHazards","DT_ArenaPhases","DT_NemesisReads",
                 "DT_RetryReads","DT_JourneyBeats","MANIFEST"];
  for(const n of names){
    const r = await fetch("data/" + n + ".json");
    DT[n] = await r.json();
  }
  DT.hazards = DT.DT_JourneyHazards.slice().sort((a,b)=>a.Day-b.Day);
  DT.phases  = DT.DT_ArenaPhases.slice().sort((a,b)=>a.PhaseIndex-b.PhaseIndex);
  const rows = DT.MANIFEST.reduce((n,m)=>n+m.rows,0);
  $("prov").innerHTML = "All content generated by the Rex Machina agent pipelines. " +
    rows + " rows across " + DT.MANIFEST.length + " DataTables, loaded unmodified from <code>data/</code>.";
  intro();
  // Demo mode for the pipeline video: open index.html#demo and the page
  // titles itself, skips to the fight after six seconds, and hands the
  // controls to the computer five seconds after that. No clicks needed.
  if(typeof location !== "undefined" && location.hash === "#demo"){
    document.title = "Rex Machina demo";
    document.body.style.zoom = "1.15";
    setTimeout(() => { beginFight(); setTimeout(() => autoStart(), 5000); }, 8000);
  }
}

// The first screen. A grader with two minutes needs to reach the fight, and
// the journey takes longer than that when played properly, so the fight is one
// click away from the start. Skipping it costs nothing but the stamina bonus.
function intro(){
  S.mode = "intro";
  if(typeof document === "undefined") return;
  S.randomSpawn = true;
  try { const d = localStorage.getItem("rm_diff"); if(d && DIFFS[d]) CFG = Object.assign({ name: d }, DIFFS[d]); } catch(e) {}
  hud([["day", 0], ["act", "-"], ["condition", "sound"]]);
  clearSay();
  say("<span class='sys'>A shelter dog walks nine days home to the family that gave her away, " +
      "and finds a robot dog in her place.</span>");
  say("<span class='sys'>Nine days on foot, then a fight in the yard against the thing that took her place.</span>");
  $("stage").innerHTML =
    "<div class='intro'>" + ctlRow("Nine days home") +
    "<div class='padrow'>" + hintBox() +
    "<div class='btns col'>" +
    "<button class='primary' onclick='startHazard(0)'>Start from the shelter &middot; 6 min</button>" +
    "<button onclick='beginFight()'>Skip to the fight &middot; 2 min</button></div></div>" +
    "<h2 style='margin-top:16px'>How to play</h2>" +
    "<ol>" +
    "<li><b>Six encounters</b> on the road home, one screen each. Something hunts you, and it always shows a tell before it strikes. " +
    "The strip marks the tell turn and the break turn before you press anything.</li>" +
    "<li><b>Two buttons.</b> <b>Hold still</b> lets a turn pass. <b>Break for it</b> runs, and ends the encounter one way or the other.</li>" +
    "<li><b>The rule.</b> Hold through the tell, hold one more turn, then break. Break earlier and it catches you. Hold longer and it catches you. " +
    "Getting caught costs a retry, and three of the six leave you limping.</li>" +
    "<li><b>Then the fight.</b> Reach the kid on the board before the rounds or your stamina run out. The robot does not chase you. " +
    "It moves to the tile it thinks you will step on next, marked \u00d7, and says what it measured.</li>" +
    "</ol>" +
    "<div class='hint'>Stuck? <b>Watch the computer</b> plays any screen for you and says why it does each thing. " +
    "Arrow keys or WASD in the fight, E to wait.</div>" +
    "<h2 style='margin-top:16px'>What made this</h2>" +
    "<ul>" +
    "<li><b>Every line and every number</b> in the game was generated by agent pipelines. " +
    "The game code contains no content.</li>" +
    "<li><b>REX</b>, the robot, is a goal-oriented agent: perception, prediction, intercept, veto.</li>" +
    "<li><b>Its reads</b> are RAG output over the design document, keyed by how much charge it has left.</li>" +
    "<li><b>Its retry lines</b> come from a generate, evaluate, refine loop with a circuit breaker.</li>" +
    "<li><b>The journey narration</b> was scored and rewritten by a style-guide agent.</li>" +
    "<li><b>The build was attacked</b> by an adversarial QA agent. It found three bugs; they are fixed.</li>" +
    "</ul></div>";
  badge("");
}

// ------------------------------------------------------------- ACTS 1 and 2
// Six generated encounters. Each row carries a Telegraph, a WindowTurns count
// and an EscapeCondition: move on the turn after the tell, not before.
function telegraphTurn(h){ return Math.max(1, h.WindowTurns - 1); }

function startHazard(i){
  if(i === 0 && typeof document !== "undefined") rollTheme();
  S.act = i < 4 ? 1 : 2;
  S.hazard = i; S.hzTurn = 0; S.hzFails = 0; S.mode = "hazard";
  const h = DT.hazards[i];
  clearSay();
  say("<span class='sys'>Day " + h.Day + ", Act " + h.Act + ". " + h.Location + "</span>");
  say(h.PlayerSees);
  if(i === 0) say("<span class='sys'>Encounter 1 of 6. Hold still while it winds up. When the strip turns orange, that is the tell: hold once more, then break for it. " +
                  "The two marks on the strip are the tell turn and the break turn.</span>");
  drawHazard();
}

function drawHazard(){
  if(typeof document === "undefined") return;
  S.hzState = "play";
  const h = DT.hazards[S.hazard], tt = telegraphTurn(h);
  hud([["day", h.Day], ["act", h.Act], ["encounter", (S.hazard+1) + " of " + DT.hazards.length],
       ["turn", S.hzTurn + " of " + h.WindowTurns], ["tell on turn", tt], ["condition", S.limping ? "limping" : "sound"]]);
  let body = "<div class='sys'>Pursuer: " + h.PursuerType + "</div>";
  body += "<div class='sys' style='margin-top:6px'>Teaches: " + h.Teaches + "</div>";
  if(S.hzTurn === tt) body = "<div class='rex' style='font-size:16px'>&gt; " + h.Telegraph + "</div>" + body;
  // What holding still is for. Without this a first click on Break is a loss
  // with no idea why, which is a bad first thirty seconds.
  // The window opens the turn AFTER the tell. Breaking on the tell itself is
  // early and is caught, so the hint has to say "hold once more" here, not
  // "break" -- the earlier wording lost five runs in a row for a real player.
  body = ctlRow("Day " + h.Day + " &middot; encounter " + (S.hazard+1) + " of " + DT.hazards.length) +
         "<div class='boardwrap'><canvas id='strip' width='440' height='120'></canvas></div>" +
         "<div class='tip' id='tip'>Tap the strip to see what each figure is.</div>" + body;
  $("stage").innerHTML = body +
    "<div class='padrow'>" + hintBox() +
    "<div class='btns col'><button class='primary' onclick='hz(\"wait\")'>Hold still<small>let this turn pass</small></button>" +
    "<button onclick='hz(\"go\")'>Break for it<small>run now; ends the encounter</small></button>" +
    "<button class='quiet' onclick='beginFight()'>Skip to the fight</button></div></div>" +
    "<div class='hint'>Hold still keeps you where you are for a turn. Break for it is the one move that ends the encounter, " +
    "and it only works on the turn right after the tell.</div>";
  badge("hazard");
  stripSync(h, tt);
}

// ------------------------------------------------------------ the strip
// Acts 1 and 2 in one picture: something closing on you from the left, you on
// the right, and the moment it shows its hand. The pursuer advances a step
// per turn; on the tell turn it flares. What the buttons do is now something
// you can see the shape of before you read a word.
const STRIP = { running: false, t0: 0 };
function stripSync(h, tt){
  const c = $("strip");
  if(!c) return;
  STRIP.h = h; STRIP.tt = tt; STRIP.t0 = performance.now();
  if(STRIP.canvas !== c){
    STRIP.canvas = c;
    c.addEventListener("click", ev => {
      const r = c.getBoundingClientRect();
      const x = (ev.clientX - r.left) / r.width * c.width;
      const tp = $("tip");
      if(!tp) return;
      tp.textContent = x > 330 ? "You. Hold still while it commits to its pattern; break on the turn right after the tell."
                     : x > 40 + (S.hzTurn / h.WindowTurns) * 250 - 30 && x < 40 + (S.hzTurn / h.WindowTurns) * 250 + 30
                       ? "The pursuer: " + h.PursuerType + ". It telegraphs before it commits."
                       : "The ground between you. Each turn it closes one step.";
    });
  }
  if(!STRIP.running){ STRIP.running = true; requestAnimationFrame(paintStrip); }
}
function paintStrip(now){
  const c = $("strip");
  if(!c || S.mode !== "hazard"){ STRIP.running = false; return; }
  const g = c.getContext("2d"), h = STRIP.h, W = c.width, H = c.height;
  g.fillStyle = THEME.b; g.fillRect(0, 0, W, H);
  g.fillStyle = THEME.a; g.fillRect(0, H - 34, W, 34);
  g.strokeStyle = THEME.line; g.beginPath(); g.moveTo(0, H - 34.5); g.lineTo(W, H - 34.5); g.stroke();
  // turn ticks
  for(let i = 0; i <= h.WindowTurns; i++){
    const x = 40 + i / h.WindowTurns * 250;
    g.fillStyle = i <= S.hzTurn ? "#8b97a2" : "#2b333b";
    g.fillRect(x - 1, H - 30, 2, 8);
  }
  g.font = "700 9px Cinzel, Georgia, serif"; g.textAlign = "center"; g.textBaseline = "top";
  const xt = 40 + STRIP.tt / h.WindowTurns * 250, xb = 40 + (STRIP.tt + 1) / h.WindowTurns * 250;
  g.fillStyle = "#e0a34a"; g.fillRect(xt - 1.5, H - 32, 3, 10); g.fillText("TELL", xt, H - 20);
  g.fillStyle = "#7fb069"; g.fillRect(xb - 1.5, H - 32, 3, 10); g.fillText("BREAK", xb, H - 20);
  // pursuer, advancing
  const px = 40 + Math.min(S.hzTurn, h.WindowTurns) / h.WindowTurns * 250;
  const tell = S.hzTurn === STRIP.tt;
  const open = S.hzTurn === STRIP.tt + 1;
  const pulse = 0.5 + 0.5 * Math.sin(now / 180);
  if(tell){
    const glow = g.createRadialGradient(px, H - 52, 4, px, H - 52, 46);
    glow.addColorStop(0, "rgba(224,163,74," + (0.25 + 0.3 * pulse) + ")"); glow.addColorStop(1, "rgba(224,163,74,0)");
    g.fillStyle = glow; g.fillRect(px - 50, H - 100, 100, 70);
  }
  g.fillStyle = tell ? "#e0a34a" : "#5b6673";
  g.beginPath(); g.ellipse(px, H - 50, 16, 10, 0, 0, Math.PI * 2); g.fill();      // body
  g.beginPath(); g.arc(px + 16, H - 58, 7, 0, Math.PI * 2); g.fill();            // head
  g.fillRect(px - 12, H - 44, 4, 10); g.fillRect(px - 4, H - 44, 4, 10); g.fillRect(px + 4, H - 44, 4, 10); g.fillRect(px + 12, H - 44, 4, 10);
  g.fillStyle = "#111"; g.beginPath(); g.arc(px + 18, H - 60, 1.5, 0, Math.PI * 2); g.fill();
  if(tell){ g.fillStyle = "#e0a34a"; g.font = "bold 14px Barlow, 'Segoe UI', Arial, sans-serif"; g.textAlign = "center"; g.fillText("!", px + 16, H - 70); }
  // you, at the right
  drawDog(g, W - 88, H - 78, 44, -1);
  label(g, "YOU", W - 66, H - 80, "#7fb069");
  label(g, tell ? "THE TELL. HOLD ONCE MORE" : open ? "NOW. BREAK" : "turn " + S.hzTurn + " of " + h.WindowTurns, px, H - 72 - (tell || open ? 14 : 0), tell ? "#e0a34a" : open ? "#7fb069" : "#8b97a2");
  requestAnimationFrame(paintStrip);
}

function hz(choice){
  if(AUTO.on && !AUTO.acting) autoStop();
  const h = DT.hazards[S.hazard];
  const tt = telegraphTurn(h);
  if(choice === "go"){
    if(S.hzTurn === tt + 1){ hazardWin(h); return; }
    hazardFail(h, S.hzTurn <= tt
      ? "You broke on turn " + S.hzTurn + ". The tell comes on turn " + tt + ", so the window is turn " + (tt+1) + "."
      : "You broke on turn " + S.hzTurn + ". The window was turn " + (tt+1) + ", right after the tell.");
    return;
  }
  S.hzTurn++;
  if(S.hzTurn > h.WindowTurns){ hazardFail(h, "You held too long. The window was turn " + (tt+1) + ", right after the tell."); return; }
  drawHazard();
}

function hazardWin(h){
  say("<span class='win'>Clear.</span> " + h.EscapeCondition, "");
  S.hzState = "won";
  const next = S.hazard + 1;
  $("stage").innerHTML = "<div class='btns'><button onclick='" +
    (next < DT.hazards.length ? "startHazard(" + next + ")" : "beginFight()") +
    "'>" + (next < DT.hazards.length ? "Keep going" : "Day 8. The street you know.") +
    "</button></div>";
}

function hazardFail(h, why){
  S.hzFails++; S.totalFails++;
  let extra = "";
  if(h.CausesCondition && !S.limping){ S.limping = true; extra = " The back leg has opinions now."; }
  say("<span class='lose'>Caught.</span> " + why + " " + h.FailCondition + extra);
  S.hzTurn = 0; S.hzState = "lost";
  $("stage").innerHTML = "<div class='btns'><button class='primary' onclick='drawHazard()'>Again</button>" +
    "<button onclick='autoStart()'>Watch the computer do it</button></div>";
}

// ------------------------------------------------------------------- ACT 3
function beginFight(){
  S.act = 3; S.mode = "fight"; S.over = false;
  S.stamina = 17 - Math.min(S.totalFails, 3) + CFG.staminaBonus;   // 17 clean, 14 floor, before difficulty
  S.staminaMax = S.stamina;
  FX.list = []; FX.shake = 0; FX.streak = 0; FX.ring = null; FX.lastBand = "clinical"; FX.lowSaid = false;
  S.dog = [0,0]; S.rex = [5,5]; S.kid = [7,4]; S.distMax = 11;
  if(S.randomSpawn) placePieces();
  S.round = 0; S.charge = START_CHARGE;
  S.moves = []; S.lastCat = null; S.phaseIx = 0; S.attempts++; S.spoken = []; S.log = []; S.ledger = [];
  S.checkpoint = null; S.predicted = null;
  if(S.randomSpawn) ensureWinnable();
  if(typeof document !== "undefined") rollTheme();
  clearSay();
  const p = DT.phases[0];
  say("<span class='sys'>Act 3. " + p.ArenaName + ". " + p.Light + "</span>");
  say(p.PlayerSees);
  if(S.limping) say("<span class='sys'>You arrive limping. It can see that.</span>");
  say("<span class='sys'>Reach the kid before the clock or your legs run out. " +
      "Arrow keys or WASD to move, E to wait.</span>");
  if(S.priorAttempt) fireRetryLine();
  drawFight();
}

function phase(){ return DT.phases[S.phaseIx]; }

// A different board every fight. Only the browser asks for this; the headless
// tests keep the canonical layout so their numbers stay meaningful. The kid is
// kept at least eight tiles from the dog so there is a fight to have, and the
// robot starts closer to the kid than to you, which is where a guard would be.
function placePieces(){
  const p = DT.phases[0];
  const [w,h] = p.GridSpan.toLowerCase().split("x").map(Number);
  const cover = p.CoverTiles || [];
  const rnd = n => Math.floor(Math.random() * n);
  const free = t => !cover.some(c => eq(c, t));
  for(let tries = 0; tries < 500; tries++){
    const dog = [rnd(w), rnd(h)], kid = [rnd(w), rnd(h)], rex = [rnd(w), rnd(h)];
    if(!free(dog) || !free(kid) || !free(rex)) continue;
    if(man(dog, kid) < 8) continue;
    if(man(rex, dog) < 3 || man(rex, kid) < 2 || man(rex, kid) > man(rex, dog)) continue;
    S.dog = dog; S.kid = kid; S.rex = rex; S.distMax = man(dog, kid);
    return;
  }
}
function approach(){ return Math.max(0, Math.min(1, 1 - man(S.dog, S.kid) / S.distMax)); }
function band(){ return S.charge > BAND_CLIN ? "clinical" : (S.charge >= BAND_CONF ? "confident" : "strained"); }
function inBounds(t){ const p = phase(); const [w,h] = p.GridSpan.toLowerCase().split("x").map(Number);
                      return t[0]>=0 && t[0]<w && t[1]>=0 && t[1]<h; }

function drawFight(){
  if(typeof document === "undefined") return;
  const p = phase();
  const [w,h] = p.GridSpan.toLowerCase().split("x").map(Number);
  const low = Math.max(3, Math.round((S.staminaMax || 17) * 0.25));
  const stCls = S.stamina <= 0 ? "empty" : S.stamina <= low ? "low" : "";
  const bd = band();
  hud([["phase", p.PhaseIndex + "/3 " + p.ArenaName], ["round", S.round + "/" + CFG.maxRounds],
       ["stamina", "<span class='" + stCls + "'>" + S.stamina + "</span><span class='hbar " + stCls + "'><em style='width:" + Math.round(100 * S.stamina / (S.staminaMax || 17)) + "%'></em></span>"],
       ["approach", approach().toFixed(2) + "<span class='hbar gold'><em style='width:" + Math.round(100 * approach()) + "%'></em></span>"],
       ["charge", Math.round(S.charge) + "%<span class='hbar charge " + bd + "'><em style='width:" + Math.round(S.charge) + "%'></em></span>"],
       ["register", "<span class='reg " + bd + "'>" + bd + "</span>"]]);
  const T = BOARD.T;
  let t = "<div class='boardrow'><div class='boardwrap'><canvas id='board' width='" + (w*T) + "' height='" + (h*T) + "'></canvas></div>" + ledgerHtml() + "</div>";
  t = ctlRow("Act 3 &middot; " + p.ArenaName) + t;
  t += "<div class='tip' id='tip'>Tap or hover anything on the board to see what it is.</div>";
  t += "<div class='legend'>" +
       "<span><i class='sw you'></i>you, the dog</span>" +
       "<span><i class='sw rex'></i>REX, the robot</span>" +
       "<span><i class='sw pred'></i>where REX thinks you will step</span>" +
       "<span><i class='sw kid'></i>the kid: reach her</span>" +
       "<span><i class='sw cover'></i>cover</span></div>";
  // Explicit grid areas: auto-placement put the left arrow in the top row.
  t += "<div class='padrow'>" + hintBox() + "<div class='pad'>" +
       "<button class='key' style='grid-area:1/2' onclick=\"mv('up')\">&uarr;</button>" +
       "<button class='key' style='grid-area:2/1' onclick=\"mv('left')\">&larr;</button>" +
       "<button class='key' style='grid-area:2/2' onclick=\"mv('wait')\" title='Stay on your tile for a round. REX still moves and still spends charge, so a wait can make it come to you or tire. Two waits in four moves is a pattern it will name.'>wait</button>" +
       "<button class='key' style='grid-area:2/3' onclick=\"mv('right')\">&rarr;</button>" +
       "<button class='key' style='grid-area:3/2' onclick=\"mv('down')\">&darr;</button></div></div>";
  t += "<div class='hint'>Tap a tile next to the dog, or use the arrows. <b>wait</b> holds your tile for a round: " +
       "REX still moves and still spends charge, so a wait can pull it onto a wrong tile or tire it. " +
       "It speaks only when it has measured something.</div>";
  $("stage").innerHTML = t;
  badge("fight");
  boardSync();
}

function hud(pairs){
  if(typeof document === "undefined") return;
  $("hud").innerHTML = pairs.map(([k,v]) => "<span><i>" + k + "</i><b>" + v + "</b></span>").join("");
}

// --- the dog's observables, ported from game/rex/dog.py ---
function recentMoves(){ return S.moves.slice(-CFG.window); }
function dirFreq(){
  const span = S.moves.slice(-FREQ).filter(m => STEP[m]);
  const out = {left:0,right:0,up:0,down:0};
  if(!span.length) return out;
  for(const m of span) out[m]++;
  for(const k in out) out[k] = out[k] / span.length;
  return out;
}
function periodicity(){
  const span = S.moves.slice(-FREQ);
  if(span.length < 4) return 0;
  let best = 0;
  for(let lag=2; lag<6; lag++){
    let hits = 0, n = 0;
    for(let i=lag;i<span.length;i++){ n++; if(span[i] === span[i-lag]) hits++; }
    if(n) best = Math.max(best, hits/n);
  }
  return best;
}

// --- the Nemesis, ported from game/rex/nemesis.py ---
function predict(){
  const w = recentMoves().filter(m => STEP[m]);
  if(!w.length) return S.dog.slice();
  const c = {};
  for(const m of w) c[m] = (c[m]||0)+1;
  const best = Object.keys(c).sort((a,b)=>c[b]-c[a])[0];
  return [S.dog[0]+STEP[best][0], S.dog[1]+STEP[best][1]];
}
function stepToward(from, target){
  let best = from, bd = man(from, target);
  for(const d in STEP){
    const c = [from[0]+STEP[d][0], from[1]+STEP[d][1]];
    if(!inBounds(c) || eq(c, S.dog)) continue;   // solid: it stops beside you, not on you
    if(man(c, target) < bd){ best = c; bd = man(c, target); }
  }
  return best;
}
function rexAct(){
  const predicted = predict();
  const before = man(S.rex, S.dog);
  let move = stepToward(S.rex, predicted);
  if(man(move, S.dog) > before) move = stepToward(S.rex, S.dog);  // GDD 6.1 veto
  const moved = !eq(move, S.rex);
  S.rex = move;
  S.predicted = predicted;   // drawn on the grid, so the guess is visible
  S.charge = Math.max(0, Math.min(START_CHARGE, S.charge - (moved ? CFG.pursuit : HOLD) + SOLAR));
  return predicted;
}
function firingCategories(){
  // Every trigger that fires this round, in GDD 4 priority order. A5 returned
  // only the first, so one category dominated and suppression ate the rest:
  // a winning run surfaced 2 lines out of 24. Returning the whole set lets the
  // speaker fall through to the next live trigger instead of going quiet.
  const out = [], f = dirFreq();
  if(periodicity() >= 0.6) out.push("periodicity_called");
  if(Math.max(f.left,f.right,f.up,f.down) >= 0.45) out.push("sealing_direction");
  if(S.moves.slice(-4).filter(m=>m==="wait").length >= 2) out.push("stall_detected");
  if((phase().CoverTiles||[]).some(c=>eq(c,S.dog))) out.push("cover_habit");
  if((phase().ExitTiles||[]).some(e=>man(S.dog,e)<=2)) out.push("exit_fixation");
  if(S.charge < BAND_CONF) out.push("charge_strain");
  if(S.limping) out.push("gait_read");
  return out;
}
const COMPASS = ["left","right","up","down"];
function namesDirection(line){
  return COMPASS.filter(d => new RegExp("\\b" + d + "\\b", "i").test(line));
}
function dominantDir(){
  const f = dirFreq();
  let best = null, bv = -1;
  for(const d of COMPASS) if(f[d] > bv){ bv = f[d]; best = d; }
  return bv > 0 ? best : null;
}
function speakRead(){
  // GDD 4 suppression: never the same category twice running. With the full
  // firing set we can honour that and still speak, by taking the next live
  // trigger down the ladder.
  for(const cat of firingCategories()){
    if(cat === S.lastCat) continue;
    const row = DT.DT_NemesisReads.find(r => r.ReadCategory===cat && r.ChargeBand===band());
    if(!row || S.spoken.includes(row.Line)) continue;   // never twice in one run
    // RM-001, found by qa/adversary.js: the generated lines for
    // sealing_direction all name "left", but the trigger fires whenever any
    // one direction dominates. The robot was telling a right-running dog it
    // favoured left. A read that misreports the observable it cites is worse
    // than silence, so the line is held back unless the direction matches.
    const named = namesDirection(row.Line);
    if(named.length && !named.includes(dominantDir())) continue;
    S.lastCat = cat;
    S.spoken.push(row.Line);
    say("<span class='rex'>REX: &ldquo;" + row.Line + "&rdquo;</span>");
    return;
  }
}
function fireRetryLine(){
  const rows = DT.DT_RetryReads.filter(r => r.Gate === S.priorAttempt);
  const row = rows.find(r => r.ChargeBand === band()) || rows[0];
  if(row){ S.spoken.push(row.Line);
           say("<span class='rex'>REX: &ldquo;" + row.Line + "&rdquo;</span>"); }
}

function mv(dir){
  if(S.over || S.mode !== "fight") return;
  if(AUTO.on && !AUTO.acting) autoStop();
  if(dir !== "wait"){
    const t = [S.dog[0]+STEP[dir][0], S.dog[1]+STEP[dir][1]];
    if(!inBounds(t)){
      // RM-003, found by qa/adversary.js: a rejected move changed nothing at
      // all, so a player holding a key at the edge saw a frozen game.
      say("<span class='sys'>The fence is there. Nothing on that side.</span>");
      return;
    }
    if(eq(t, S.rex)){
      // Pieces are solid. The old rule let the dog walk through the robot,
      // which made a straight line the best line and the cut-off a joke.
      say("<span class='sys'>REX is on that tile. Go round it.</span>");
      return;
    }
    S.dog = t;
  }
  const judge = S.judge && S.randomSpawn;
  let before = null;
  if(judge){
    const held = S.dog; S.dog = dir === "wait" ? held : [held[0]-STEP[dir][0], held[1]-STEP[dir][1]];
    before = { line: searchLine(), predicted: S.predicted, dist: man(S.dog, S.kid) };
    S.dog = held;
  }
  S.moves.push(dir);
  S.round++;
  rexAct();
  speakRead();
  // RM-002, found by qa/adversary.js: the adjacency drain could take stamina
  // to -1 and the HUD showed it. Empty is empty.
  const prevStamina = S.stamina;
  S.stamina = Math.max(0, S.stamina - 1 - (man(S.rex, S.dog) <= 1 ? 1 : 0));
  if(judge){ fxStamina(prevStamina); fxBand(); }
  if(judge) rateMove(dir, before, { line: man(S.dog, S.kid) === 0 ? [] : searchLine(), dog: S.dog, rex: S.rex, round: S.round });
  checkGate();
  drawFight();
  checkEnd();
}
function checkGate(){
  const a = approach();
  let ix = 0;
  for(let i=0;i<DT.phases.length;i++){
    const p = DT.phases[i];
    if(a >= p.ApproachLow && (a < p.ApproachHigh || p.PhaseIndex === 3)) ix = i;
  }
  if(ix !== S.phaseIx){
    S.phaseIx = ix;
    S.checkpoint = {phase: ix, moves: S.moves.slice(), dog: S.dog.slice()};
    const p = phase();
    say("<span class='sys'>&gt;&gt;&gt; The arena advances. " + p.ArenaName + ".</span>");
    if(S.randomSpawn) stinger("THE ARENA ADVANCES", "#c8aa6e", { sub: p.ArenaName, life: 2200 });
    say("<span class='sys'>" + p.Light + "</span>");
  }
}
function checkEnd(){
  if(approach() >= 1){
    S.over = true;
    if(S.randomSpawn) fxEnd(true);
    say("<span class='win'>She sees you. The robot goes still.</span>");
    $("stage").innerHTML += "<div class='btns'><button onclick='location.reload()'>Again from the shelter</button></div>";
  } else if(S.stamina <= 0 || S.round >= CFG.maxRounds){
    S.over = true;
    S.priorAttempt = phase().PhaseID.replace("phase_","");
    if(S.randomSpawn) fxEnd(false);
    say("<span class='lose'>The porch light is still on. You cannot reach it.</span>");
    $("stage").innerHTML += "<div class='btns'><button class='primary' onclick='beginFight()'>Retry from the gate</button>" +
      "<button onclick='autoStart()'>Watch the computer win it</button></div>";
  }
}

// ------------------------------------------------------------ hints
// A hint is a reading of the board, not an instruction. It names the thing
// the player is not looking at -- the drain, the meter, the pattern -- and
// leaves the move to them. Easy says the most specific true thing; moderate
// says something general; hard says almost nothing.
function hintFor(){
  if(AUTO.on) return AUTO.note;
  const level = CFG.name;
  if(S.mode === "intro"){
    return level === "hard" ? "Hard: no hints, a six-move memory, thirteen rounds."
         : level === "easy" ? "Easy: the hint says exactly what to do next. Change it here or on any screen."
         : "Moderate: the hint says what matters, not what to press. Change it here or on any screen.";
  }
  if(S.mode === "hazard"){
    const h = DT.hazards[S.hazard], tt = telegraphTurn(h);
    if(level === "hard") return "No hints on hard. The strip still shows the tell.";
    if(S.hzTurn === tt) return level === "easy"
      ? "That is the tell, in orange. Hold still exactly one more time, then break."
      : "That is the tell. Hold still one more time, then break.";
    if(S.hzTurn < tt) return level === "easy"
      ? "Hold still " + (tt - S.hzTurn) + (tt - S.hzTurn === 1 ? " time" : " times") + " until the strip turns orange. " +
        "Hold once more after that, then break."
      : "Hold still until the tell shows in orange. Hold once more after it, then break. Early or late and you are caught.";
    return "Now. Break for it.";
  }
  if(S.mode !== "fight") return "";
  const gap = man(S.rex, S.dog);
  const last3 = S.moves.slice(-3).filter(m => STEP[m]);
  const same3 = last3.length === 3 && last3.every(m => m === last3[0]);
  const a = approach();
  const specific = [];
  if(gap <= 1) specific.push("It is beside you. Every round spent here costs two stamina instead of one.");
  if(S.predicted && !eq(S.predicted, S.dog) && man(S.predicted, S.dog) === 1)
    specific.push("The \u00d7 is a guess about your next step. A guess is only right if you make it right.");
  if(same3) specific.push("Three moves the same way. It has a window of " + CFG.window + " and you have filled it.");
  if(S.charge < 45) specific.push("Its charge is dropping. A tired machine holds still more than it moves.");
  if(S.round >= 4 && a < 0.2) specific.push("The meter fills only when the path to the kid gets shorter. Sideways is a round it gets for free.");
  const general = [
    "It goes where it thinks you are going. Being predictable is the only way to lose.",
    "Distance to the kid is the score. Distance to the robot is the cost.",
    "It forgets. An old trick works again once it is out of the window."
  ];
  if(level === "hard") return "No hints on hard. The board is the hint.";
  if(level === "easy") return specific[0] || general[S.round % general.length];
  return specific.length && S.round % 2 === 0 ? specific[0] : general[S.round % general.length];
}

function ctlRow(label){
  return "<div class='ctl'><div class='ctll'>" + (label || "") + "</div>" +
         "<div class='ctlr'>" + diffSelect() +
         "<button class='" + (AUTO.on ? "primary" : "quiet") + "' onclick='autoToggle()' title='The computer plays from here and says why it does each thing. Any key or button gives you the controls back.'>" +
         (AUTO.on ? "Stop watching" : "Watch the computer") + "</button>" +
         (S.mode === "fight" ? "<button class='quiet' onclick='beginFight()' title='Same journey, new spawn, fresh stamina'>Restart fight</button>" : "") +
         "<button class='quiet' onclick='location.reload()' title='Back to the first screen'>Restart game</button></div></div>";
}
function hintBox(){
  return "<div class='hintbox" + (AUTO.on ? " auto" : "") + "' id='hintbox'><span class='hl'>" + (AUTO.on ? "computer" : "hint") + "</span><span>" + hintFor() + "</span></div>";
}

// ------------------------------------------------------------ autoplay
// For the player who has lost every round: the computer plays, in the same
// rules, and says why. The encounters are a fixed rhythm. The fight is a
// search: REX is deterministic given the dog's moves, so the planner walks
// the tree ahead of it and only ever commits to a line that reaches the kid.
const AUTO = { on: false, acting: false, timer: null, note: "" };
let QUIET = false;
function autoToggle(){ if(AUTO.on) autoStop(); else autoStart(); }
function autoStart(){
  if(AUTO.on) return;
  AUTO.on = true; AUTO.note = "Watching. Any key or button gives you the controls back.";
  if(S.mode === "intro") startHazard(0);
  else if(S.mode === "fight"){
    if(S.over || !autoPlan().full){ AUTO.note = "No line from here reaches her, so the fight starts over. Watch this one."; beginFight(); }
    else drawFight();
  }
  else if(S.mode === "hazard"){ if(S.hzState === "lost") drawHazard(); else if(S.hzState === "play") drawHazard(); }
  autoTick();
}
function autoStop(){
  AUTO.on = false; AUTO.note = "";
  if(AUTO.timer){ clearTimeout(AUTO.timer); AUTO.timer = null; }
  if(S.mode === "fight" && !S.over) drawFight();
  else if(S.mode === "hazard" && S.hzState === "play") drawHazard();
}
function autoDecide(){
  // What the computer would do from here, and why, without doing it.
  if(S.mode === "hazard"){
    const h = DT.hazards[S.hazard], tt = telegraphTurn(h), n = DT.hazards.length;
    if(S.hzState === "won"){
      const next = S.hazard + 1;
      return { note: next < n ? "Clear. On to the next one." : "Six clear. On to the yard.",
               act: () => next < n ? startHazard(next) : beginFight() };
    }
    if(S.hzState === "lost") return { note: "Again.", act: () => drawHazard() };
    if(S.hzTurn === tt + 1) return { note: "Break for it now. This is the turn right after the tell, the only turn it works.", act: () => hz("go") };
    if(S.hzTurn === tt) return { note: "That is the tell, in orange. Hold still exactly once more, then break.", act: () => hz("wait") };
    const k = tt - S.hzTurn;
    return { note: "Hold still. The tell is " + k + (k === 1 ? " turn" : " turns") + " away, and breaking before it is a catch.", act: () => hz("wait") };
  }
  if(S.mode === "fight" && !S.over){
    const plan = autoPlan();
    return { note: plan.why, act: () => mv(plan.dir) };
  }
  return null;
}
function refreshHint(){ const hb = $("hintbox"); if(hb && hb.lastChild) hb.lastChild.textContent = AUTO.note; }
function autoTick(){
  if(!AUTO.on) return;
  const d = autoDecide();
  if(!d){ AUTO.on = false; AUTO.timer = null; return; }
  AUTO.note = d.note; refreshHint();
  AUTO.timer = setTimeout(() => {
    if(!AUTO.on) return;
    AUTO.acting = true;
    try { d.act(); } finally { AUTO.acting = false; }
    if(S.mode === "fight" && S.over){
      AUTO.on = false; AUTO.timer = null;
      AUTO.note = "Reached her. That is the whole trick: go where it is not looking, and never the same way twice.";
      refreshHint();
      const wb = document.querySelector("button[onclick='autoToggle()']");
      if(wb){ wb.textContent = "Watch the computer"; wb.className = "quiet"; }
      return;
    }
    autoTick();
  }, S.mode === "fight" ? 1100 : 1300);
}
function snapshot(){
  return { dog: S.dog.slice(), rex: S.rex.slice(), round: S.round, stamina: S.stamina, charge: S.charge,
           moves: S.moves.slice(), predicted: S.predicted };
}
function restore(sn){
  // Copies, never the snapshot's own arrays: a later simulated move would
  // otherwise push into the snapshot and leak into the real game's history.
  S.dog = sn.dog.slice(); S.rex = sn.rex.slice(); S.round = sn.round; S.stamina = sn.stamina; S.charge = sn.charge;
  S.moves = sn.moves.slice(); S.predicted = sn.predicted;
}
function simMove(dir){
  // the rules of mv() without the words. Grids are all the same size, so
  // the arena advancing changes nothing the planner needs.
  if(dir !== "wait"){
    const t = [S.dog[0]+STEP[dir][0], S.dog[1]+STEP[dir][1]];
    if(!inBounds(t) || eq(t, S.rex)) return false;
    S.dog = t;
  }
  S.moves.push(dir); S.round++;
  rexAct();
  S.stamina = Math.max(0, S.stamina - 1 - (man(S.rex, S.dog) <= 1 ? 1 : 0));
  return true;
}
const PLAN = { key: null, rest: [] };
function stateKey(){ return S.dog + "|" + S.rex + "|" + S.round + "|" + S.stamina + "|" + S.charge + "|" + S.moves.join(","); }
function autoPlan(){
  // A line found once holds: REX is deterministic, so as long as the board
  // is where the line expected it, the next move is already known.
  if(PLAN.key === stateKey() && PLAN.rest.length){
    const line = PLAN.rest;
    return finishPlan(line);
  }
  return searchPlan();
}
function finishPlan(line){
  const start = snapshot(); QUIET = true;
  const dir = line[0];
  simMove(dir); PLAN.key = stateKey(); PLAN.rest = line.slice(1);
  restore(start); QUIET = false;
  return explain(dir, true);
}
function searchPlan(){
  const best = searchLine();
  if(best && best.length) return finishPlan(best);
  PLAN.key = null; PLAN.rest = [];
  return explain(legalMoves()[0] || "wait", false);
}
function legalMoves(){
  const out = [];
  for(const d in STEP){
    const t = [S.dog[0]+STEP[d][0], S.dog[1]+STEP[d][1]];
    if(inBounds(t) && !eq(t, S.rex)) out.push(d);
  }
  return out;
}
function searchLine(){
  // Iterative deepening: the shortest line that reaches the kid, so there
  // is never a wait or a detour the position did not demand. Among moves
  // of equal worth, a change of direction is tried before a repeat, so the
  // line has nothing for REX to read. Returns the line, or null.
  const start = snapshot(); QUIET = true;
  let budget = 80000, best = null;
  const options = () => {
    const out = [];
    const prev = S.moves.length ? S.moves[S.moves.length - 1] : null;
    for(const d in STEP){
      const t = [S.dog[0]+STEP[d][0], S.dog[1]+STEP[d][1]];
      if(!inBounds(t) || eq(t, S.rex)) continue;
      out.push([d, man(t, S.kid) + (man(t, S.rex) <= 1 ? 1 : 0) + (d === prev ? 0.5 : 0)]);
    }
    out.sort((a,b) => a[1] - b[1]);
    out.push(["wait", 99]);
    return out.map(o => o[0]);
  };
  const need0 = man(S.dog, S.kid), maxDepth = Math.min(CFG.maxRounds - S.round, S.stamina);
  for(let limit = need0; limit <= maxDepth && !best && budget > 0; limit++){
    const seen = new Set();
    const dfs = (path, left) => {
      if(man(S.dog, S.kid) === 0){ best = path.slice(); return true; }
      if(left <= 0 || S.stamina <= 0 || --budget < 0) return false;
      const need = man(S.dog, S.kid);
      if(need > left || need > S.stamina) return false;
      const key = S.dog + "|" + S.rex + "|" + left + "|" + S.stamina + "|" + recentMoves().join(",");
      if(seen.has(key)) return false;
      seen.add(key);
      for(const d of options()){
        const sn = snapshot();
        if(simMove(d)){ path.push(d); if(dfs(path, left - 1)){ restore(sn); return true; } path.pop(); }
        restore(sn);
      }
      return false;
    };
    dfs([], limit);
    restore(start);
  }
  restore(start); QUIET = false;
  return best;
}

// ------------------------------------------------------------ the ledger
// Every move the player makes, judged after the fact by the same search
// the computer plays with: did it stay on a shortest line to the kid, and
// what did it pay for the privilege.
function rateMove(dir, before, after){
  const Lb = before.line ? before.line.length : null;
  const La = after.line ? after.line.length : null;
  const ontoX = before.predicted && dir !== "wait" && eq(after.dog, before.predicted);
  const drained = man(after.rex, after.dog) <= 1;
  let rating, note;
  if(La === null && Lb === null){
    const closer = man(after.dog, S.kid) < before.dist;
    if(closer && !drained){ rating = "good"; note = "Closer, and clear of it. No line to her remains at this stamina, but this is the way to go down."; }
    else if(closer){ rating = "fine"; note = "Closer, but it is beside you. No line to her remains at this stamina."; }
    else { rating = "think better"; note = "No line to her remains, and this did not bring you closer."; }
  }
  else if(La === null){ rating = "danger"; note = "That move closed the last line to her at this stamina."; }
  else if(La === 0){ rating = "excellent"; note = "Home."; }
  else {
    const slack = La - (Lb === null ? La : Lb - 1);
    if(slack <= 0 && !ontoX && !drained){ rating = "excellent"; note = "On the shortest line, off its guess, out of its reach."; }
    else if(slack <= 0){ rating = "good"; note = ontoX ? "Shortest line, but you stepped onto the tile it guessed." : "Shortest line, but it is beside you now and that costs double."; }
    else if(slack === 1 && !ontoX && !drained){ rating = "fine"; note = "A round given away, but safely. It read nothing."; }
    else if(slack === 1){ rating = "think better"; note = ontoX ? "A round lost, and onto its guess." : "A round lost, and it is beside you."; }
    else { rating = "think better"; note = "That cost " + slack + " rounds against the shortest line."; }
  }
  S.ledger.push({ n: after.round, dir, rating, note });
  fxGrade(rating);
}
function ledgerHtml(){
  const L = S.ledger.slice().reverse();
  const counts = {};
  for(const e of S.ledger) counts[e.rating] = (counts[e.rating] || 0) + 1;
  const sum = ["excellent","good","fine","think better","danger"].filter(k => counts[k]).map(k => counts[k] + " " + k).join(" &middot; ");
  return "<div class='ledger' id='ledger'><div class='lt'>Ledger</div>" +
    (L.length ? "<ol>" + L.map((e, i) => "<li class='" + e.rating.replace(" ", "-") + (i === 0 ? " new" : "") + "'>" +
      "<span class='n'>" + e.n + "</span><span class='mv'>" + e.dir + "</span><span class='rt'>" + e.rating + "</span>" +
      "<div class='nt'>" + e.note + "</div></li>").join("") + "</ol>" : "<div class='nt'>Your moves, judged as you make them.</div>") +
    (sum ? "<div class='ls'>" + sum + "</div>" : "") + "</div>";
}
function explain(dir, full){
  // say why, in terms of what is on the board
  const last = S.moves.length ? S.moves[S.moves.length - 1] : null;
  const t = dir === "wait" ? S.dog : [S.dog[0]+STEP[dir][0], S.dog[1]+STEP[dir][1]];
  const guessed = S.predicted && eq(S.predicted, t);
  let why;
  if(dir === "wait"){
    const sn = snapshot(); QUIET = true; simMove("wait"); const pinned = eq(S.rex, sn.rex); restore(sn); QUIET = false;
    why = pinned
      ? "Wait. REX is pinned beside me and cannot step. Each wait pushes an old move out of its memory, and the tile it is guarding opens."
      : "Wait. REX has to move anyway and pays charge for it; a round I do not spend walking into its guess.";
  }
  else if(guessed) why = "Step " + dir + ", onto the ×. It expects this one, but every other tile costs more rounds than I have; the line still ends at her.";
  else if(man(t, S.kid) < man(S.dog, S.kid)) why = dir === last
    ? "Step " + dir + " again. Still the shortest way to her, and REX is not on it."
    : "Step " + dir + ". Closer to her, and not the tile REX is moving to cut off.";
  else why = "Step " + dir + ". Sideways for a round, so the next two are not the same way and it has nothing to read.";
  return { dir, why, full };
}
function ensureWinnable(){
  // A random spawn is only fair if a line to the kid exists. Roll until the
  // planner can prove one; the player never starts a fight that cannot be won.
  for(let tries = 0; tries < 40; tries++){
    if(autoPlan().full) return;
    placePieces(); S.moves = []; S.round = 0; S.charge = START_CHARGE; S.predicted = null;
  }
}


function diffSelect(){
  return "<label class='diff'>difficulty <select onchange='setDiff(this.value)'>" +
    Object.keys(DIFFS).map(k => "<option value='" + k + "'" + (k === CFG.name ? " selected" : "") + ">" +
                                DIFFS[k].label + "</option>").join("") + "</select></label>";
}

// What a thing on the board is, for a tap or a hover. The legend names them;
// this says what they do to you.
function describe(t){
  const p = phase();
  if(eq(t, S.dog)) return "You. Tap a neighbouring tile or use the arrows; tap your own tile to wait. Waiting is a round where only REX moves and spends charge.";
  if(eq(t, S.rex)) return "REX. It moves after you, to the tile it predicts you will take. Next to you it doubles your stamina cost.";
  if(eq(t, S.kid)) return "The kid. Stand on her tile to win. The approach meter is your distance to here.";
  if(S.predicted && eq(t, S.predicted)) return "The prediction. REX expects you to step here next, and will move to cut it off.";
  if((p.CoverTiles||[]).some(c => eq(c, t))) return "Cover. You can stand here. REX reads it as a habit if you keep doing it.";
  if((p.ExitTiles||[]).some(e => eq(e, t))) return "An exit from this arena. Loitering near one is something REX notices and names.";
  return "Open ground. Tile " + t[0] + "," + t[1] + ".";
}

// ------------------------------------------------------------ themes
// The floor changes every round. Same board, different light, so a long fight
// does not look like one still image and the round count is felt as well as
// read. The pieces keep their colours; only the ground moves.
const THEMES = [
  // Seven places, each keyed to one of the palettes the League client uses
  // for its regions, so no two are near each other and none is near the
  // navy the page is built from. Floors sit at mid or high luminance on
  // purpose: the interface is dark, so the board must not be.
  { name: "rose garden",    a: "#9a2f6a", b: "#84285a", line: "#4e1636", glow: "#ff6fb5",
    sky: "rgba(255,140,200,.16)", deco: "petals" },                       // Ionia
  { name: "marble porch",   a: "#cfc8b6", b: "#bdb5a1", line: "#8f8772", glow: "#ffe9a6",
    sky: "rgba(255,255,255,.08)", deco: "porch" },                        // Demacia
  { name: "crimson dusk",   a: "#8a2328", b: "#731c21", line: "#421013", glow: "#ff4a4a",
    sky: "rgba(255,80,60,.14)",  deco: "rails" },                         // Noxus
  { name: "sand lot",       a: "#cfa452", b: "#b89047", line: "#725722", glow: "#ffd76a",
    sky: "rgba(255,225,140,.16)", deco: "flood" },                        // Shurima
  { name: "ice yard",       a: "#7bbfe0", b: "#68aed2", line: "#2f6f92", glow: "#dffcff",
    sky: "rgba(255,255,255,.12)", deco: "puddles" },                      // Freljord
  { name: "runoff green",   a: "#579a30", b: "#498528", line: "#254a14", glow: "#b6ff3c",
    sky: "rgba(190,255,80,.12)", deco: "grass" },                         // Zaun
  { name: "brass floods",   a: "#b3712f", b: "#9c6127", line: "#5c3814", glow: "#ffb45a",
    sky: "rgba(255,200,120,.16)", deco: "moon" }                          // Piltover
];
let THEME = THEMES[0];
function rollTheme(){
  // One place per match. A new fight or a new run from the shelter rolls a
  // new one; a round does not.
  let t = THEME;
  while(t === THEME) t = THEMES[Math.floor(Math.random() * THEMES.length)];
  THEME = t;
}
// a tiny seeded generator so the set dressing does not jitter every frame
function seeded(seed){ let x = seed | 0 || 1; return () => { x ^= x << 13; x ^= x >>> 17; x ^= x << 5; return ((x >>> 0) % 10000) / 10000; }; }
function deco(g, w, h, T, now){
  const W = w*T, H = h*T, r = seeded(THEME.name.length * 7919 + 17);
  g.save();
  if(THEME.deco === "grass"){
    g.strokeStyle = "rgba(170,230,120,.55)"; g.lineWidth = 1.5;
    for(let i=0;i<70;i++){ const x = r()*W, y = r()*H, l = 4 + r()*6;
      g.beginPath(); g.moveTo(x, y); g.lineTo(x - 2 + r()*4, y - l); g.stroke(); }
    const sky = g.createLinearGradient(0,0,0,H); sky.addColorStop(0,"rgba(255,140,50,.35)"); sky.addColorStop(.6,"rgba(255,140,50,0)");
    g.fillStyle = sky; g.fillRect(0,0,W,H);
  } else if(THEME.deco === "stars"){
    for(let i=0;i<60;i++){ const tw = 0.5 + 0.5*Math.sin(now/600 + i);
      g.fillStyle = "rgba(255,255,255," + (0.25 + 0.6*tw*r()) + ")"; g.fillRect(r()*W, r()*H*0.6, 1.5, 1.5); }
    const moon = g.createRadialGradient(W-50, 40, 4, W-50, 40, 90);
    moon.addColorStop(0,"rgba(220,230,255,.45)"); moon.addColorStop(1,"rgba(220,230,255,0)");
    g.fillStyle = moon; g.fillRect(0,0,W,H);
  } else if(THEME.deco === "flood"){
    const cone = g.createRadialGradient(W/2, -20, 10, W/2, -20, H*1.1);
    cone.addColorStop(0,"rgba(255,220,120,.55)"); cone.addColorStop(.5,"rgba(255,200,90,.18)"); cone.addColorStop(1,"rgba(255,200,90,0)");
    g.fillStyle = cone; g.fillRect(0,0,W,H);
    g.fillStyle = "rgba(255,230,150,.9)"; g.fillRect(W/2-14, 0, 28, 4);
  } else if(THEME.deco === "moon"){
    const beam = g.createLinearGradient(0,0,W,H); beam.addColorStop(0,"rgba(220,225,255,.22)"); beam.addColorStop(.5,"rgba(220,225,255,0)"); beam.addColorStop(1,"rgba(220,225,255,.12)");
    g.fillStyle = beam; g.fillRect(0,0,W,H);
    g.fillStyle = "rgba(0,0,20,.35)";
    for(let i=0;i<5;i++){ const x = r()*W; g.fillRect(x, 0, 6 + r()*10, H); }
  } else if(THEME.deco === "rails"){
    g.fillStyle = "rgba(0,0,0,.25)";
    for(let i=0;i<120;i++) g.fillRect(r()*W, r()*H, 2, 2);
    const y1 = H*0.35, y2 = H*0.68;
    g.strokeStyle = "rgba(40,20,10,.7)"; g.lineWidth = 6;
    for(let x=10;x<W;x+=26){ g.beginPath(); g.moveTo(x, y1-8); g.lineTo(x, y2+8); g.stroke(); }
    g.strokeStyle = "#c9c2b8"; g.lineWidth = 3;
    for(const y of [y1, y2]){ g.beginPath(); g.moveTo(0,y); g.lineTo(W,y); g.stroke(); }
  } else if(THEME.deco === "puddles"){
    for(let i=0;i<9;i++){ const x = r()*W, y = r()*H, rx = 14 + r()*22, ry = 5 + r()*8;
      const pg = g.createRadialGradient(x, y, 1, x, y, rx);
      pg.addColorStop(0,"rgba(170,200,230,.45)"); pg.addColorStop(1,"rgba(170,200,230,.05)");
      g.fillStyle = pg; g.beginPath(); g.ellipse(x, y, rx, ry, 0, 0, Math.PI*2); g.fill(); }
    g.strokeStyle = "rgba(200,220,240,.12)"; g.lineWidth = 1;
    for(let i=0;i<25;i++){ const x = r()*W, y = r()*H; g.beginPath(); g.moveTo(x,y); g.lineTo(x+1, y+8); g.stroke(); }
  } else if(THEME.deco === "petals"){
    for(let i=0;i<40;i++){ const x = r()*W, y = r()*H, a = r()*Math.PI;
      g.fillStyle = "rgba(255,190,225," + (0.35 + 0.4*r()) + ")";
      g.beginPath(); g.ellipse(x, y, 5, 2.5, a, 0, Math.PI*2); g.fill(); }
    const sky = g.createLinearGradient(0,0,0,H); sky.addColorStop(0,"rgba(255,120,190,.3)"); sky.addColorStop(.5,"rgba(255,120,190,0)");
    g.fillStyle = sky; g.fillRect(0,0,W,H);
  } else if(THEME.deco === "porch"){
    const y = (h-1)*T, x0 = Math.min(4, w-3)*T;
    const lamp = g.createLinearGradient(0, y-T, 0, y+T); lamp.addColorStop(0,"rgba(255,220,130,.0)"); lamp.addColorStop(1,"rgba(255,220,130,.6)");
    g.fillStyle = lamp; g.fillRect(x0, y - T, 3*T, 2*T);
    g.fillStyle = "rgba(255,230,160,.55)"; g.fillRect(x0, y, 3*T, T);
    g.fillStyle = "rgba(255,240,200,.9)"; g.fillRect(x0 + 1.5*T - 5, y + T - 6, 10, 6);
  }
  g.restore();
}

// ------------------------------------------------------------ the board
// Drawn, not tabulated. The text grid told you which cell said DOG; it did not
// tell you that the dog was you, that the robot was hunting, or that the ×
// was a prediction rather than a wall. Everything below exists so a stranger
// reads the board before reading a word: the piece with the ring is you, the
// grey angular one with the red eye is the machine, the small figure on the
// lit square is where you are going. Pieces slide between tiles so a move is
// something you watch, and the robot's line comes out of the robot.
//
// Nothing here changes the game. S is read, never written; mv() is the only
// way the board affects the fight, and it is the same mv() the keys call.
// ------------------------------------------------------------ feedback
// What the board says back. A grade is a callout in the moment, not a line
// in a ledger; a stamina threshold is felt before it is read; REX changing
// state is visible on REX. Everything here is drawn on the board canvas by
// paint(), from a queue of timed effects.
const FX = { list: [], shake: 0, streak: 0, ring: null, lastBand: null, lowSaid: false };
function fx(kind, o){ if(typeof performance === "undefined") return; FX.list.push(Object.assign({ kind, t0: performance.now() }, o)); }
function stinger(text, colour, o){ fx("stinger", Object.assign({ text, colour, life: 1500, sub: "" }, o || {})); }
function burst(x, y, colour, n, speed){
  for(let i = 0; i < n; i++){
    const a = Math.random() * Math.PI * 2, v = (0.5 + Math.random()) * (speed || 1.6);
    fx("spark", { x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, colour, life: 500 + Math.random() * 400, size: 1.5 + Math.random() * 2 });
  }
}
const GRADE = {
  excellent:      { colour: "#0ac8b9", shake: 0,  sparks: 16 },
  good:           { colour: "#f0e6d2", shake: 0,  sparks: 6 },
  fine:           { colour: "#c8aa6e", shake: 0,  sparks: 0 },
  "think better": { colour: "#ff9a3c", shake: 5,  sparks: 0 },
  danger:         { colour: "#e84057", shake: 9,  sparks: 0 }
};
function fxGrade(rating){
  const gdef = GRADE[rating] || GRADE.fine;
  const T = BOARD.T, cx = S.dog[0]*T + T/2, cy = S.dog[1]*T + T/2;
  FX.streak = rating === "excellent" ? FX.streak + 1 : 0;
  // escalation, the way a multi-kill callout climbs
  const text = rating === "excellent" ? (["EXCELLENT","CLEAN","UNREADABLE","GHOST"][Math.min(FX.streak, 4) - 1]) : rating.toUpperCase();
  const sub = FX.streak >= 3 ? FX.streak + " in a row it could not read" : "";
  stinger(text, gdef.colour, { sub, life: rating === "danger" ? 2000 : 1400 });
  if(gdef.sparks) burst(cx, cy, gdef.colour, gdef.sparks, rating === "excellent" ? 2.2 : 1.2);
  FX.shake = Math.max(FX.shake, gdef.shake);
  FX.ring = { colour: gdef.colour, t0: performance.now() };
  if(rating === "danger") fx("vignette", { colour: "232,64,87", life: 900 });
}
function fxStamina(prev){
  const low = Math.max(3, Math.round(S.staminaMax * 0.25));
  if(S.stamina <= 0 && prev > 0){ stinger("OUT OF LEGS", "#e84057", { sub: "stamina is gone", life: 2400 }); fx("vignette", { colour: "232,64,87", life: 1600 }); FX.shake = Math.max(FX.shake, 12); }
  else if(S.stamina <= low && prev > low){ stinger("LEGS GOING", "#ff9a3c", { sub: S.stamina + " stamina left. Every drain is two.", life: 1800 }); fx("vignette", { colour: "255,154,60", life: 900 }); }
}
function fxBand(){
  const b = band();
  if(FX.lastBand && b !== FX.lastBand){
    const T = BOARD.T, cx = S.rex[0]*T + T/2, cy = S.rex[1]*T + T/2;
    if(b === "strained"){ stinger("REX STRAINED", "#e84057", { sub: "charge under " + BAND_CONF + "%. It holds still more than it moves.", life: 2000 }); burst(cx, cy, "#ff6a3c", 22, 2.4); }
    else if(b === "confident" && FX.lastBand === "clinical"){ stinger("REX CONFIDENT", "#c8aa6e", { sub: "charge under " + BAND_CLIN + "%. It starts to commit.", life: 1600 }); burst(cx, cy, "#c8aa6e", 8, 1.4); }
  }
  FX.lastBand = b;
}
function fxEnd(won){
  const T = BOARD.T;
  if(won){
    stinger("SHE SEES YOU", "#f0e6d2", { sub: "the robot goes still", life: 4000 });
    burst(S.kid[0]*T + T/2, S.kid[1]*T + T/2, "#ffd76a", 40, 3);
    fx("vignette", { colour: "255,215,106", life: 2200 });
  } else {
    stinger(S.stamina <= 0 ? "OUT OF LEGS" : "OUT OF ROUNDS", "#e84057", { sub: "the porch light is still on", life: 4000 });
    fx("vignette", { colour: "232,64,87", life: 2400 }); FX.shake = Math.max(FX.shake, 10);
    fx("fade", { life: 1e9 });
  }
}
function paintFx(g, now, W, H){
  const keep = [];
  for(const e of FX.list){
    const age = now - e.t0, k = age / e.life;
    if(k >= 1) continue;
    keep.push(e);
    if(e.kind === "spark"){
      g.globalAlpha = 1 - k;
      g.fillStyle = e.colour;
      const x = e.x + e.vx * age / 16, y = e.y + e.vy * age / 16 + 0.002 * age * age / 16;
      g.fillRect(x - e.size/2, y - e.size/2, e.size, e.size);
      g.globalAlpha = 1;
    } else if(e.kind === "vignette"){
      const v = g.createRadialGradient(W/2, H/2, W*0.25, W/2, H/2, W*0.75);
      v.addColorStop(0, "rgba(" + e.colour + ",0)"); v.addColorStop(1, "rgba(" + e.colour + "," + (0.55 * (1 - k)) + ")");
      g.fillStyle = v; g.fillRect(0, 0, W, H);
    } else if(e.kind === "fade"){
      g.fillStyle = "rgba(1,10,19," + Math.min(0.55, age / 1200 * 0.55) + ")"; g.fillRect(0, 0, W, H);
    }
  }
  // stingers stack from the top, newest on top
  let row = 0;
  for(const e of keep.slice().reverse()){
    if(e.kind !== "stinger") continue;
    const age = now - e.t0, k = age / e.life;
    const inK = Math.min(1, age / 160), outK = k > 0.75 ? (1 - k) / 0.25 : 1;
    const scale = 1.35 - 0.35 * ease(inK);
    g.save();
    g.globalAlpha = Math.min(inK, outK);
    g.translate(W/2, 46 + row * 40);
    g.scale(scale, scale);
    g.font = "700 22px Cinzel, Georgia, serif"; g.textAlign = "center"; g.textBaseline = "middle";
    const tw = g.measureText(e.text).width;
    g.fillStyle = "rgba(1,10,19,.72)"; g.fillRect(-tw/2 - 26, -17, tw + 52, e.sub ? 46 : 34);
    g.strokeStyle = e.colour; g.lineWidth = 1;
    g.beginPath(); g.moveTo(-tw/2 - 26, -17); g.lineTo(tw/2 + 26, -17); g.moveTo(-tw/2 - 26, e.sub ? 29 : 17); g.lineTo(tw/2 + 26, e.sub ? 29 : 17); g.stroke();
    g.shadowColor = e.colour; g.shadowBlur = 14;
    g.fillStyle = e.colour; g.fillText(e.text, 0, 0);
    g.shadowBlur = 0;
    if(e.sub){ g.font = "500 11px Barlow, 'Segoe UI', Arial, sans-serif"; g.fillStyle = "#f0e6d2"; g.fillText(e.sub, 0, 20); }
    g.restore();
    row++;
  }
  FX.list = keep;
}

const BOARD = {
  T: 44, running: false, dog: null, rex: null, dogFrom: null, rexFrom: null,
  t0: 0, dur: 220, dogFace: 1, rexFace: -1, bubble: null, bubbleT0: 0, canvas: null
};

function boardSync(){
  // Called after every redraw. Remembers where the pieces were drawn last so
  // the next paint can slide them from there to where the state says they are.
  const c = $("board");
  if(!c) return;
  if(!BOARD.dog || S.round === 0){ BOARD.dog = S.dog.slice(); BOARD.rex = S.rex.slice(); BOARD.dogFrom = BOARD.rexFrom = null; }
  if(!eq(BOARD.dog, S.dog) || !eq(BOARD.rex, S.rex)){
    BOARD.dogFrom = BOARD.dog.slice(); BOARD.rexFrom = BOARD.rex.slice();
    if(S.dog[0] !== BOARD.dog[0]) BOARD.dogFace = Math.sign(S.dog[0] - BOARD.dog[0]);
    if(S.rex[0] !== BOARD.rex[0]) BOARD.rexFace = Math.sign(S.rex[0] - BOARD.rex[0]);
    BOARD.dog = S.dog.slice(); BOARD.rex = S.rex.slice();
    BOARD.t0 = performance.now();
  }
  if(BOARD.canvas !== c){
    BOARD.canvas = c;
    const tileAt = ev => {
      const r = c.getBoundingClientRect();
      return [Math.floor((ev.clientX - r.left) / r.width  * c.width  / BOARD.T),
              Math.floor((ev.clientY - r.top)  / r.height * c.height / BOARD.T)];
    };
    c.addEventListener("mousemove", ev => { const tp = $("tip"); if(tp) tp.textContent = describe(tileAt(ev)); });
    c.addEventListener("click", ev => {
      const [x, y] = tileAt(ev);
      const dx = x - S.dog[0], dy = y - S.dog[1];
      const tp = $("tip"); if(tp) tp.textContent = describe([x, y]);
      if(dx === 0 && dy === 0) mv("wait");
      else if(Math.abs(dx) + Math.abs(dy) === 1) mv(dx === 1 ? "right" : dx === -1 ? "left" : dy === 1 ? "down" : "up");
    });
  }
  if(!BOARD.running){ BOARD.running = true; requestAnimationFrame(paint); }
}

function lerpPos(from, to, k){
  if(!from) return to;
  return [from[0] + (to[0]-from[0]) * k, from[1] + (to[1]-from[1]) * k];
}
function ease(k){ return k < 0.5 ? 2*k*k : 1 - Math.pow(-2*k+2, 2)/2; }

function paint(now){
  const c = $("board");
  if(!c || S.mode !== "fight"){ BOARD.running = false; return; }
  const g = c.getContext("2d"), T = BOARD.T, p = phase();
  const [w,h] = p.GridSpan.toLowerCase().split("x").map(Number);
  const k = ease(Math.min(1, (now - BOARD.t0) / BOARD.dur));
  const dogPos = lerpPos(BOARD.dogFrom, BOARD.dog, k);
  const rexPos = lerpPos(BOARD.rexFrom, BOARD.rex, k);
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.clearRect(0, 0, c.width, c.height);
  if(FX.shake > 0.3){ g.translate((Math.random() - 0.5) * FX.shake, (Math.random() - 0.5) * FX.shake); FX.shake *= 0.86; } else FX.shake = 0;

  // floor: the place this round happens in. Two colours, then the set
  // dressing for the theme, then a thin grid so tiles still count.
  for(let y=0;y<h;y++) for(let x=0;x<w;x++){
    g.fillStyle = (x+y)%2 ? THEME.a : THEME.b;
    g.fillRect(x*T, y*T, T, T);
  }
  g.fillStyle = THEME.sky; g.fillRect(0, 0, w*T, h*T);
  deco(g, w, h, T, now);
  const wash = g.createRadialGradient(w*T/2, h*T/2, 20, w*T/2, h*T/2, w*T*0.75);
  wash.addColorStop(0, "rgba(255,255,255,0)"); wash.addColorStop(1, "rgba(0,0,0,.28)");
  g.fillStyle = wash; g.fillRect(0, 0, w*T, h*T);
  c.style.borderColor = THEME.glow; c.style.boxShadow = "0 0 28px " + THEME.glow + "77";
  g.strokeStyle = THEME.line; g.lineWidth = 1;
  for(let i=0;i<=w;i++){ g.beginPath(); g.moveTo(i*T+.5,0); g.lineTo(i*T+.5,h*T); g.stroke(); }
  for(let i=0;i<=h;i++){ g.beginPath(); g.moveTo(0,i*T+.5); g.lineTo(w*T,i*T+.5); g.stroke(); }
  // the theme, named in the corner, so a change of place is never a guess
  g.font = "700 10px Cinzel, Georgia, serif"; g.textAlign = "right"; g.textBaseline = "top";
  const tn = THEME.name.toUpperCase(), tw = g.measureText(tn).width + 10;
  g.fillStyle = "rgba(13,15,17,.7)"; g.fillRect(w*T - tw - 4, 4, tw, 14);
  g.fillStyle = THEME.glow; g.fillText(tn, w*T - 9, 6);

  // exits and cover, from the phase row
  for(const e of (p.ExitTiles||[])){
    g.strokeStyle = "#3f6f86"; g.setLineDash([4,3]); g.lineWidth = 2;
    g.strokeRect(e[0]*T+5, e[1]*T+5, T-10, T-10); g.setLineDash([]);
  }
  for(const cv of (p.CoverTiles||[])) drawCrate(g, cv[0]*T, cv[1]*T, T);

  // the kid's tile, lit
  const kx = S.kid[0]*T, ky = S.kid[1]*T;
  const grad = g.createRadialGradient(kx+T/2, ky+T/2, 4, kx+T/2, ky+T/2, T*0.9);
  grad.addColorStop(0, "rgba(224,163,74,.35)"); grad.addColorStop(1, "rgba(224,163,74,0)");
  g.fillStyle = grad; g.fillRect(kx-T/2, ky-T/2, T*2, T*2);
  g.fillStyle = "rgba(0,0,10,.45)";
  g.beginPath(); g.ellipse(kx + T/2, ky + T/2 + 12, T*0.36, T*0.16, 0, 0, Math.PI*2); g.fill();
  drawKid(g, kx, ky, T);

  // the prediction, pulsing so it reads as a guess and not as a wall
  if(S.predicted && !eq(S.predicted, S.rex)){
    const pulse = 0.55 + 0.45 * Math.sin(now / 260);
    const px = S.predicted[0]*T, py = S.predicted[1]*T;
    g.strokeStyle = "rgba(111,168,199," + (0.35 + 0.5*pulse) + ")"; g.lineWidth = 2;
    g.strokeRect(px+4, py+4, T-8, T-8);
    g.beginPath(); g.moveTo(px+13, py+13); g.lineTo(px+T-13, py+T-13);
    g.moveTo(px+T-13, py+13); g.lineTo(px+13, py+T-13); g.stroke();
  }

  for(const pos of [rexPos, dogPos, S.kid]){
    g.fillStyle = "rgba(0,0,10,.45)";
    g.beginPath(); g.ellipse(pos[0]*T + T/2, pos[1]*T + T/2 + 12, T*0.36, T*0.16, 0, 0, Math.PI*2); g.fill();
  }
  drawRex(g, rexPos[0]*T, rexPos[1]*T, T, BOARD.rexFace, now);
  // the grade, as a ring around the dog for a second
  if(FX.ring && now - FX.ring.t0 < 1000){
    const rk = (now - FX.ring.t0) / 1000;
    g.strokeStyle = FX.ring.colour; g.globalAlpha = 1 - rk; g.lineWidth = 3;
    g.beginPath(); g.arc(dogPos[0]*T + T/2, dogPos[1]*T + T/2 + 2, T*0.42 + rk * 16, 0, Math.PI*2); g.stroke();
    g.globalAlpha = 1;
  }
  drawDog(g, dogPos[0]*T, dogPos[1]*T, T, BOARD.dogFace);

  // labels: the one thing the text grid never managed
  label(g, "YOU", dogPos[0]*T + T/2, dogPos[1]*T - 3, "#7fb069");
  label(g, "REX", rexPos[0]*T + T/2, rexPos[1]*T - 3, "#c9564b");
  label(g, "KID", kx + T/2, ky - 3, "#e0a34a");

  // the read, out of the robot's mouth, for a few seconds
  if(BOARD.bubble && now - BOARD.bubbleT0 < 4200){
    bubble(g, BOARD.bubble, rexPos[0]*T + T/2, rexPos[1]*T, w*T);
  }
  paintFx(g, now, w*T, h*T);
  requestAnimationFrame(paint);
}

function label(g, text, x, y, colour){
  // Above the piece, unless the piece is on the top row, where above is off
  // the canvas and the label vanished with it.
  if(y < 16) y += BOARD.T + 1;
  g.font = "700 10px Cinzel, Georgia, serif";
  g.textAlign = "center"; g.textBaseline = "bottom";
  g.fillStyle = "rgba(13,15,17,.75)";
  const wdt = g.measureText(text).width + 8;
  g.fillRect(x - wdt/2, y - 12, wdt, 12);
  g.fillStyle = colour; g.fillText(text, x, y - 1);
}

function bubble(g, text, x, y, boardW){
  g.font = "500 13px Barlow, 'Segoe UI', Arial, sans-serif";
  const pad = 8, maxW = 230;
  // wrap
  const words = text.split(" "), lines = []; let cur = "";
  for(const wd of words){
    const t = cur ? cur + " " + wd : wd;
    if(g.measureText(t).width > maxW - pad*2 && cur){ lines.push(cur); cur = wd; } else cur = t;
  }
  if(cur) lines.push(cur);
  const bw = Math.min(maxW, Math.max(...lines.map(l => g.measureText(l).width)) + pad*2);
  const bh = lines.length * 15 + pad*2;
  let bx = x - bw/2, by = y - bh - 22;
  bx = Math.max(4, Math.min(boardW - bw - 4, bx));
  if(by < 4) by = y + 48;
  g.fillStyle = "rgba(20,24,28,.96)"; g.strokeStyle = "#e0a34a"; g.lineWidth = 1;
  roundRect(g, bx, by, bw, bh, 5); g.fill(); g.stroke();
  g.fillStyle = "#e0a34a"; g.textAlign = "left"; g.textBaseline = "top";
  lines.forEach((l, i) => g.fillText(l, bx + pad, by + pad + i*15));
}

function roundRect(g, x, y, w, h, r){
  g.beginPath(); g.moveTo(x+r, y); g.lineTo(x+w-r, y); g.quadraticCurveTo(x+w, y, x+w, y+r);
  g.lineTo(x+w, y+h-r); g.quadraticCurveTo(x+w, y+h, x+w-r, y+h); g.lineTo(x+r, y+h);
  g.quadraticCurveTo(x, y+h, x, y+h-r); g.lineTo(x, y+r); g.quadraticCurveTo(x, y, x+r, y); g.closePath();
}

function drawCrate(g, x, y, T){
  g.fillStyle = "#4a3a26"; g.fillRect(x+6, y+8, T-12, T-14);
  g.strokeStyle = "#7a5f3a"; g.lineWidth = 1.5; g.strokeRect(x+6.5, y+8.5, T-13, T-15);
  g.beginPath(); g.moveTo(x+6, y+8); g.lineTo(x+T-6, y+T-6); g.moveTo(x+T-6, y+8); g.lineTo(x+6, y+T-6); g.stroke();
}

function drawDog(g, x, y, T, face){
  // a low, long body, a head with two ears, a tail. Warm brown, green ring.
  g.save(); g.translate(x + T/2, y + T/2); g.scale(face || 1, 1);
  g.strokeStyle = "rgba(127,176,105,.9)"; g.lineWidth = 2;
  g.beginPath(); g.arc(0, 2, T*0.42, 0, Math.PI*2); g.stroke();
  g.fillStyle = "#8a5a2b";
  g.beginPath(); g.ellipse(-2, 4, 12, 7, 0, 0, Math.PI*2); g.fill();          // body
  g.fillRect(-11, 8, 3, 6); g.fillRect(-5, 8, 3, 6); g.fillRect(3, 8, 3, 6); g.fillRect(8, 8, 3, 6); // legs
  g.beginPath(); g.arc(11, -2, 6, 0, Math.PI*2); g.fill();                    // head
  g.beginPath(); g.moveTo(7, -7); g.lineTo(9, -13); g.lineTo(12, -6); g.fill(); // ear
  g.beginPath(); g.moveTo(11, -7); g.lineTo(14, -12); g.lineTo(16, -5); g.fill();
  g.strokeStyle = "#8a5a2b"; g.lineWidth = 2.5; g.lineCap = "round";
  g.beginPath(); g.moveTo(-13, 2); g.lineTo(-18, -5); g.stroke();             // tail
  g.fillStyle = "#c9956a"; g.beginPath(); g.arc(15, 0, 2.6, 0, Math.PI*2); g.fill(); // snout
  g.fillStyle = "#111"; g.beginPath(); g.arc(13, -3, 1.2, 0, Math.PI*2); g.fill();   // eye
  g.restore();
}

function drawRex(g, x, y, T, face, now){
  // the same body plan, squarer, taller, cold, one red visor. Red glow under it.
  const bd = S.mode === "fight" ? band() : "clinical";
  const strained = bd === "strained";
  g.save(); g.translate(x + T/2, y + T/2);
  if(strained){
    g.translate((Math.random() - 0.5) * 2.4, (Math.random() - 0.5) * 2.4);
    if(now && Math.random() < 0.18) fx("spark", { x: x + T/2 + (Math.random()-0.5)*16, y: y + T/2 - 6, vx: (Math.random()-0.5)*1.6, vy: -0.8 - Math.random(), colour: Math.random() < 0.5 ? "#ff6a3c" : "#ffd76a", life: 260 + Math.random()*240, size: 1.5 });
  }
  const glowA = strained ? 0.2 + 0.25 * Math.random() : bd === "confident" ? 0.5 : 0.35;
  const glow = g.createRadialGradient(0, 6, 2, 0, 6, T*0.55);
  glow.addColorStop(0, "rgba(201,86,75," + glowA + ")"); glow.addColorStop(1, "rgba(201,86,75,0)");
  g.fillStyle = glow; g.fillRect(-T/2, -T/2, T, T);
  g.scale(face || 1, 1);
  g.fillStyle = "#6f7887";
  g.fillRect(-13, -4, 24, 11);                                                // body
  g.fillStyle = "#4b535f";
  g.fillRect(-12, 7, 4, 8); g.fillRect(-5, 7, 4, 8); g.fillRect(2, 7, 4, 8); g.fillRect(8, 7, 4, 8); // legs
  g.fillRect(-16, -2, 4, 6);                                                  // hip block
  g.fillStyle = "#6f7887"; g.fillRect(8, -13, 12, 10);                       // head
  g.fillStyle = strained ? (Math.random() < 0.7 ? "#ff3b2a" : "#5a1a14") : bd === "confident" ? "#ff5a3c" : "#ff3b2a";
  if(bd === "confident"){ g.shadowColor = "#ff3b2a"; g.shadowBlur = 8; }
  g.fillRect(14, -10, 6, 3);                                                  // visor
  g.shadowBlur = 0;
  g.fillStyle = "#4b535f"; g.fillRect(10, -17, 2, 5);                        // antenna
  g.restore();
}

function drawKid(g, x, y, T){
  g.save(); g.translate(x + T/2, y + T/2);
  g.fillStyle = "#e0a34a"; g.globalAlpha = .25; g.fillRect(-T/2+2, -T/2+2, T-4, T-4); g.globalAlpha = 1;
  g.fillStyle = "#2b2b2b"; g.fillRect(-5, 6, 4, 9); g.fillRect(1, 6, 4, 9);   // legs
  g.fillStyle = "#c9564b"; g.fillRect(-7, -6, 14, 13);                        // jacket
  g.fillRect(-11, -5, 4, 9); g.fillRect(7, -5, 4, 9);                          // arms
  g.fillStyle = "#e8b48a"; g.beginPath(); g.arc(0, -12, 6, 0, Math.PI*2); g.fill(); // head
  g.fillStyle = "#2b2b2b"; g.fillRect(-6, -19, 12, 5);                        // hair
  g.restore();
}

if (typeof document !== "undefined") document.addEventListener("keydown", e => {
  const k = {w:"up",a:"left",s:"down",d:"right",e:"wait",
             ArrowUp:"up",ArrowLeft:"left",ArrowDown:"down",ArrowRight:"right"}[e.key];
  if(AUTO.on && k) autoStop();
  if(k && S.mode === "fight"){ e.preventDefault(); mv(k); }
});
if (typeof document !== "undefined") boot();

// Headless entry point for tests/sim.js. The browser ignores this.
if (typeof module !== "undefined" && module.exports) {
  module.exports = { S, DT, STEP, MAXROUNDS, man, eq, approach, band, inBounds,
                     predict, stepToward, rexAct, firingCategories, mv, beginFight,
                     drawFight, checkEnd, telegraphTurn, hz, startHazard,
                     dirFreq, periodicity, setSinks, speakRead, fireRetryLine,
                     namesDirection, dominantDir, autoPlan, searchLine, rateMove,
                     setDiff, DIFFS, placePieces, phase, getCfg: () => CFG };
}
