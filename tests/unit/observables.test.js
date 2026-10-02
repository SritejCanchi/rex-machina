// What Rex measures about the player's moves: direction frequency, periodicity,
// the dominant direction and the one-step prediction.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { G, fight } = require("./_load");

test("direction frequency ignores waits and covers only the last 20 moves", () => {
  fight();
  G.S.moves = ["left", "left", "right", "wait"];
  const f = G.dirFreq();
  assert.equal(f.left, 2 / 3);
  assert.equal(f.right, 1 / 3);
  assert.equal(f.up + f.down, 0);

  G.S.moves = Array(5).fill("up").concat(Array(20).fill("down"));
  assert.equal(G.dirFreq().up, 0, "moves older than 20 drop out");
});

test("direction frequency is all zero before any directional move", () => {
  fight();
  G.S.moves = ["wait", "wait"];
  assert.deepEqual(G.dirFreq(), { left: 0, right: 0, up: 0, down: 0 });
  assert.equal(G.dominantDir(), null);
});

test("periodicity needs four moves and catches repeating patterns", () => {
  fight();
  G.S.moves = ["up", "right", "up"];
  assert.equal(G.periodicity(), 0, "fewer than four moves never reads as a pattern");
  G.S.moves = ["up", "right", "up", "right", "up", "right"];
  assert.equal(G.periodicity(), 1);
});

test("a five-beat cycle is still caught (GDD 3, exploit 5: window aliasing)", () => {
  fight();
  const cycle = ["up", "right", "down", "left", "wait"];
  G.S.moves = cycle.concat(cycle);
  assert.equal(G.periodicity(), 1, "the four-move window cannot see it, the lag-5 check must");
});

test("dominant direction breaks ties in compass order", () => {
  fight();
  G.S.moves = ["right", "left"];
  assert.equal(G.dominantDir(), "left");
  G.S.moves = ["right", "right", "left"];
  assert.equal(G.dominantDir(), "right");
});

test("the prediction is the dog's tile plus its most frequent recent step", () => {
  fight();
  G.S.dog = [4, 4];
  G.S.moves = [];
  assert.deepEqual(G.predict(), [4, 4], "no history: predict the dog stays");
  G.S.moves = ["left", "right", "right", "up"];
  assert.deepEqual(G.predict(), [5, 4]);
  G.S.moves = ["down", "up"];
  assert.deepEqual(G.predict(), [4, 5], "a tie goes to the step seen first in the window");
});

test("namesDirection matches whole words only", () => {
  assert.deepEqual(G.namesDirection("Target favored left nine of twenty recorded moves."), ["left"]);
  assert.deepEqual(G.namesDirection("Leftover energy, upright posture."), []);
  assert.deepEqual(G.namesDirection("Right, then down."), ["right", "down"]);
});
