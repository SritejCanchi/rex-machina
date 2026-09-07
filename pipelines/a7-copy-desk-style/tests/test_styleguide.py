#!/usr/bin/env python3
"""Tests for the parser, the countable audit, and the loop's three outcomes."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styleguide import audit, evaluate                       # noqa: E402
import pipeline                                              # noqa: E402

passed = failed = 0


def ok(cond, label):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("  FAIL", label)


CASE = json.load(open(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "beats.json"), encoding="utf-8"))[0]

# ---- the SCORE and REASON parser ------------------------------------
s, r = evaluate.parse("SCORE: [4/10]\nREASON: [Ends on an abstract noun.]")
ok(s == 4 and "abstract noun" in r, "parses the bracketed form")
s, r = evaluate.parse("SCORE: 7/10\nREASON: Over budget by nine words.")
ok(s == 7 and "budget" in r, "parses the bare form")
s, r = evaluate.parse("SCORE: [10/10]\nREASON: [Clean.\nNothing to fix.]")
ok(s == 10 and "Nothing to fix" in r, "reason may span lines")
for bad in ["no score here at all", "SCORE: [8/10]", "REASON: [only a reason]"]:
    try:
        evaluate.parse(bad)
        ok(False, "rejects malformed reply: %s" % bad[:24])
    except ValueError:
        ok(True, "rejects malformed reply")

# ---- the countable audit, both directions ---------------------------
a = audit.audit("You keep walking. The porch light is the same as it was.", CASE)
ok(a["word_count"] == 12 and audit.clean(a), "clean line audits clean")
ok(audit.audit("Your destiny waits.", CASE)["banned_words"] == ["destiny"],
   "banned word is found")
ok(audit.audit("You made it!", CASE)["exclamations"] == 1, "exclamation found")
ok(audit.audit("**Arrival**\nYou made it", CASE)["markdown"], "markdown found")
ok(audit.audit("It is not a home, but a house you knew.", CASE)["not_x_but_y"],
   "not X but Y found")
ok(not audit.audit("The dog walks on.", CASE)["second_person"],
   "third person is flagged")
long_line = " ".join(["word"] * 41)
ok(audit.audit(long_line, CASE)["over_budget_by"] == 11, "over budget measured")


# ---- the loop -------------------------------------------------------
class Scripted:
    """Answers as the Generator, the Evaluator or the Refiner by prompt shape."""
    name = "scripted"

    def __init__(self, texts, scores):
        self.texts, self.scores = list(texts), list(scores)

    def complete(self, role, prompt, max_tokens=700):
        if "NARRATION TO REVIEW" in prompt:
            s, why = self.scores.pop(0)
            return "SCORE: [%d/10]\nREASON: [%s]" % (s, why)
        return json.dumps({"narration": self.texts.pop(0)})


h, outcome = run = pipeline.run_case(
    Scripted(["first draft"], [(10, "clean")]), CASE)
ok(outcome == "accepted" and len(h) == 1, "a first draft scoring 10 stops")

h, outcome = pipeline.run_case(
    Scripted(["bad draft", "fixed draft"], [(4, "ends on an abstract noun"),
                                            (9, "clean")]), CASE)
ok(outcome == "accepted" and len(h) == 2, "one repair reaching the threshold stops")
ok(h[-1]["text"] == "fixed draft", "the repaired text is what ships")
ok(h[0]["score"] == 4 and h[-1]["score"] == 9, "both scores are kept")

h, outcome = pipeline.run_case(
    Scripted(["a", "b", "c", "d"], [(3, "x"), (4, "x"), (5, "x"), (6, "x")]), CASE)
ok(outcome == "stopped at the repair limit", "the repair limit stops the loop")
ok(len(h) == pipeline.MAX_REPAIRS + 1, "the limit is %d repairs" % pipeline.MAX_REPAIRS)

# the loop must be driven by the score, never by the countable audit
h, outcome = pipeline.run_case(
    Scripted([" ".join(["word"] * 60)], [(10, "clean")]), CASE)
ok(outcome == "accepted", "a countably wrong line the Evaluator scores 10 is accepted")
ok(not audit.clean(h[-1]["audit"]), "and the audit still records it as wrong")

# ---- the plateau detector, added after live run 2 -------------------
h, outcome = pipeline.run_case(
    Scripted(["a", "b", "c"], [(7, "x"), (7, "x"), (7, "x")]), CASE)
ok(outcome.startswith("evaluator plateaued at 7"), "a flat score stops the loop")
ok(len(h) == 3, "the plateau stops before the repair limit")
h, outcome = pipeline.run_case(
    Scripted(["a", "b", "c", "d"], [(5, "x"), (6, "x"), (7, "x"), (8, "x")]), CASE)
ok(outcome == "stopped at the repair limit", "a rising score is not a plateau")

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
