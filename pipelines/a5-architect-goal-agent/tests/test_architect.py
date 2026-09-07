"""Tests for the agent and the slice. No third-party runner.

Every rule is tested in both directions where that is meaningful: it fires when
it should, and it does not fire on the near miss. The regression tests at the
bottom are the two bugs found while building this, kept so they cannot return.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "game"))

from architect import gaps, gdd, memory, score      # noqa: E402
from architect.scan import Codebase                 # noqa: E402
from rex.loop import Game, MAX_ROUNDS               # noqa: E402
from rex.reads import ReadBank                      # noqa: E402

PASS = []
FAIL = []


def check(label, cond):
    (PASS if cond else FAIL).append(label)


GDD_PATH = os.path.join(ROOT, "docs", "gdd_rex_machina.md")
CODE = Codebase(os.path.join(ROOT, "game"))
REQS = gdd.extract(GDD_PATH)
KEYS = {r.key for r in REQS}

# ---- GDD extraction ------------------------------------------------
check("gdd finds the charge contract field", "self_charge_pct" in KEYS)
check("gdd finds the aggression contract field", "aggression" in KEYS)
check("gdd finds prose system names", "the_machine_tires" in KEYS)
check("gdd records section numbers", all(r.section.isdigit() for r in REQS))
check("gdd de-duplicates", len(KEYS) == len(REQS))
check("gdd does not invent keys", "inventory_system" not in KEYS)

# ---- codebase perception -------------------------------------------
check("scanner reads every module", CODE.summary()["modules"] >= 6)
check("scanner finds real definitions", bool(CODE.find("predict")))
check("scanner separates comments from code",
      any("charge" in t.lower() for _, _, t in CODE.comments))
check("scanner finds no stub for a real function", not CODE.find_stub("predict"))

# ---- gap classification, both directions ---------------------------
def feat(key, **kw):
    f = {"key": key, "detect": kw.pop("detect", [key]), "requires": [],
         "blocks": [], "priority": "medium"}
    f.update(kw)
    return f


check("implemented is detected",
      gaps.classify(feat("predicted_tile", detect=["predict"]), CODE).status
      == "implemented")
check("absent is detected",
      gaps.classify(feat("wormhole", detect=["wormhole"]), CODE).status == "absent")
check("exact name match counts as implemented",
      gaps.classify(feat("periodicity"), CODE).status == "implemented")
check("attribute counts only on exact match",
      gaps.classify(feat("recthing", detect=["rected"]), CODE).status != "implemented")

# ---- scoring --------------------------------------------------------
a = gaps.Gap(feat("root", blocks=["x", "y"], priority="critical"), "absent", "")
b = gaps.Gap(feat("x", requires=["root"], priority="critical"), "absent", "")
c = gaps.Gap(feat("y", requires=["root"], priority="critical"), "absent", "")
ranked = score.score_all([a, b, c])
check("unblocked root outranks its dependents", ranked[0].key == "root")
check("unmet prerequisites score zero dependency",
      ranked[-1].breakdown["dependency"] == 0.0)
check("weights sum to one", abs(sum(score.WEIGHTS.values()) - 1.0) < 1e-9)
check("stubbed outranks absent on state",
      score.STATE_SCORE["stubbed"] > score.STATE_SCORE["absent"])
check("implemented scores zero state", score.STATE_SCORE["implemented"] == 0.0)

# ---- memory ---------------------------------------------------------
check("memory reads built keys", isinstance(memory.previously_built(), set))
check("memory reads failed keys", isinstance(memory.previously_failed(), set))

# ---- the slice itself ------------------------------------------------
def play(script):
    g = Game()
    i = 0
    while not g.over:
        g.play_round(script[i % len(script)])
        i += 1
    return g


win = Game()
opt = ["right"] * 7 + ["down"] * 4
for i, m in enumerate(opt):
    win.play_round(m)
check("a clean line wins", win.outcome == "win")
check("the fight is losable", play(["wait"]).outcome == "loss")
check("the round cap holds", play(["up"]).round <= MAX_ROUNDS)
check("approach is positional, not ratcheted",
      play(["right", "left"]).log[-1]["approach"] < 0.6)

veto = play(["left", "right"])
check("the engine veto fires", veto.nemesis.rejected_intercepts > 0)

bank = ReadBank()
check("read bank carries all three registers", set(bank.bands) ==
      {"clinical", "confident", "strained"})
check("category suppression blocks a repeat",
      bank.select("gait_read", "clinical") is not None
      and bank.select("gait_read", "clinical") is None)

# ---- the generated feature -------------------------------------------
g = Game()
start = g.nemesis.self_charge_pct
for m in opt:
    g.play_round(m)
check("charge is exposed under the GDD contract name", isinstance(start, int))
check("charge falls during pursuit", g.nemesis.self_charge_pct < start)
check("the register shifts inside one fight",
      g.nemesis.charge_band() != "clinical")
check("charge never goes negative", g.nemesis.charge >= 0)

# GDD 3 says the machine tires and is forced to pause. That only holds if a
# stationary round is a net gain, so test the accounting directly rather than
# inferring it from a whole playthrough, where the robot may sit still anyway.
probe = Game()
probe.nemesis.charge = 50.0
probe.nemesis._spend(moved=True)
after_move = probe.nemesis.charge
probe.nemesis.charge = 50.0
probe.nemesis._spend(moved=False)
after_hold = probe.nemesis.charge
check("pursuit costs charge", after_move < 50.0)
check("holding still recovers charge", after_hold > 50.0)
check("charge is capped at full",
      (setattr(probe.nemesis, "charge", 100.0),
       probe.nemesis._spend(False), probe.nemesis.charge)[2] <= 100.0)

# ---- report -----------------------------------------------------------
for f in FAIL:
    print("FAIL  %s" % f)
print("%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
