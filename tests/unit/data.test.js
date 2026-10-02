// The five tables every build reads: present, unmodified since the pipelines
// wrote them, and shaped the way the game expects.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("crypto"), fs = require("fs"), path = require("path");
const { ROOT, readTable } = require("./_load");

// Same rule as tools/sync_datatables.py: hash with line endings normalised to LF.
const sha = file => crypto.createHash("sha256")
  .update(fs.readFileSync(file).toString("binary").replace(/\r\n/g, "\n"), "binary").digest("hex");

test("every table matches its MANIFEST hash and row count", () => {
  const manifest = readTable("MANIFEST");
  assert.equal(manifest.length, 5);
  for (const m of manifest) {
    const file = path.join(ROOT, "data", m.file);
    assert.equal(sha(file), m.sha256, m.file + " changed since the pipeline wrote it");
    assert.equal(readTable(m.file.replace(".json", "")).length, m.rows, m.file + " row count");
  }
  assert.equal(manifest.reduce((n, m) => n + m.rows, 0), 42);
});

test("arena phases: three, in order, with exits and cover inside the grid", () => {
  const phases = readTable("DT_ArenaPhases").sort((a, b) => a.PhaseIndex - b.PhaseIndex);
  assert.deepEqual(phases.map(p => p.PhaseIndex), [1, 2, 3]);
  for (const p of phases) {
    const [w, h] = p.GridSpan.toLowerCase().split("x").map(Number);
    for (const t of [...(p.ExitTiles || []), ...(p.CoverTiles || [])])
      assert.ok(t[0] >= 0 && t[0] < w && t[1] >= 0 && t[1] < h, p.PhaseID + " tile off the grid " + t);
  }
});

test("journey hazards: six, one per day order, each with a tell and an escape", () => {
  const h = readTable("DT_JourneyHazards");
  assert.equal(h.length, 6);
  assert.equal(new Set(h.map(x => x.HazardID)).size, 6);
  for (const x of h) {
    assert.ok(x.Telegraph && x.EscapeCondition, x.HazardID);
    assert.ok(Number.isInteger(x.WindowTurns) && x.WindowTurns > 0, x.HazardID + " window");
  }
});

test("retry lines and journey beats keep to their word budgets", () => {
  // Counted the way the A6 pipeline counts (ger/rules.py words()): letter runs,
  // so "Right-up" is two words.
  const words = line => (line.match(/[A-Za-z']+/g) || []).length;
  for (const r of readTable("DT_RetryReads")) {
    assert.equal(r.WordCount, words(r.Line), r.RowName);
    assert.ok(r.WordCount <= 12, r.RowName + " over the 12-word budget");
  }
  for (const b of readTable("DT_JourneyBeats")) {
    assert.ok(b.WordCount <= b.WordBudget, b.RowName + " over budget");
  }
});
