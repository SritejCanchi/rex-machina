// What Rex says: triggers, the RM-001 rule, suppression, and the reads table.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { G, fight, readTable } = require("./_load");

// Put the dog somewhere that fires no position trigger (no cover, no exit near).
function quietSpot() { G.S.dog = [5, 0]; G.S.rex = [5, 9]; }

test("RM-001: a line naming 'left' is held back when the player favours right", () => {
  fight(); quietSpot();
  G.S.moves = Array(10).fill("right");
  G.S.lastCat = "periodicity_called";          // so the next live trigger is sealing_direction
  G.S.spoken = []; G.S.charge = 100;
  assert.ok(G.firingCategories().includes("sealing_direction"));
  G.speakRead();
  assert.equal(G.S.spoken.length, 0, "Rex must stay silent rather than say a false line");
});

test("RM-001: the same line is spoken when the player really favours left", () => {
  fight(); quietSpot();
  G.S.moves = Array(10).fill("left");
  G.S.lastCat = "periodicity_called";
  G.S.spoken = []; G.S.charge = 100;
  G.speakRead();
  assert.equal(G.S.spoken.length, 1);
  assert.match(G.S.spoken[0], /\bleft\b/i);
});

test("six moves right from the start never produce a line naming another direction", () => {
  fight();
  for (let i = 0; i < 6; i++) G.mv("right");
  const dom = G.dominantDir();
  for (const line of G.S.spoken)
    for (const d of G.namesDirection(line)) assert.equal(d, dom, "false read: " + line);
});

test("suppression: the category spoken last round is skipped this round", () => {
  fight(); quietSpot();
  G.S.moves = ["up", "right", "up", "right", "up", "right"];
  G.S.spoken = []; G.S.charge = 100; G.S.lastCat = null;
  G.speakRead();
  assert.equal(G.S.lastCat, "periodicity_called");
  const periodicLines = new Set(readTable("DT_NemesisReads")
    .filter(r => r.ReadCategory === "periodicity_called").map(r => r.Line));
  const first = G.S.spoken.length;
  G.speakRead();
  // Still periodic, but suppressed. The only other live trigger here names
  // "left", so RM-001 holds it too: the right answer is silence.
  for (const line of G.S.spoken.slice(first))
    assert.ok(!periodicLines.has(line), "the same category twice in a row: " + line);
});

test("a line is never spoken twice in one fight", () => {
  fight(); quietSpot();
  G.S.moves = ["up", "right", "up", "right", "up", "right"];
  G.S.spoken = []; G.S.charge = 100;
  for (let i = 0; i < 6; i++) { G.S.lastCat = null; G.speakRead(); }
  assert.equal(new Set(G.S.spoken).size, G.S.spoken.length);
});

test("the reads table has one line for every category in every charge band", () => {
  const rows = readTable("DT_NemesisReads");
  const keys = rows.map(r => r.ReadCategory + "/" + r.ChargeBand);
  assert.equal(rows.length, 24);
  assert.equal(new Set(keys).size, 24, "duplicate category and band");
  for (const r of rows) {
    assert.ok(r.Line && r.Line.trim(), r.ReadID + " has no line");
    assert.equal(r.WordCount, r.Line.trim().split(/\s+/).length, r.ReadID + " word count");
  }
});

test("RM-13: 'same exit' lines must not claim two approaches when the trigger fires on one",
     { todo: "open bug RM-13, found by the Unity AI evaluation" }, () => {
  // Two steps down from the start put the dog within two tiles of the exit at
  // [0,4] for the first time, and the exit line is what Rex says.
  fight();
  G.mv("down"); G.mv("down");
  const said = G.S.spoken.join(" ");
  assert.doesNotMatch(said, /consecutive|twice/i, "claimed a repeat after one approach");
});
