// Replays fixed move sequences through the shipped browser game (game.js) and
// writes a per-turn trace. unity/parity/ParityCheck.cs replays the same
// sequences through the Unity C# port, and compare.py diffs the two.
//
//   node unity/parity/js_trace.js > unity/parity/js_trace.json
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const G = require(path.join(ROOT, "game.js"));
G.setSinks(() => ({ innerHTML:"", children:[], appendChild(){}, removeChild(){},
                    get firstChild(){ return null; } }));
for (const n of ["DT_JourneyHazards","DT_ArenaPhases","DT_NemesisReads",
                 "DT_RetryReads","DT_JourneyBeats","MANIFEST"])
  G.DT[n] = JSON.parse(fs.readFileSync(path.join(ROOT,"data",n+".json"),"utf8"));
G.DT.hazards = G.DT.DT_JourneyHazards.slice().sort((a,b)=>a.Day-b.Day);
G.DT.phases  = G.DT.DT_ArenaPhases.slice().sort((a,b)=>a.PhaseIndex-b.PhaseIndex);
// Pin the yard phase: the C# port has one arena, so the gate to phase 2 is out of scope.
G.DT.phases = G.DT.phases.slice(0, 1);

const SEQS = JSON.parse(fs.readFileSync(path.join(__dirname, "sequences.json"), "utf8"));
const out = {};
for (const [name, moves] of Object.entries(SEQS)) {
  G.S.totalFails = 0; G.S.limping = false; G.S.priorAttempt = null; G.S.randomSpawn = false;
  G.beginFight();
  const turns = [];
  for (const m of moves) {
    if (G.S.over) break;
    const roundBefore = G.S.round, spokenBefore = G.S.spoken.length;
    G.mv(m);
    turns.push({
      move: m,
      counted: G.S.round !== roundBefore,            // false = the game refused the move
      dog: G.S.dog.slice(), rex: G.S.rex.slice(),
      predicted: G.S.predicted ? G.S.predicted.slice() : null,
      charge: G.S.charge, band: G.band(), stamina: G.S.stamina,
      line: G.S.spoken.length > spokenBefore ? G.S.spoken[G.S.spoken.length - 1] : null,
    });
  }
  out[name] = turns;
}
process.stdout.write(JSON.stringify(out, null, 1));
