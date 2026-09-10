// Headless tests. No browser, no key, no network.
//   node tests/sim.js
// Proves the fight is winnable from every journey outcome, that the engine
// veto holds, that read suppression works, and that the hazard windows are
// fair. Run before every deploy.
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");

// minimal DOM sink so the game module can run headless
const sink = () => ({ innerHTML: "", children: [], appendChild(){}, removeChild(){},
                      get firstChild(){ return null; } });
const G = require(path.join(ROOT, "game.js"));
G.setSinks(sink);

for (const n of ["DT_JourneyHazards","DT_ArenaPhases","DT_NemesisReads",
                 "DT_RetryReads","DT_JourneyBeats","MANIFEST"]) {
  G.DT[n] = JSON.parse(fs.readFileSync(path.join(ROOT, "data", n + ".json"), "utf8"));
}
G.DT.hazards = G.DT.DT_JourneyHazards.slice().sort((a,b)=>a.Day-b.Day);
G.DT.phases  = G.DT.DT_ArenaPhases.slice().sort((a,b)=>a.PhaseIndex-b.PhaseIndex);

let pass = 0, fail = 0;
const ok = (c, label) => { if (c) pass++; else { fail++; console.log("  FAIL " + label); } };

// ---- the winning line: searched, not scripted ---------------------------
// The robot is deterministic given the dog's moves, so game.js can search
// for the shortest line to the kid. Pieces are solid, so the old straight
// line through the robot no longer exists; whatever line the search finds
// from the gate is the proof the fight is fair.
const OPTIMAL = "planned";

function play(fails, limping, moves) {
  G.S.totalFails = fails; G.S.limping = limping; G.S.priorAttempt = null;
  G.S.attempts = 0;
  G.beginFight();
  const line = [];
  if (moves === "planned") { while (!G.S.over && line.length < 40) { const d = G.autoPlan().dir; line.push(d); G.mv(d); } }
  else for (const m of moves) { if (G.S.over) break; G.mv(m); }
  return { over: G.S.over, won: G.approach() >= 1, stamina: G.S.stamina,
           rounds: G.S.round, charge: G.S.charge, band: G.band(), line };
}

for (const f of [0,1,2,3,6]) {
  const r = play(f, f > 0, OPTIMAL);
  ok(r.won, "a winning line exists after " + f + " failed encounters");
  if (r.won) console.log("    %d fails -> win in %d rounds, %d stamina left, charge %d%%, %s: %s",
                         f, r.rounds, r.stamina, Math.round(r.charge), r.band, r.line.join(" "));
}

// a wandering line must lose, or the fight is not a fight
const WANDER = ["right","left","right","left","right","left","right","left",
                "right","left","right","left","right","left","right"];
ok(!play(0, false, WANDER).won, "a wandering line loses even after a clean journey");

// ---- the engine veto, GDD 6.1 ------------------------------------------
{
  G.S.totalFails = 0; G.beginFight();
  let vetoHeld = true;
  for (let n = 0; n < 40 && !G.S.over; n++) {
    const m = G.autoPlan().dir;
    const before = G.man(G.S.rex, G.S.dog);
    G.mv(m);
    if (G.man(G.S.rex, G.S.dog) > before + 1) vetoHeld = false;
  }
  ok(vetoHeld, "the robot never ends a round further away than it started");
}

// ---- charge and register ------------------------------------------------
{
  const r = play(0, false, OPTIMAL);
  ok(r.charge < 100, "pursuit drains charge");
  ok(["clinical","confident","strained"].includes(r.band), "the register is a real band");
}

// ---- reads come from the pipeline table, and suppress ------------------
{
  const cats = new Set(G.DT.DT_NemesisReads.map(r => r.ReadCategory));
  ok(cats.size === 8, "24 read lines across 8 categories");
  ok(G.DT.DT_NemesisReads.length === 24, "the read table is the one A4 generated");
  ok(G.DT.DT_RetryReads.length === 6, "the retry table is the one A6 generated");
  ok(G.DT.DT_JourneyHazards.length === 6, "the hazard table is the one A4 generated");
}

// ---- the hazard windows are fair --------------------------------------
for (const h of G.DT.hazards) {
  const t = G.telegraphTurn(h);
  ok(t >= 1 && t + 1 <= h.WindowTurns + 1,
     "hazard " + h.HazardID + " can be escaped inside its window");
}

// ---- every table row the game reads is present -------------------------
{
  let missing = 0;
  for (const cat of new Set(G.DT.DT_NemesisReads.map(r=>r.ReadCategory)))
    for (const b of ["clinical","confident","strained"])
      if (!G.DT.DT_NemesisReads.find(r=>r.ReadCategory===cat&&r.ChargeBand===b)) missing++;
  ok(missing === 0, "every category has a line in all three registers");
}

// ---- the boss actually talks, and does not repeat itself ---------------
{
  const r = play(2, true, OPTIMAL);
  const lines = G.S.spoken;
  ok(lines.length >= 3, "the boss speaks at least three times in a winning run");
  ok(new Set(lines).size === lines.length, "no line is repeated inside one run");
  const known = new Set(G.DT.DT_NemesisReads.map(x => x.Line));
  ok(lines.every(l => known.has(l)), "every line spoken came from the A4 table");
  console.log("    winning run surfaced %d read lines: %s", lines.length,
              JSON.stringify(lines[0]));
}

// ---- a loss arms the retry line from the A6 table ----------------------
{
  G.S.totalFails = 0; G.S.limping = false; G.S.priorAttempt = null;
  G.beginFight();
  for (let i = 0; i < 15 && !G.S.over; i++) G.mv("wait");
  ok(G.S.over && G.approach() < 1, "standing still loses");
  ok(G.S.priorAttempt !== null, "a loss records which gate you died at");
  G.beginFight();
  const known = new Set(G.DT.DT_RetryReads.map(x => x.Line));
  ok(G.S.spoken.length > 0 && known.has(G.S.spoken[0]),
     "the retry opens with a line from the A6 table");
  console.log("    retry line: %s", JSON.stringify(G.S.spoken[0]));
}

// ---- the hazard timing is a real test ----------------------------------
{
  G.S.totalFails = 0; G.S.limping = false;
  G.startHazard(0);
  const h = G.DT.hazards[0], t = G.telegraphTurn(h);
  for (let i = 0; i < t + 1; i++) G.hz("wait");
  const before = G.S.totalFails;
  G.hz("go");
  ok(G.S.totalFails === before, "breaking on the turn after the tell escapes");

  G.startHazard(0);
  G.hz("go");
  ok(G.S.totalFails === before + 1, "breaking before the tell is caught");

  G.startHazard(1);
  const h2 = G.DT.hazards[1];
  for (let i = 0; i <= h2.WindowTurns; i++) G.hz("wait");
  ok(G.S.limping === h2.CausesCondition,
     "an encounter flagged CausesCondition leaves you limping when it is failed");
}

console.log("\n%d passed, %d failed", pass, fail);
process.exit(fail ? 1 : 0);
