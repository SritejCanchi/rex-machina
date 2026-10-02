// Loads the shipped game.js headless with the real tables, for node:test.
// Each test file runs in its own process, so the game's module state is fresh
// per file. Call fight() at the start of every test that touches state.
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..", "..");

const G = require(path.join(ROOT, "game.js"));
G.setSinks(() => ({ innerHTML: "", children: [], appendChild(){}, removeChild(){},
                    get firstChild(){ return null; } }));

const TABLES = ["DT_JourneyHazards", "DT_ArenaPhases", "DT_NemesisReads",
                "DT_RetryReads", "DT_JourneyBeats", "MANIFEST"];
const readTable = n => JSON.parse(fs.readFileSync(path.join(ROOT, "data", n + ".json"), "utf8"));
for (const n of TABLES) G.DT[n] = readTable(n);
G.DT.hazards = G.DT.DT_JourneyHazards.slice().sort((a, b) => a.Day - b.Day);
G.DT.phases  = G.DT.DT_ArenaPhases.slice().sort((a, b) => a.PhaseIndex - b.PhaseIndex);

// The canonical opening the headless tests use: dog [0,0], Rex [5,5], kid [7,4],
// yard phase, moderate difficulty, a clean journey.
function fight({ diff = "moderate", fails = 0, limping = false } = {}) {
  G.setDiff(diff);
  G.S.totalFails = fails; G.S.limping = limping; G.S.priorAttempt = null;
  G.S.randomSpawn = false;
  G.beginFight();
  return G.S;
}

// What Rex said since a mark in the log, as plain text.
const rexLines = (from = 0) => G.S.log.slice(from).filter(l => l.startsWith("REX:"));

module.exports = { G, ROOT, fight, readTable, rexLines };
