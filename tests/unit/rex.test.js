// Rex's move: step toward the predicted tile, never onto the dog, never off the
// board, and never a step that loses ground on the dog (the GDD 6.1 veto).
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { G, fight } = require("./_load");

// Seeded generator so the property tests are the same on every run.
function rng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6D2B79F5) >>> 0;
    let t = Math.imul(s ^ (s >>> 15), s | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const DIRS = ["up", "down", "left", "right", "wait"];

test("stepToward stays on the board and never steps onto the dog", () => {
  fight();
  const r = rng(1);
  for (let i = 0; i < 2000; i++) {
    G.S.dog = [Math.floor(r() * 10), Math.floor(r() * 10)];
    const from = [Math.floor(r() * 10), Math.floor(r() * 10)];
    const target = [Math.floor(r() * 12) - 1, Math.floor(r() * 12) - 1];
    const to = G.stepToward(from, target);
    assert.ok(G.inBounds(to), "off the board: " + JSON.stringify({ from, target, to }));
    assert.ok(!G.eq(to, G.S.dog) || G.eq(to, from), "onto the dog: " + JSON.stringify({ from, to }));
    assert.ok(G.man(from, to) <= 1, "moved more than one tile");
  }
});

test("the veto: Rex never ends its move further from the dog than it started", () => {
  fight();
  const r = rng(2);
  for (let i = 0; i < 2000; i++) {
    G.S.dog = [Math.floor(r() * 10), Math.floor(r() * 10)];
    do { G.S.rex = [Math.floor(r() * 10), Math.floor(r() * 10)]; } while (G.eq(G.S.rex, G.S.dog));
    G.S.moves = Array.from({ length: 6 }, () => DIRS[Math.floor(r() * 5)]);
    G.S.charge = 100;
    const before = G.man(G.S.rex, G.S.dog);
    G.rexAct();
    assert.ok(G.man(G.S.rex, G.S.dog) <= before,
      "lost ground: " + JSON.stringify({ dog: G.S.dog, rex: G.S.rex, moves: G.S.moves }));
  }
});

test("charge: a move costs pursuit minus solar, holding gains, both clamped 0 to 100", () => {
  const cfg = G.getCfg();
  fight();
  G.S.dog = [0, 0]; G.S.rex = [5, 5]; G.S.moves = ["right"]; G.S.charge = 50;
  G.rexAct();
  assert.equal(G.S.charge, 50 - cfg.pursuit + 2, "moved: pursuit cost, plus solar");

  G.S.dog = [0, 0]; G.S.rex = [0, 1]; G.S.moves = []; G.S.charge = 100;
  G.rexAct();
  assert.equal(G.S.charge, 100, "holding next to the dog: +1 net, capped at 100");

  G.S.dog = [0, 0]; G.S.rex = [5, 5]; G.S.moves = ["right"]; G.S.charge = 1;
  G.rexAct();
  assert.equal(G.S.charge, 0, "never below zero");
});

test("charge bands: clinical above 60, confident 30 to 60, strained below 30", () => {
  fight();
  for (const [c, b] of [[100, "clinical"], [61, "clinical"], [60, "confident"],
                        [30, "confident"], [29, "strained"], [0, "strained"]]) {
    G.S.charge = c;
    assert.equal(G.band(), b, "charge " + c);
  }
});
