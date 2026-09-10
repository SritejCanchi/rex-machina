// The Chaos Crew: an adversarial tester for Rex Machina.
//   node qa/adversary.js [runs]
//
// It does not play the game. It tries to break it. The strategy list is not
// generic: GDD 3 names six exploits that were found in the v3 stress test and
// closed, and five of them are re-attempted here directly. The rest are
// invariants the fight must never violate, plus a fuzzer for what nobody
// thought of.
//
// Writes qa/report.json.
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
const G = require(path.join(ROOT, "game.js"));
G.setSinks(() => ({ innerHTML:"", children:[], appendChild(){}, removeChild(){},
                    get firstChild(){ return null; } }));
for (const n of ["DT_JourneyHazards","DT_ArenaPhases","DT_NemesisReads",
                 "DT_RetryReads","DT_JourneyBeats","MANIFEST"])
  G.DT[n] = JSON.parse(fs.readFileSync(path.join(ROOT,"data",n+".json"),"utf8"));
G.DT.hazards = G.DT.DT_JourneyHazards.slice().sort((a,b)=>a.Day-b.Day);
G.DT.phases  = G.DT.DT_ArenaPhases.slice().sort((a,b)=>a.PhaseIndex-b.PhaseIndex);

const findings = [];
const measurements = {};      // evidence that is not a defect, but is the point
let checks = 0;
function report(f){
  checks++;
  findings.push(Object.assign({
    id: "RM-" + String(findings.length + 1).padStart(3, "0"),
    found_at: new Date().toISOString()
  }, f));
}
function snapshot(){
  return { round: G.S.round, dog: G.S.dog.slice(), rex: G.S.rex.slice(),
           stamina: G.S.stamina, charge: Math.round(G.S.charge),
           approach: Number(G.approach().toFixed(3)), register: G.band(),
           phase: G.DT.phases[G.S.phaseIx].PhaseID, moves: G.S.moves.slice(-6) };
}
function fresh(fails=0, limping=false){
  G.S.totalFails = fails; G.S.limping = limping; G.S.priorAttempt = null;
  G.beginFight();
}
// A fight from a random spawn, the way the shipped build starts one. The
// fixed [0,0] opening the sections below use is a test fixture; the player
// never sees it, so anything that only breaks on a random board would have
// gone out undetected.
function freshRandom(fails=0, limping=false){
  G.S.randomSpawn = true;
  try { fresh(fails, limping); } finally { G.S.randomSpawn = false; }
}
function legalDirs(){
  return ["left","right","up","down"].filter(d => {
    const t = [G.S.dog[0] + G.STEP[d][0], G.S.dog[1] + G.STEP[d][1]];
    return G.inBounds(t) && !G.eq(t, G.S.rex);
  }).concat(["wait"]);
}
const DIRS = ["up","down","left","right","wait"];
let seed = 20260907;
const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
const pick = a => a[Math.floor(rnd() * a.length)];

// --- 1. GDD 3 exploit 4: the approach ratchet ---------------------------
// Step in and step out. If approach banks progress the fight is free.
(function ratchet(){
  fresh();
  const start = G.approach();
  let peak = start;
  for (let i = 0; i < 6 && !G.S.over; i++){
    G.mv("right"); peak = Math.max(peak, G.approach());
    G.mv("left");
    if (G.approach() > start + 1e-9)
      return report({ location: "Act 3 / approach meter (game.js approach())",
        error_type: "exploit_reintroduced",
        severity: "critical",
        summary: "Stepping out did not give back the approach that stepping in bought.",
        game_context: snapshot(),
        repro: "right, left, repeated from the start tile",
        gdd_reference: "GDD 3 exploit 4, the approach ratchet" });
  }
  checks++;
})();

// --- 2. GDD 3 exploit 2: the leash --------------------------------------
// Bait the robot at its predicted tile and try to walk it away from you.
(function leash(){
  fresh();
  let worst = 0;
  const pattern = ["right","right","up","up","left","left","down","down"];
  for (let i = 0; i < 14 && !G.S.over; i++){
    const before = G.man(G.S.rex, G.S.dog);
    G.mv(pattern[i % pattern.length]);
    const after = G.man(G.S.rex, G.S.dog);
    worst = Math.max(worst, after - before);
    if (after > before + 1)
      return report({ location: "Act 3 / Nemesis intercept (game.js rexAct())",
        error_type: "exploit_reintroduced", severity: "critical",
        summary: "The robot ended a round further from the dog than it began, by more than the dog's own step. The engine-side veto did not hold.",
        game_context: snapshot(),
        repro: pattern.join(", ") + " on a loop",
        gdd_reference: "GDD 6.1, reject any intercept_move that increases true distance" });
  }
  checks++;
})();

// --- 3. GDD 3 exploit 5: window aliasing --------------------------------
// A 5-beat cycle never repeats inside a 4-move window. The two engine
// scalars are supposed to catch it anyway.
(function aliasing(){
  fresh();
  const cycle = ["right","right","down","left","up"];
  for (let i = 0; i < 15 && !G.S.over; i++) G.mv(cycle[i % 5]);
  const caught = G.S.spoken.length > 0;
  if (!caught)
    report({ location: "Act 3 / Nemesis perception (firingCategories, periodicity)",
      error_type: "exploit_reintroduced", severity: "high",
      summary: "A five-beat movement cycle drew no read at all across a full fight. The periodicity and frequency scalars did not see it.",
      game_context: snapshot(),
      repro: cycle.join(", ") + " repeated for 15 rounds",
      gdd_reference: "GDD 3 exploit 5, window aliasing" });
  checks++;
})();

// --- 4. GDD 3 exploit 3: no fail state ----------------------------------
(function failState(){
  fresh(0, false);
  for (let i = 0; i < 40 && !G.S.over; i++) G.mv("wait");
  if (!G.S.over || G.approach() >= 1)
    report({ location: "Act 3 / round loop (checkEnd)",
      error_type: "no_fail_state", severity: "critical",
      summary: "Standing still for the whole fight did not end it as a loss.",
      game_context: snapshot(), repro: "wait, 40 times",
      gdd_reference: "GDD 3 exploit 3, no fail state" });
  checks++;
})();

// --- 5. does the read line actually describe what the dog did? ----------
// sealing_direction fires when any one compass direction dominates. The line
// it speaks is a fixed string. If that string names a direction, it had
// better be the direction the dog favoured.
(function readTruth(){
  for (const dir of ["right","up","down","left"]){
    fresh();
    const seen = [];
    for (let i = 0; i < 9 && !G.S.over; i++){
      const before = G.S.spoken.length;
      G.mv(dir);
      if (G.S.spoken.length > before) seen.push(G.S.spoken[G.S.spoken.length-1]);
    }
    const f = G.dirFreq();
    const dominant = Object.keys(f).sort((a,b)=>f[b]-f[a])[0];
    for (const line of seen){
      const named = ["left","right","up","down"].filter(d =>
        new RegExp("\\b" + d + "\\b", "i").test(line));
      if (named.length && !named.includes(dominant)){
        report({ location: "Act 3 / read selection (speakRead) x DT_NemesisReads.json",
          error_type: "content_logic_mismatch", severity: "high",
          summary: "The robot cited a direction the dog never favoured. The line reads " +
                   JSON.stringify(line) + " while the dominant direction was " +
                   dominant + " at " + Math.round(f[dominant]*100) + " percent.",
          game_context: snapshot(),
          repro: "move " + dir + " nine times from the start tile",
          gdd_reference: "GDD 4, the read reports what the Nemesis measured" });
        return;
      }
    }
  }
  checks++;
})();

// --- 6. invariants under random play ------------------------------------
(function fuzz(runs){
  const bad = { charge:0, bounds:0, hang:0, unknownLine:0, negStam:0 };
  const known = new Set(G.DT.DT_NemesisReads.map(r=>r.Line)
                  .concat(G.DT.DT_RetryReads.map(r=>r.Line)));
  let worstStam = 0;
  for (let r = 0; r < runs; r++){
    fresh(Math.floor(rnd()*4), rnd() < 0.5);
    let steps = 0;
    while (!G.S.over && steps < 200){ G.mv(pick(DIRS)); steps++; }
    if (steps >= 200) bad.hang++;
    if (G.S.charge < 0 || G.S.charge > 100) bad.charge++;
    if (!G.inBounds(G.S.dog) || !G.inBounds(G.S.rex)) bad.bounds++;
    if (G.S.spoken.some(l => !known.has(l))) bad.unknownLine++;
    if (G.S.stamina < 0){ bad.negStam++; worstStam = Math.min(worstStam, G.S.stamina); }
    checks += 5;
  }
  if (bad.hang) report({ location:"Act 3 / round loop", error_type:"non_termination",
    severity:"critical", summary: bad.hang + " of " + runs + " random fights never ended.",
    game_context: snapshot(), repro:"random legal inputs" });
  if (bad.charge) report({ location:"Act 3 / Nemesis charge (rexAct)", error_type:"range_violation",
    severity:"medium", summary:"Charge left the 0 to 100 range in " + bad.charge + " runs.",
    game_context: snapshot(), repro:"random legal inputs" });
  if (bad.bounds) report({ location:"Act 3 / movement", error_type:"boundary_break",
    severity:"critical", summary:"A pawn left the grid in " + bad.bounds + " runs.",
    game_context: snapshot(), repro:"random legal inputs" });
  if (bad.unknownLine) report({ location:"Act 3 / read selection", error_type:"content_provenance",
    severity:"high", summary:"A spoken line was not in any generated DataTable, in " +
    bad.unknownLine + " runs.", game_context: snapshot(), repro:"random legal inputs" });
  if (bad.negStam) report({ location:"Act 3 / stamina (mv, checkEnd)", error_type:"state_underflow",
    severity:"medium",
    summary:"Stamina went below zero before the round ended, reaching " + worstStam +
            ", in " + bad.negStam + " of " + runs + " runs. The HUD can show a negative number.",
    game_context: snapshot(), repro:"random legal inputs until the adjacency drain overshoots" });
})(Number(process.argv[2] || 300));

// --- 7. boundary probing -------------------------------------------------
(function walls(){
  fresh();
  const before = { round: G.S.round, stam: G.S.stamina, rex: G.S.rex.slice(), log: G.S.log.length };
  for (let i = 0; i < 12; i++){ G.mv("up"); G.mv("left"); }   // both walls at (0,0)
  if (G.S.round !== before.round)
    report({ location:"Act 3 / movement (mv)", error_type:"free_action", severity:"low",
      summary:"Pressing into a wall advanced the round counter.", game_context:snapshot(),
      repro:"up and left repeatedly from the corner tile (0,0)" });
  else if(G.S.stamina === before.stam && G.eq(G.S.rex, before.rex)
          && G.S.log.length === before.log)
    report({ location:"Act 3 / movement (mv)", error_type:"soft_lock_risk", severity:"low",
      summary:"Pressing into a wall is a complete no-op: no round, no stamina, no robot move, and nothing written to the message log. A player holding a key at the edge sees a frozen game with no feedback.",
      game_context:snapshot(),
      repro:"hold the up arrow at the top edge; nothing on screen changes" });
  checks++;
})();

// --- 8. the hazards: is any encounter unwinnable or unloseable? ----------
(function hazards(){
  for (let i = 0; i < G.DT.hazards.length; i++){
    const h = G.DT.hazards[i], t = G.telegraphTurn(h);
    G.S.totalFails = 0; G.S.limping = false;
    G.startHazard(i);
    for (let k = 0; k < t + 1; k++) G.hz("wait");
    const before = G.S.totalFails;
    G.hz("go");
    if (G.S.totalFails !== before)
      report({ location:"Acts 1-2 / " + h.HazardID + " (hz)", error_type:"unwinnable_encounter",
        severity:"critical",
        summary:"Breaking on the turn after the tell did not escape " + h.HazardID + ".",
        game_context:{ hazard:h.HazardID, window:h.WindowTurns, telegraph_turn:t },
        repro:"wait " + (t+1) + " times, then break",
        gdd_reference:"the row's own EscapeCondition" });
    G.startHazard(i);
    const b2 = G.S.totalFails;
    G.hz("go");
    if (G.S.totalFails === b2)
      report({ location:"Acts 1-2 / " + h.HazardID + " (hz)", error_type:"unloseable_encounter",
        severity:"high",
        summary:"Breaking on turn zero, before any tell, still escaped " + h.HazardID + ".",
        game_context:{ hazard:h.HazardID, window:h.WindowTurns, telegraph_turn:t },
        repro:"break immediately" });
    checks += 2;
  }
})();

// --- 9. can a fight be won without the journey mattering? ---------------
// This used to play a scripted line, seven right and four down. That line
// only ever worked because the dog could walk through the robot; once the
// pieces became solid it started losing, and the check went quiet while
// still reporting itself as passed. A scripted line is a fossil. The line
// is searched now, so the check measures the handoff and not a fixture.
(function journeyWeight(){
  const runs = [0,3].map(f => { fresh(f, f>0);
    const line = [];
    while (!G.S.over && line.length < 40){ const d = G.autoPlan().dir; line.push(d); G.mv(d); }
    return { fails:f, won:G.approach()>=1, stamina:G.S.stamina, rounds:G.S.round };
  });
  if (!runs.every(r => r.won))
    report({ location:"Acts 1-2 to Act 3 handoff (beginFight)", error_type:"unwinnable_fight",
      severity:"critical",
      summary:"A searched optimal line did not reach the kid from the opening position after " +
              runs.filter(r=>!r.won).map(r=>r.fails).join(" and ") + " failed encounters.",
      game_context:{ runs }, repro:"play the line autoPlan() returns, from the gate" });
  if (runs.every(r=>r.won) && runs[0].stamina === runs[1].stamina)
    report({ location:"Acts 1-2 to Act 3 handoff (beginFight)", error_type:"dead_mechanic",
      severity:"medium",
      summary:"A clean journey and a failed one produce identical Act 3 state, so nothing in Acts 1 and 2 affects the fight.",
      game_context:{ runs }, repro:"play the optimal line after 0 fails and after 3" });
  checks++;
})();

// --- 10. the closed exploits, at every difficulty -----------------------
// Difficulty is not cosmetic: it changes the robot's memory window (3, 4 or
// 6 moves), the round limit (18, 15, 13), what pursuit costs it and the
// stamina the dog starts with. Every exploit above was re-attempted at the
// middle setting only, so two of the three shipped configurations had never
// been attacked at all.
(function difficultyParity(){
  const cycle = ["right","right","down","left","up"];              // five beats
  const leash = ["right","right","up","up","left","left","down","down"];
  for (const level of Object.keys(G.DIFFS)){
    G.setDiff(level);
    const cfg = G.getCfg();

    fresh();                                                        // no fail state
    for (let i = 0; i < cfg.maxRounds + 25 && !G.S.over; i++) G.mv("wait");
    if (!G.S.over || G.approach() >= 1)
      report({ location:"Act 3 / round loop (checkEnd), difficulty " + level,
        error_type:"no_fail_state", severity:"critical",
        summary:"Standing still for the whole fight did not end it as a loss on " + level + ".",
        game_context:Object.assign(snapshot(), { difficulty:level, cfg }),
        repro:"set difficulty to " + level + ", then wait " + (cfg.maxRounds + 25) + " times",
        gdd_reference:"GDD 3 exploit 3, no fail state" });
    checks++;

    fresh();                                                        // window aliasing
    for (let i = 0; i < cfg.maxRounds && !G.S.over; i++) G.mv(cycle[i % 5]);
    if (!G.S.spoken.length)
      report({ location:"Act 3 / Nemesis perception (firingCategories), difficulty " + level,
        error_type:"exploit_reintroduced", severity:"high",
        summary:"A five-beat cycle drew no read across a full fight on " + level +
                ", where the robot remembers " + cfg.window + " moves.",
        game_context:Object.assign(snapshot(), { difficulty:level, window:cfg.window }),
        repro:"set difficulty to " + level + ", then " + cycle.join(", ") + " on a loop",
        gdd_reference:"GDD 3 exploit 5, window aliasing" });
    checks++;

    fresh();                                                        // the leash
    let worst = 0;
    for (let i = 0; i < cfg.maxRounds && !G.S.over; i++){
      const before = G.man(G.S.rex, G.S.dog);
      G.mv(leash[i % leash.length]);
      worst = Math.max(worst, G.man(G.S.rex, G.S.dog) - before);
    }
    if (worst > 1)
      report({ location:"Act 3 / Nemesis intercept (rexAct), difficulty " + level,
        error_type:"exploit_reintroduced", severity:"critical",
        summary:"The robot ended a round " + worst + " tiles further from the dog than it began, on " +
                level + ". The engine-side veto did not hold.",
        game_context:Object.assign(snapshot(), { difficulty:level }),
        repro:"set difficulty to " + level + ", then " + leash.join(", ") + " on a loop",
        gdd_reference:"GDD 6.1, reject any intercept_move that increases true distance" });
    checks++;
  }
  G.setDiff("moderate");
})();

// --- 11. the pieces are solid -------------------------------------------
// The dog used to be able to walk through the robot, which made a straight
// run at the kid the best line and the interception decorative. Pieces are
// solid now, which creates a second way for a move to be refused. RM-003
// was exactly that failure on the first way: a refusal that changed nothing
// and said nothing looks like a frozen game.
(function solidPieces(){
  let overlaps = null;
  for (let r = 0; r < 80 && !overlaps; r++){
    freshRandom(Math.floor(rnd()*4), rnd() < 0.5);
    for (let s = 0; s < 60 && !G.S.over; s++){
      G.mv(pick(DIRS));
      if (G.eq(G.S.dog, G.S.rex)) { overlaps = snapshot(); break; }
    }
    checks++;
  }
  if (overlaps)
    report({ location:"Act 3 / movement (mv, stepToward)", error_type:"state_violation",
      severity:"critical",
      summary:"The dog and the robot ended a round on the same tile. Neither is allowed to occupy the other.",
      game_context:overlaps, repro:"random legal inputs from a random spawn" });

  // walk into the robot on purpose
  fresh();
  G.S.dog = [4,4]; G.S.rex = [5,4]; G.S.kid = [9,9]; G.S.distMax = 10;
  const b = { round:G.S.round, stam:G.S.stamina, dog:G.S.dog.slice(), rex:G.S.rex.slice(), log:G.S.log.length };
  G.mv("right");
  const noop = G.S.round === b.round && G.S.stamina === b.stam
            && G.eq(G.S.dog, b.dog) && G.eq(G.S.rex, b.rex);
  if (!noop)
    report({ location:"Act 3 / movement (mv)", error_type:"free_action", severity:"medium",
      summary:"Stepping into the robot was refused but still moved the game on: the round, the stamina or the robot changed.",
      game_context:snapshot(), repro:"stand west of the robot and press east" });
  else if (G.S.log.length === b.log)
    report({ location:"Act 3 / movement (mv)", error_type:"soft_lock_risk", severity:"low",
      summary:"Stepping into the robot is a silent no-op. This is RM-003 on the second refusal path: a player holding the key sees a frozen game and is told nothing.",
      game_context:snapshot(), repro:"stand west of the robot and hold east",
      gdd_reference:"RM-003, the fence message" });
  checks += 2;
})();

// --- 12. is a random spawn always winnable? -----------------------------
// The shipped build places the three pieces at random and then rolls again
// until its own search can prove a win exists. That promise is the whole
// fairness argument for random spawns, and it is best-effort: the roller
// gives up after a fixed number of tries and starts the fight anyway.
(function spawnFairness(){
  const SPAWNS = Number(process.env.RM_SPAWNS || 40);
  const table = [];
  for (const level of Object.keys(G.DIFFS)){
    G.setDiff(level);
    for (const fails of [0, 3]){
      let unwinnable = 0, rawOk = 0, sample = null;
      for (let i = 0; i < SPAWNS; i++){
        // what a raw placement would have given, with no fairness roll at all
        fresh(fails, fails > 0);
        G.placePieces();
        G.S.moves = []; G.S.round = 0; G.S.charge = 100; G.S.predicted = null;
        if (G.searchLine()) rawOk++;
        // and what the shipped path gives
        freshRandom(fails, fails > 0);
        if (!G.searchLine()){ unwinnable++; sample = sample || snapshot(); }
        checks += 2;
      }
      table.push({ difficulty:level, failed_encounters:fails,
                   raw_spawn_winnable: rawOk + "/" + SPAWNS,
                   after_fairness_roll: (SPAWNS - unwinnable) + "/" + SPAWNS });
      if (unwinnable)
        report({ location:"Act 3 / spawn placement (placePieces, ensureWinnable)",
          error_type:"unwinnable_start", severity:"critical",
          summary:unwinnable + " of " + SPAWNS + " random spawns on " + level + " after " + fails +
                  " failed encounters began a fight with no line to the kid at the stamina the player had.",
          game_context:Object.assign(sample, { difficulty:level, fails }),
          repro:"start the fight repeatedly on " + level + " and search for a winning line at round 0",
          gdd_reference:"the fairness promise ensureWinnable() makes" });
    }
  }
  G.setDiff("moderate");
  measurements.spawn_fairness = { sampled_per_row: SPAWNS, rows: table,
    note: "ensureWinnable() rerolls a random board until its own search proves a win exists. The left column is what the player would have got without it." };
})();

// --- 13. the computer's own line, as an oracle --------------------------
// Watch the computer searches the robot's decision model for the shortest
// line to the kid and commits to it. Two things have to hold or the feature
// is a lie: every move it commits to must be legal against the live rules,
// and the board it predicted must be the board that arrives.
(function plannerHonesty(){
  const RUNS = Number(process.env.RM_PLANS || 12);
  for (const level of Object.keys(G.DIFFS)){
    G.setDiff(level);
    let lost = 0, refused = 0, diverged = 0, sample = null;
    for (let i = 0; i < RUNS; i++){
      freshRandom(i % 4, i % 2 === 0);
      let steps = 0;
      while (!G.S.over && steps < 40){
        const plan = G.autoPlan();
        const round = G.S.round;
        G.mv(plan.dir); steps++;
        if (G.S.round === round){ refused++; sample = sample || snapshot(); }
      }
      if (G.approach() < 1){ lost++; sample = sample || snapshot(); }
      checks += 2;
    }
    if (refused)
      report({ location:"Act 3 / planner (autoPlan, simMove)", error_type:"model_divergence",
        severity:"high",
        summary:"The computer committed to " + refused + " moves the live rules refused, on " + level +
                ". Its model of the board and the board disagree.",
        game_context:Object.assign(sample || {}, { difficulty:level }),
        repro:"press Watch the computer on " + level + " and follow the moves it plays" });
    if (lost)
      report({ location:"Act 3 / planner (autoPlan)", error_type:"feature_does_not_hold",
        severity:"high",
        summary:"Watch the computer lost " + lost + " of " + RUNS + " fights on " + level +
                ". It offers itself to a player who cannot win, so losing is the one thing it must not do.",
        game_context:Object.assign(sample || {}, { difficulty:level }),
        repro:"press Watch the computer on " + level + " from a random spawn" });
  }
  G.setDiff("moderate");
})();

// --- 14. does the ledger tell the truth? --------------------------------
// Every move the player makes is graded in a panel beside the board. The
// grade is an assertion about the position, so it can be wrong, and a wrong
// grade is worse than no grade: it teaches the player the opposite lesson.
(function ledgerTruth(){
  // The judge is gated on the random-spawn flag as well as its own, because
  // that flag is what tells the game it is in front of a player. Both have to
  // stay on for the whole section or the ledger simply never runs.
  const wasJudge = G.S.judge, wasRandom = G.S.randomSpawn;
  G.S.judge = true; G.S.randomSpawn = true;
  let missing = 0, falseDanger = 0, wrongExcellent = 0, sample = null;
  for (let r = 0; r < 25; r++){
    fresh(Math.floor(rnd()*4), rnd() < 0.5);
    let n = 0;
    while (!G.S.over && n < 30){
      const predicted = G.S.predicted ? G.S.predicted.slice() : null;
      const dirs = legalDirs(), dir = pick(dirs);
      const entries = G.S.ledger.length;
      const round = G.S.round;
      G.mv(dir);
      if (G.S.round === round) continue;                 // refused, nothing to grade
      n++;
      if (G.S.ledger.length !== entries + 1){ missing++; sample = sample || snapshot(); continue; }
      const e = G.S.ledger[G.S.ledger.length - 1];
      if (e.rating === "danger" && G.searchLine()){ falseDanger++; sample = sample || snapshot(); }
      if (e.rating === "excellent" && predicted && G.eq(G.S.dog, predicted)){
        wrongExcellent++; sample = sample || snapshot();
      }
      checks += 3;
    }
  }
  G.S.judge = wasJudge; G.S.randomSpawn = wasRandom;
  if (missing)
    report({ location:"Act 3 / ledger (rateMove)", error_type:"missing_feedback", severity:"medium",
      summary:missing + " moves that cost a round produced no ledger entry, so the record the player reads is not the record of what they did.",
      game_context:sample || {}, repro:"random legal inputs with the ledger judge on" });
  if (falseDanger)
    report({ location:"Act 3 / ledger (rateMove)", error_type:"false_grade", severity:"high",
      summary:falseDanger + " moves were graded danger, meaning the last line to the kid was closed, while a winning line still existed.",
      game_context:sample || {}, repro:"random legal inputs with the ledger judge on" });
  if (wrongExcellent)
    report({ location:"Act 3 / ledger (rateMove)", error_type:"false_grade", severity:"medium",
      summary:wrongExcellent + " moves onto the tile the robot had predicted were graded excellent. Excellent is defined as off its guess.",
      game_context:sample || {}, repro:"step onto the marked tile and read the grade" });
})();

// --- 15. an independent oracle over the game's own search ---------------
// Everything the ledger says about a dead run, and the whole fairness
// promise behind random spawns, rests on one bounded depth-first search
// inside the game. A bounded search has two ways to return nothing: the
// position is lost, or the search gave up. Those are the same answer to the
// player and opposite answers to a designer. So this does not ask the game.
// It replays one move from the exported primitives and runs its own much
// larger breadth-first search, then compares verdicts.
(function oracle(){
  const CASES = Number(process.env.RM_ORACLE || 10);
  const DIRS4 = ["left","right","up","down","wait"];
  const grab = () => ({ dog:G.S.dog.slice(), rex:G.S.rex.slice(), moves:G.S.moves.slice(),
                        round:G.S.round, stamina:G.S.stamina, charge:G.S.charge,
                        predicted:G.S.predicted ? G.S.predicted.slice() : null });
  const put = st => { G.S.dog=st.dog.slice(); G.S.rex=st.rex.slice(); G.S.moves=st.moves.slice();
                      G.S.round=st.round; G.S.stamina=st.stamina; G.S.charge=st.charge;
                      G.S.predicted=st.predicted ? st.predicted.slice() : null; };
  // one move, exactly as mv() applies it, minus the words
  function step(st, dir){
    put(st);
    if (dir !== "wait"){
      const t = [G.S.dog[0]+G.STEP[dir][0], G.S.dog[1]+G.STEP[dir][1]];
      if (!G.inBounds(t) || G.eq(t, G.S.rex)) return null;
      G.S.dog = t;
    }
    G.S.moves.push(dir); G.S.round++;
    G.rexAct();
    G.S.stamina = Math.max(0, G.S.stamina - 1 - (G.man(G.S.rex, G.S.dog) <= 1 ? 1 : 0));
    return grab();
  }
  function search(start, maxRounds, budget){
    const seen = new Set(), kid = G.S.kid;
    let frontier = [start], depth = 0, nodes = 0;
    const cap = Math.min(maxRounds - start.round, start.stamina);
    while (frontier.length && depth <= cap){
      const next = [];
      for (const st of frontier){
        if (st.stamina <= 0 || st.round >= maxRounds) continue;
        if (G.man(st.dog, kid) > Math.min(st.stamina, maxRounds - st.round)) continue;
        for (const d of DIRS4){
          const ns = step(st, d);
          if (!ns) continue;
          if (++nodes > budget) return { win:false, exhausted:true, nodes };
          if (G.eq(ns.dog, kid)) return { win:true, depth:depth+1, nodes };
          const k = ns.dog + "|" + ns.rex + "|" + ns.round + "|" + ns.stamina + "|" + ns.moves.slice(-6).join(",");
          if (seen.has(k)) continue;
          seen.add(k);
          next.push(ns);
        }
      }
      frontier = next; depth++;
    }
    return { win:false, exhausted:false, nodes };
  }

  // Collect positions where the game says the run is dead while the dog still
  // looks comfortable: distance to the kid well inside both stamina and rounds.
  // A search that gives up will hide here.
  const suspects = [];
  for (const level of Object.keys(G.DIFFS)){
    G.setDiff(level);
    const maxRounds = G.getCfg().maxRounds;
    for (let r = 0; r < 20 && suspects.length < CASES; r++){
      freshRandom(Math.floor(rnd()*4), rnd() < 0.5);
      while (!G.S.over && suspects.length < CASES){
        const before = G.S.round;
        G.mv(pick(legalDirs()));
        if (G.S.round === before || G.S.over) { if (G.S.over) break; else continue; }
        if (G.searchLine()) continue;
        const slack = Math.min(G.S.stamina, maxRounds - G.S.round) - G.man(G.S.dog, G.S.kid);
        if (slack >= 4) suspects.push({ level, maxRounds, slack, state: grab(),
                                        kid: G.S.kid.slice(), distMax: G.S.distMax });
      }
    }
  }

  let disagreed = 0, gaveUp = 0, sample = null;
  for (const sp of suspects){
    G.setDiff(sp.level);
    G.S.kid = sp.kid.slice(); G.S.distMax = sp.distMax;
    const verdict = search(sp.state, sp.maxRounds, 400000);
    put(sp.state);
    if (verdict.win){ disagreed++; sample = sample || Object.assign(snapshot(), { oracle_depth: verdict.depth, slack: sp.slack }); }
    else if (verdict.exhausted) gaveUp++;
    checks++;
  }
  G.setDiff("moderate");

  if (disagreed)
    report({ location:"Act 3 / search (searchLine), ledger and spawn fairness both read it",
      error_type:"false_negative_search", severity:"high",
      summary:"An independent search found a winning line in " + disagreed + " of " + suspects.length +
              " positions the game had already written off. The ledger grades those moves danger and tells the player they killed their own run.",
      game_context:sample, repro:"reach a position where the ledger says danger while stamina and rounds still exceed the distance to the kid" });
  measurements.oracle_cross_check = {
    suspect_positions: suspects.length, oracle_disagreed: disagreed,
    oracle_budget_exhausted: gaveUp,
    note: "positions the game called dead while the dog still had four or more rounds and stamina in hand, re-searched independently"
  };
})();

const out = {
  game: "Rex Machina", target: "game.js, the capstone build served at index.html",
  agent: "qa/adversary.js", run_at: new Date().toISOString(),
  strategy: ["GDD 3 exploit 4 approach ratchet", "GDD 3 exploit 2 the leash",
             "GDD 3 exploit 5 window aliasing", "GDD 3 exploit 3 no fail state",
             "read line versus measured observable", "randomised invariant fuzz",
             "boundary probing", "per-encounter winnability and loseability",
             "journey to fight handoff", "closed exploits at every difficulty",
             "solid pieces and the second refusal path", "random spawn fairness",
             "the planner as its own oracle", "ledger grades versus the search",
             "independent oracle over the game's own search"],
  checks_run: checks, findings_count: findings.length, findings, measurements
};
fs.writeFileSync(path.join(__dirname, "report.json"), JSON.stringify(out, null, 1));
console.log("%d checks, %d findings\n", checks, findings.length);
for (const f of findings)
  console.log("  [" + f.severity.toUpperCase() + "] " + f.error_type +
              "\n      " + f.location + "\n      " + f.summary + "\n");
console.log("wrote qa/report.json");
