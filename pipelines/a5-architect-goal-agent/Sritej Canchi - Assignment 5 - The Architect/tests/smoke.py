"""Headless playthrough: prove the slice runs and the loop terminates."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "game"))
from rex.loop import Game

def run(script, label):
    g = Game()
    i = 0
    while not g.over:
        g.play_round(script[i % len(script)])
        i += 1
    reads = [e for e in g.log if e["read"]]
    bands = {e["charge_band"] for e in reads}
    gates = [e["gate"] for e in g.log if e["gate"]]
    print("%-18s rounds=%2d outcome=%-4s reads=%2d bands=%s gates=%s vetoes=%d"
          % (label, g.round, g.outcome, len(reads), sorted(bands), gates,
             g.nemesis.rejected_intercepts))
    return g

run(["right","down"], "diagonal rush")
run(["right","right","down","down"], "L pattern")
run(["left","right"], "oscillate")
run(["down","down","down","right","right","right"], "edge run")
run(["wait"], "stall")

print()
opt = ["right"]*7 + ["down"]*4
g = Game()
i = 0
while not g.over:
    g.play_round(opt[i] if i < len(opt) else "wait")
    i += 1
print("%-18s rounds=%2d outcome=%-4s stamina_left=%d" % ("OPTIMAL PATH", g.round, g.outcome, g.dog.stamina))
assert g.outcome == "win", "the fight must be winnable on a clean line"
print("winnability: OK")
