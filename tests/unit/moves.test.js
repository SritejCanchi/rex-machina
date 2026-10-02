// The player's move: refused moves, solid pieces and the stamina floor.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { G, fight } = require("./_load");

function snapshot() {
  const S = G.S;
  return { round: S.round, moves: S.moves.length, dog: S.dog.slice(), rex: S.rex.slice(),
           stamina: S.stamina, charge: S.charge };
}

test("a step into the fence is refused: no turn, no cost, but something is said (RM-003)", () => {
  fight();                                     // dog starts in the corner at [0,0]
  for (const dir of ["left", "up"]) {
    const before = snapshot(), logAt = G.S.log.length;
    G.mv(dir);
    assert.deepEqual(snapshot(), before, dir + " into the fence changed state");
    assert.ok(G.S.log.length > logAt, dir + " into the fence said nothing");
  }
});

test("pieces are solid: a step onto Rex's tile is refused the same way", () => {
  fight();
  G.S.dog = [3, 3]; G.S.rex = [4, 3];
  const before = snapshot(), logAt = G.S.log.length;
  G.mv("right");
  assert.deepEqual(snapshot(), before);
  assert.ok(G.S.log.length > logAt);
});

test("a legal move counts as one round and Rex answers it", () => {
  fight();
  const before = snapshot();
  G.mv("right");
  assert.equal(G.S.round, before.round + 1);
  assert.equal(G.S.moves.length, before.moves + 1);
  assert.deepEqual(G.S.dog, [1, 0]);
  assert.ok(G.S.predicted, "Rex marks a predicted tile");
});

test("RM-002: stamina never drops below zero, even with the adjacency drain", () => {
  fight();
  G.S.dog = [4, 4]; G.S.rex = [5, 4]; G.S.stamina = 1;
  G.mv("wait");
  assert.equal(G.S.stamina, 0);
});

test("each round costs one stamina, two when Rex ends next to the dog", () => {
  fight();
  G.S.dog = [0, 0]; G.S.rex = [9, 9]; G.S.stamina = 10;
  G.mv("right");
  assert.equal(G.S.stamina, 9, "far from Rex");
  fight();
  G.S.dog = [4, 4]; G.S.rex = [5, 4]; G.S.stamina = 10;
  G.mv("wait");
  assert.equal(G.S.stamina, 8, "Rex adjacent after its move");
});
