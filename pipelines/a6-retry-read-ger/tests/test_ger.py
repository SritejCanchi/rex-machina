#!/usr/bin/env python3
"""Every rule tested in both directions, plus the four loop outcomes.

A rule that only ever fires is as useless as one that never does, so each rule
gets a line it must reject and a line it must pass.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ger import breaker, rules                              # noqa: E402
import pipeline                                             # noqa: E402

passed = failed = 0


def ok(cond, label):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("  FAIL", label)


CASE = {"case_id": "t", "prior_attempt": "fence_gap", "phase": 2,
        "rounds_survived": 9, "adjacent_rounds": 3, "self_charge_pct": 52,
        "charge_band": "confident", "periodicity": 0.72,
        "dir_freq_20": {"left": 0.45, "right": 0.15, "up": 0.25, "down": 0.15},
        "dog_observable": {"gait": "limping", "collar": True}}


def fired(line):
    return {r for r, _ in rules.check(line, CASE)}


# ---- R1, tense ------------------------------------------------------
ok("R1_TENSE" in fired("I'll seal the fence gap this time."), "R1 rejects intent")
ok("R1_TENSE" in fired("You will break left at the fence again."), "R1 rejects will")
ok("R1_TENSE" not in fired("Fence gap taken nine times in twenty."), "R1 passes past tense")

# ---- R2, prior reference --------------------------------------------
ok("R2_PRIOR_REF" in fired("Left dominated nine of twenty moves."), "R2 rejects no gate")
ok("R2_PRIOR_REF" not in fired("Fence habit cost you nine rounds."), "R2 passes named gate")

# ---- R3, budget -----------------------------------------------------
ok("R3_BUDGET" in fired("The fence gap is where you stopped and it was the "
                        "left bias that did it again and again."), "R3 rejects long")
ok("R3_BUDGET" not in fired("Fence gap. Left nine of twenty."), "R3 passes bark")

# ---- R4, invented numbers -------------------------------------------
ok("R4_INVENTED_NUMBER" in fired("Fence gap held you forty rounds."), "R4 rejects invented")
ok("R4_INVENTED_NUMBER" in fired("Fence gap, 37 left turns recorded."), "R4 rejects digits")
ok("R4_INVENTED_NUMBER" not in fired("Fence gap. Nine of twenty went left."), "R4 passes real")
# The first live run slipped "seventy percent" past R4 because the word was
# missing from the spelled-number list. Kept as a regression.
ok("R4_INVENTED_NUMBER" in fired("Fence bias seventy percent recorded."), "R4 rejects spelled seventy")
ok("R4_INVENTED_NUMBER" in fired("Fence bias ninety percent recorded."), "R4 rejects spelled ninety")

# ---- R5, journey leak -----------------------------------------------
ok("R5_JOURNEY_LEAK" in fired("Alley habits fail at the fence."), "R5 rejects journey")
ok("R5_JOURNEY_LEAK" in fired("Nine days of this ends at the fence."), "R5 rejects days")
ok("R5_JOURNEY_LEAK" not in fired("Fence gap. Three rounds spent beside me."), "R5 passes arena")

# ---- the authored fallbacks must obey the rules they enforce --------
for gate, line in breaker.FALLBACK.items():
    c = dict(CASE, prior_attempt=gate)
    ok(rules.check(line, c) == [], "fallback for %s is clean" % gate)


# ---- the loop, four outcomes ----------------------------------------
class Scripted:
    """Stands in for the model so the loop can be tested without a call."""
    name = "scripted"

    def __init__(self, replies):
        self.replies = list(replies)

    def complete(self, role, prompt, max_tokens=300):
        if not self.replies:
            raise AssertionError("loop asked for more replies than scripted")
        r = self.replies.pop(0)
        if isinstance(r, BaseException):
            raise r
        return json.dumps({"line": r})


trace = []
line, br, prov = pipeline.run_case(
    Scripted(["Fence gap. Nine of twenty went left."]), CASE, trace)
ok(prov == "model" and len(br.attempts) == 1, "clean first draft is accepted")

trace = []
line, br, prov = pipeline.run_case(
    Scripted(["I'll seal the fence this time.",
              "Fence gap. Nine of twenty went left."]), CASE, trace)
ok(prov == "model_refined" and len(br.attempts) == 2, "one repair is accepted")

trace = []
line, br, prov = pipeline.run_case(
    Scripted(["I'll seal the fence this time.",
              "I will take the fence next time.",
              "Expect the fence sealed."]), CASE, trace)
ok(prov == "authored_fallback", "budget exhaustion escalates")
ok(line == breaker.FALLBACK["fence_gap"], "escalation ships the authored line")

trace = []
line, br, prov = pipeline.run_case(
    Scripted(["I'll seal the fence this time.",
              "I'll seal the fence this time."]), CASE, trace)
ok(br.reason == "refiner returned the same line twice", "no-progress trips early")
ok(len(br.attempts) == 2, "no-progress stops before the budget")

trace = []
line, br, prov = pipeline.run_case(
    Scripted([SystemExit("Live call failed, HTTP 401.")]), CASE, trace)
ok(prov == "authored_fallback", "provider failure escalates")
ok("provider error" in br.reason, "provider failure is named as such")

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
