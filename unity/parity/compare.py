"""Diff the browser game's trace against the Unity C# port's trace, turn by turn.

    python unity/parity/compare.py

Both traces use game.js coordinates (the C# side mirrors y back before writing).
A turn matches when the dog, Rex, the predicted tile, charge, stamina and the
spoken line are all equal after the same input.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
js = json.load(open(os.path.join(HERE, "js_trace.json")))
cs = json.load(open(os.path.join(HERE, "cs_trace.json")))
FIELDS = ["dog", "rex", "predicted", "charge", "stamina", "line"]

total = same = 0
first_div = {}
for name, jt in js.items():
    ct = cs[name]
    for i, j in enumerate(jt):
        c = ct[i]
        total += 1
        diff = [f for f in FIELDS if j[f] != c[f]]
        if not diff:
            same += 1
        elif name not in first_div:
            first_div[name] = (i + 1, j["move"], j["counted"], diff,
                               {f: j[f] for f in diff}, {f: c[f] for f in diff})
    print("%-22s %2d turns  %2d match  refused by the game: %d"
          % (name, len(jt), sum(1 for i, j in enumerate(jt)
                                if all(j[f] == ct[i][f] for f in FIELDS)),
             sum(1 for j in jt if not j["counted"])))

print("\n%d of %d turns match" % (same, total))
for name, (turn, move, counted, diff, jv, cv) in first_div.items():
    print("\n%s: first divergence at turn %d, input '%s' (%s)"
          % (name, turn, move, "counted" if counted else "REFUSED by game.js"))
    print("  game.js :", jv)
    print("  C# port :", cv)
