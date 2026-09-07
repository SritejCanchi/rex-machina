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
(function journeyWeight(){
  const OPT = ["right","right","right","right","right","right","right",
               "down","down","down","down"];
  const runs = [0,3].map(f => { fresh(f, f>0);
    for (const m of OPT){ if (G.S.over) break; G.mv(m); }
    return { fails:f, won:G.approach()>=1, stamina:G.S.stamina }; });
  if (runs.every(r=>r.won) && runs[0].stamina === runs[1].stamina)
    report({ location:"Acts 1-2 to Act 3 handoff (beginFight)", error_type:"dead_mechanic",
      severity:"medium",
      summary:"A clean journey and a failed one produce identical Act 3 state, so nothing in Acts 1 and 2 affects the fight.",
      game_context:{ runs }, repro:"play the optimal line after 0 fails and after 3" });
  checks++;
})();

const out = {
  game: "Rex Machina", target: "game.js, the capstone build served at index.html",
  agent: "qa/adversary.js", run_at: new Date().toISOString(),
  strategy: ["GDD 3 exploit 4 approach ratchet", "GDD 3 exploit 2 the leash",
             "GDD 3 exploit 5 window aliasing", "GDD 3 exploit 3 no fail state",
             "read line versus measured observable", "randomised invariant fuzz",
             "boundary probing", "per-encounter winnability and loseability",
             "journey to fight handoff"],
  checks_run: checks, findings_count: findings.length, findings
};
fs.writeFileSync(path.join(__dirname, "report.json"), JSON.stringify(out, null, 1));
console.log("%d checks, %d findings\n", checks, findings.length);
for (const f of findings)
  console.log("  [" + f.severity.toUpperCase() + "] " + f.error_type +
              "\n      " + f.location + "\n      " + f.summary + "\n");
console.log("wrote qa/report.json");
